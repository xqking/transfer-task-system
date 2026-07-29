from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import and_
import random
from extensions import db
from models import BankCard, TaskDetail, Person, TransferTask, Customer, Bank

ALLOC_MIN = 2000
ALLOC_MAX = 20000
MAX_CONSECUTIVE_DAYS = 2
MAX_CUSTOMERS_PER_PERSON = 2

transfer_task_bp = Blueprint('transfer_task', __name__)

def _parse_date(d):
    if isinstance(d, str):
        return datetime.strptime(d, '%Y-%m-%d').date()
    return d

def can_assign_person_to_customer(person_id, customer_id, task_date, TaskDetail):
    from datetime import timedelta
    
    # 检查今日客户数量限制
    customer_count = TaskDetail.query.filter(
        and_(
            TaskDetail.person_id == person_id,
            TaskDetail.task_date == task_date,
            TaskDetail.status.in_(['pending', 'completed'])
        )
    ).join(TaskDetail.card).distinct(BankCard.customer_id).count()
    
    if customer_count >= MAX_CUSTOMERS_PER_PERSON:
        return False, f'今日已分配{customer_count}个客户任务，达到上限{MAX_CUSTOMERS_PER_PERSON}个'
    
    # 检查连续分配限制
    cards = BankCard.query.filter(BankCard.customer_id == customer_id, BankCard.status == 1).all()
    for card in cards:
        if has_consecutive_allocation(person_id, card.id, task_date, TaskDetail):
            return False, f'已连续{MAX_CONSECUTIVE_DAYS}天分配客户的银行卡，今日跳过'
    
    return True, ''

def has_consecutive_allocation(person_id, card_id, task_date, TaskDetail, max_consecutive=MAX_CONSECUTIVE_DAYS):
    from datetime import timedelta
    
    consecutive_count = 0
    check_date = task_date - timedelta(days=1)
    
    for _ in range(max_consecutive):
        existing = TaskDetail.query.filter(
            and_(
                TaskDetail.person_id == person_id,
                TaskDetail.card_id == card_id,
                TaskDetail.task_date == check_date,
                TaskDetail.status.in_(['pending', 'completed'])
            )
        ).first()
        
        if existing:
            consecutive_count += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    return consecutive_count >= max_consecutive

def get_alloc_limits(total_amount, alloc_min=None, alloc_max=None):
    return alloc_min or ALLOC_MIN, alloc_max or ALLOC_MAX

def is_valid_amount(amount):
    units = amount % 10
    tens = (amount // 10) % 10
    return units != 0 and tens != 0

def calc_amount(remaining, person, card_room, total_amount, alloc_min=None, alloc_max=None):
    alloc_min, alloc_max = get_alloc_limits(total_amount, alloc_min, alloc_max)
    
    caps = [remaining]
    if card_room is not None:
        caps.append(int(card_room))
    
    mx = min(caps + [alloc_max])
    mn = alloc_min
    
    if mx < mn:
        return 0
    
    if remaining <= mx and remaining >= mn:
        if is_valid_amount(remaining):
            return remaining
        else:
            candidates = []
            for delta in range(1, 100):
                for sign in [-1, 1]:
                    adjusted = remaining + sign * delta
                    if adjusted >= mn and adjusted <= mx and is_valid_amount(adjusted):
                        candidates.append(adjusted)
            if candidates:
                return candidates[random.randint(0, len(candidates) - 1)]
    
    valid = []
    for a in range(mn, mx + 1):
        if (remaining - a) == 0 or (remaining - a) >= alloc_min:
            if is_valid_amount(a):
                valid.append(a)
    
    if valid:
        return max(valid)
    
    candidates = []
    for a in range(mn, mx + 1):
        if is_valid_amount(a):
            candidates.append(a)
    
    if candidates:
        return candidates[random.randint(0, len(candidates) - 1)]
    
    return random.randint(mn, mx)

def simulate_allocate_by_customer(total_amount, customer_id, persons, TaskDetail, task_date=None, alloc_min=None, alloc_max=None, force_allocate=False):
    """按客户分配：一个人负责一个客户的所有银行卡任务"""
    allocations = []
    task_date = task_date or datetime.now().date()
    alloc_min_val, alloc_max_val = get_alloc_limits(total_amount, alloc_min, alloc_max)
    
    # 获取客户的所有银行卡
    cards = BankCard.query.filter(BankCard.customer_id == customer_id, BankCard.status == 1).all()
    if not cards:
        return [], total_amount, {'error': '该客户没有可用的银行卡'}
    
    if len(cards) == 0:
        return [], total_amount, {'error': '该客户没有可用的银行卡'}
    
    debug_info = {
        'task_date': task_date.strftime('%Y-%m-%d'),
        'customer_id': customer_id,
        'customer_cards': len(cards),
        'total_amount': total_amount,
        'allocations': [],
        'skipped_reasons': []
    }
    
    # 为每个银行卡分配金额（按比例或平均分配）
    if len(cards) == 1:
        # 只有一张卡，全部金额给这张卡
        card_amounts = {cards[0].id: total_amount}
    else:
        # 两张卡，按比例分配（各一半或按额度）
        half = total_amount // 2
        remainder = total_amount - half
        card_amounts = {
            cards[0].id: half,
            cards[1].id: remainder
        }
    
    # 找到第一个可用的人员
    selected_person = None
    shuffled = list(persons)
    random.shuffle(shuffled)
    
    for person in shuffled:
        is_available, reason = can_assign_person_to_customer(person.id, customer_id, task_date, TaskDetail)
        if is_available or force_allocate:
            selected_person = person
            if not is_available:
                debug_info['skipped_reasons'].append(f'强制分配给 {person.name}: {reason}')
            break
        else:
            debug_info['skipped_reasons'].append(f'{person.name}: {reason}')
    
    if not selected_person:
        return [], total_amount, debug_info
    
    # 为选中的人员创建所有银行卡的分配记录
    for card in cards:
        amount = card_amounts.get(card.id, 0)
        if amount <= 0:
            continue
        
        # 确保金额有效
        valid_amount = amount
        if not is_valid_amount(valid_amount) and valid_amount >= alloc_min_val:
            # 调整为有效金额
            for delta in range(1, 100):
                for sign in [-1, 1]:
                    adjusted = valid_amount + sign * delta
                    if adjusted >= alloc_min_val and is_valid_amount(adjusted):
                        valid_amount = adjusted
                        break
                if is_valid_amount(valid_amount):
                    break
        
        if valid_amount >= alloc_min_val:
            allocation = {
                'person_id': selected_person.id,
                'person_name': selected_person.name,
                'card_id': card.id,
                'card_no': card.card_no[-4:],
                'bank_id': card.bank_id,
                'bank_name': Bank.query.get(card.bank_id).name if card.bank_id else '',
                'amount': valid_amount,
                'task_date': task_date.strftime('%Y-%m-%d')
            }
            allocations.append(allocation)
            bank_name = Bank.query.get(card.bank_id).name if card.bank_id else ''
            debug_info['allocations'].append({
                'person_name': selected_person.name,
                'card_no': card.card_no[-4:],
                'bank_name': bank_name,
                'amount': valid_amount
            })
    
    total_allocated = sum(a['amount'] for a in allocations)
    remaining = total_amount - total_allocated
    debug_info['remaining'] = remaining
    debug_info['allocated_count'] = len(allocations)
    debug_info['selected_person'] = selected_person.name
    
    return allocations, remaining, debug_info

@transfer_task_bp.route('/create', methods=['POST'])
def create_task():
    from models import TransferTask, TaskDetail, Person, Customer, BankCard, Bank
    data = request.json
    
    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({'code': 400, 'message': '客户不存在'})
    
    # 获取客户的所有银行卡
    cards = BankCard.query.filter(
        and_(
            BankCard.customer_id == data['customer_id'],
            BankCard.status == 1
        )).all()
    
    if not cards:
        return jsonify({'code': 400, 'message': '该客户没有可用的银行卡，请先添加银行卡'})
    
    excluded_person_ids = data.get('excluded_person_ids', [])
    persons = Person.query.filter(
        and_(
            Person.status == 1,
            Person.id.not_in(excluded_person_ids) if excluded_person_ids else True
        )).all()
    
    if not persons:
        return jsonify({'code': 400, 'message': '没有可用的人员，请先添加人员'})

    start_date = datetime.strptime(data.get('task_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    total_amount = int(data['total_amount'])
    
    alloc_min = data.get('alloc_min')
    alloc_max = data.get('alloc_max')
    force_allocate = data.get('force_allocate', False)
    if alloc_min:
        alloc_min = int(alloc_min)
    if alloc_max:
        alloc_max = int(alloc_max)
    
    # 使用新的按客户分配逻辑
    allocations, remaining, debug_info = simulate_allocate_by_customer(
        total_amount, data['customer_id'], persons, TaskDetail, 
        start_date, alloc_min, alloc_max, force_allocate
    )
    
    if not allocations:
        error_msg = debug_info.get('error', '没有可用的人员')
        if 'skipped_reasons' in debug_info and debug_info['skipped_reasons']:
            error_msg += '\n\n不满足条件的人员：\n' + '\n'.join(debug_info['skipped_reasons'])
        return jsonify({
            'code': 400,
            'message': error_msg,
            'data': {
                'remaining_amount': int(remaining),
                'debug_info': debug_info
            }
        })
    
    # 获取涉及的银行（可能多个）
    bank_ids = list(set(c.bank_id for c in cards))
    primary_bank_id = bank_ids[0] if bank_ids else None
    
    task = TransferTask(
        task_name=data.get('task_name', f'{customer.name}_转账任务'),
        customer_id=data['customer_id'],
        bank_id=primary_bank_id,  # 主要银行ID（用于兼容）
        total_amount=total_amount,
        task_type='daily',
        start_date=start_date,
        end_date=start_date,
        status='pending',
        remark=data.get('remark', '')
    )
    db.session.add(task)
    db.session.flush()
    
    for alloc in allocations:
        detail = TaskDetail(
            task_id=task.id,
            person_id=alloc['person_id'],
            card_id=alloc['card_id'],
            amount=alloc['amount'],
            task_date=datetime.strptime(alloc['task_date'], '%Y-%m-%d').date(),
            status='pending'
        )
        db.session.add(detail)
    
    task.transferred_amount = total_amount
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': f'任务创建成功！共分配给 {debug_info["selected_person"]} 负责 {customer.name} 的所有银行卡任务',
        'data': {
            'task_id': task.id,
            'allocated_count': len(allocations),
            'remaining_amount': 0,
            'selected_person': debug_info['selected_person'],
            'customer_name': customer.name,
            'card_count': len(cards),
            'preview': debug_info['allocations']
        }
    })

@transfer_task_bp.route('/list', methods=['GET'])
def get_task_list():
    from models import TransferTask
    from sqlalchemy import and_, or_
    
    keyword = request.args.get('keyword', '').strip()
    customer_id = request.args.get('customer_id', '').strip()
    bank_id = request.args.get('bank_id', '').strip()
    status = request.args.get('status', '').strip()
    task_date = request.args.get('task_date', '').strip()
    
    query = TransferTask.query
    
    if keyword:
        query = query.filter(TransferTask.task_name.like(f'%{keyword}%'))
    
    if customer_id:
        query = query.filter(TransferTask.customer_id == int(customer_id))
    
    if bank_id:
        query = query.filter(TransferTask.bank_id == int(bank_id))
    
    if status:
        query = query.filter(TransferTask.status == status)
    
    if task_date:
        query = query.filter(TransferTask.task_date == task_date)
    
    tasks = query.order_by(TransferTask.created_at.desc()).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': t.id,
            'task_name': t.task_name,
            'customer_name': t.customer.name if t.customer else '',
            'bank_name': t.bank.name if t.bank else '',
            'total_amount': t.total_amount,
            'transferred_amount': t.transferred_amount,
            'status': t.status,
            'remark': t.remark if hasattr(t, 'remark') else '',
            'detail_count': len(t.details)
        } for t in tasks]
    })

@transfer_task_bp.route('/gantt/<int:task_id>', methods=['GET'])
def get_gantt_data(task_id):
    from models import TransferTask, TaskDetail, Person
    task = TransferTask.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在'})
    
    persons = Person.query.filter_by(status=1).order_by(Person.code).all()
    details = TaskDetail.query.filter_by(task_id=task_id).all()
    
    dates = set()
    for d in details:
        dates.add(d.task_date)
    dates = sorted(list(dates))
    
    gantt_data = []
    for person in persons:
        row = {'person_id': person.id, 'person_name': person.name, 'dates': {}}
        for date in dates:
            ds = date.strftime('%Y-%m-%d')
            pds = [d for d in details if d.person_id == person.id and d.task_date == date]
            row['dates'][ds] = [{
                'id': d.id,
                'amount': d.amount,
                'customer_name': task.customer.name if task.customer else '',
                'bank_name': task.bank.name if task.bank else '',
                'status': d.status,
                'card_no': d.card.card_no[-4:] if d.card else ''
            } for d in pds] if pds else []
        gantt_data.append(row)
    
    return jsonify({
        'code': 200,
        'data': {
            'task': {'id': task.id, 'task_name': task.task_name, 'total_amount': task.total_amount, 'status': task.status},
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'persons': gantt_data
        }
    })

@transfer_task_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_task(id):
    from models import TransferTask, TaskDetail
    task = TransferTask.query.get(id)
    if task:
        TaskDetail.query.filter_by(task_id=id).delete()
        db.session.delete(task)
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    return jsonify({'code': 400, 'message': '任务不存在'})

@transfer_task_bp.route('/check-person-status', methods=['POST'])
def check_person_status():
    from models import Person, BankCard, TaskDetail
    data = request.json
    
    customer_id = data.get('customer_id')
    task_date = datetime.strptime(data.get('task_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    
    if not customer_id:
        return jsonify({'code': 400, 'message': '请选择客户'})
    
    # 获取客户的所有银行卡
    cards = BankCard.query.filter(
        and_(
            BankCard.customer_id == customer_id,
            BankCard.status == 1
        )
    ).all()
    
    if not cards:
        return jsonify({'code': 400, 'message': '该客户没有可用的银行卡'})
    
    card_ids = [c.id for c in cards]
    
    persons = Person.query.filter_by(status=1).all()
    
    result = []
    for person in persons:
        status = 'available'
        reason = ''
        consecutive_days = 0
        today_customer_count = 0
        
        # 检查客户数量限制
        customer_count = TaskDetail.query.filter(
            and_(
                TaskDetail.person_id == person.id,
                TaskDetail.task_date == task_date,
                TaskDetail.status.in_(['pending', 'completed'])
            )
        ).join(TaskDetail.card).distinct(BankCard.customer_id).count()
        today_customer_count = customer_count
        
        if customer_count >= MAX_CUSTOMERS_PER_PERSON:
            status = 'blocked'
            reason = f'今日已分配{customer_count}个客户任务，达到上限{MAX_CUSTOMERS_PER_PERSON}个'
            result.append({
                'id': person.id,
                'name': person.name,
                'status': status,
                'reason': reason,
                'consecutive_days': consecutive_days,
                'today_customer_count': today_customer_count
            })
            continue
        
        # 检查连续分配限制（检查该客户的所有银行卡）
        for card_id in card_ids:
            count = has_consecutive_allocation(person.id, card_id, task_date, TaskDetail, MAX_CONSECUTIVE_DAYS)
            if count:
                consecutive_days = MAX_CONSECUTIVE_DAYS
                status = 'blocked'
                reason = f'已连续{MAX_CONSECUTIVE_DAYS}天分配该客户的银行卡，今日跳过'
                break
        
        result.append({
            'id': person.id,
            'name': person.name,
            'status': status,
            'reason': reason,
            'consecutive_days': consecutive_days,
            'today_customer_count': today_customer_count
        })
    
    return jsonify({
        'code': 200,
        'data': result,
        'card_count': len(cards)
    })

@transfer_task_bp.route('/person-status-by-card', methods=['GET'])
def get_person_status_by_card():
    from models import Person, BankCard, Customer, Bank
    
    task_date = datetime.strptime(request.args.get('task_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    
    customers = Customer.query.filter_by(status=1).all()
    persons = Person.query.filter_by(status=1).all()
    
    result = []
    
    for customer in customers:
        customer_data = {
            'customer_id': customer.id,
            'customer_name': customer.name,
            'customer_color': customer.color,
            'banks': []
        }
        
        cards = BankCard.query.filter_by(customer_id=customer.id, status=1).all()
        
        bank_groups = {}
        for card in cards:
            bank = Bank.query.get(card.bank_id)
            if bank.id not in bank_groups:
                bank_groups[bank.id] = {
                    'bank_id': bank.id,
                    'bank_name': bank.name,
                    'cards': []
                }
            bank_groups[bank.id]['cards'].append(card)
        
        for bank_id, bank_data in bank_groups.items():
            bank_result = {
                'bank_id': bank_data['bank_id'],
                'bank_name': bank_data['bank_name'],
                'available_persons': [],
                'blocked_persons': []
            }
            
            card_ids = [c.id for c in bank_data['cards']]
            
            for person in persons:
                status = 'available'
                reason = ''
                
                customer_count = TaskDetail.query.filter(
                    and_(
                        TaskDetail.person_id == person.id,
                        TaskDetail.task_date == task_date,
                        TaskDetail.status.in_(['pending', 'completed'])
                    )
                ).join(TaskDetail.card).distinct(BankCard.customer_id).count()
                
                if customer_count >= MAX_CUSTOMERS_PER_PERSON:
                    status = 'blocked'
                    reason = f'今日已分配{customer_count}个客户任务'
                else:
                    for card_id in card_ids:
                        count = has_consecutive_allocation(person.id, card_id, task_date, TaskDetail, MAX_CONSECUTIVE_DAYS)
                        if count:
                            status = 'blocked'
                            reason = f'已连续{MAX_CONSECUTIVE_DAYS}天分配此卡'
                            break
                
                person_info = {
                    'id': person.id,
                    'name': person.name,
                    'status': status,
                    'reason': reason
                }
                
                if status == 'available':
                    bank_result['available_persons'].append(person_info)
                else:
                    bank_result['blocked_persons'].append(person_info)
            
            customer_data['banks'].append(bank_result)
        
        result.append(customer_data)
    
    return jsonify({
        'code': 200,
        'data': result
    })

@transfer_task_bp.route('/batch-delete', methods=['POST'])
def batch_delete_tasks():
    from models import TransferTask, TaskDetail
    data = request.json
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({'code': 400, 'message': '请选择要删除的任务'})
    
    deleted_count = 0
    for task_id in ids:
        task = TransferTask.query.get(task_id)
        if task:
            TaskDetail.query.filter_by(task_id=task_id).delete()
            db.session.delete(task)
            deleted_count += 1
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': f'成功删除 {deleted_count} 个任务',
        'data': {
            'deleted_count': deleted_count
        }
    })


@transfer_task_bp.route('/batch-complete', methods=['POST'])
def batch_complete_tasks():
    from models import TransferTask, TaskDetail
    from datetime import datetime
    data = request.json
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({'code': 400, 'message': '请选择要完成的任务'})
    
    completed_count = 0
    for task_id in ids:
        task = TransferTask.query.get(task_id)
        if task and task.status == 'pending':
            task.status = 'completed'
            task.transferred_amount = task.total_amount
            task.updated_at = datetime.now()
            
            TaskDetail.query.filter_by(task_id=task_id).update({
                'status': 'completed',
                'execute_time': datetime.now()
            })
            completed_count += 1
    
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': f'成功将 {completed_count} 个任务标记为完成',
        'data': {'completed_count': completed_count}
    })
