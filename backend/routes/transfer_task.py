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

def can_assign_person(person_id, task_date, day_person_set, TaskDetail, pending_allocs, card_id=None):
    if person_id in day_person_set:
        return False
    return True

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

def simulate_allocate(total_amount, cards, persons, TaskDetail, task_date=None, alloc_min=None, alloc_max=None, force_allocate=False):
    allocations = []
    remaining = int(total_amount)
    task_date = task_date or datetime.now().date()
    
    alloc_min_val, alloc_max_val = get_alloc_limits(total_amount, alloc_min, alloc_max)

    day_cap = len(persons)
    day_persons = set()
    
    debug_info = {
        'task_date': task_date.strftime('%Y-%m-%d'),
        'total_cards': len(cards),
        'total_persons': len(persons),
        'day_cap': day_cap,
        'skipped_persons': [],
        'card_details': []
    }

    for card in cards:
        if remaining <= 0:
            break
        card_used_today = sum(
            a['amount'] for a in allocations
            if a['card_id'] == card.id and _parse_date(a['task_date']) == task_date
        )
        card_room = 60000 - card_used_today
        
        card_debug = {
            'card_no': card.card_no[-4:],
            'card_room': card_room,
            'assigned_count': 0,
            'skipped_reasons': {}
        }

        shuffled = list(persons)
        random.shuffle(shuffled)

        for person in shuffled:
            if remaining <= 0:
                break
            if len(day_persons) >= day_cap:
                card_debug['skipped_reasons']['day_cap_reached'] = f'已达到每日上限{day_cap}人'
                break
            if card_room < alloc_min_val:
                card_debug['skipped_reasons']['card_full'] = f'卡额度不足(剩余{card_room}<{alloc_min_val})'
                break

            used_by_person = sum(a['amount'] for a in allocations if a['person_id'] == person.id)
            if used_by_person >= alloc_max_val:
                continue

            person_remaining = alloc_max_val - used_by_person
            if person_remaining < alloc_min_val:
                continue

            if has_consecutive_allocation(person.id, card.id, task_date, TaskDetail):
                if not force_allocate:
                    card_debug['skipped_reasons'][f'person_{person.id}'] = f'人员{person.name}已连续{MAX_CONSECUTIVE_DAYS}天分配此卡，今日跳过'
                    continue

            customer_count = TaskDetail.query.filter(
                and_(
                    TaskDetail.person_id == person.id,
                    TaskDetail.task_date == task_date,
                    TaskDetail.status.in_(['pending', 'completed'])
                )
            ).join(TaskDetail.card).distinct(BankCard.customer_id).count()
            
            if customer_count >= MAX_CUSTOMERS_PER_PERSON:
                if not force_allocate:
                    card_debug['skipped_reasons'][f'person_{person.id}'] = f'人员{person.name}今日已分配{customer_count}个客户任务，达到上限{MAX_CUSTOMERS_PER_PERSON}个'
                    continue

            max_possible = min(person_remaining, remaining, card_room, alloc_max_val)
            
            if max_possible < alloc_min_val:
                continue

            if remaining <= alloc_max_val:
                target_amount = remaining
            else:
                target_amount = max_possible
            
            target_amount = min(target_amount, max_possible)
            target_amount = max(target_amount, alloc_min_val)

            candidates = []
            search_low = max(alloc_min_val, target_amount - 1000)
            for a in range(target_amount, search_low - 1, -1):
                if a < alloc_min_val:
                    break
                if is_valid_amount(a):
                    remaining_after = remaining - a
                    if remaining_after == 0 or remaining_after >= alloc_min_val:
                        candidates.append(a)
                        if len(candidates) >= 15:
                            break
            
            if not candidates:
                for a in range(min(target_amount, alloc_max_val), alloc_min_val - 1, -1):
                    if is_valid_amount(a):
                        remaining_after = remaining - a
                        if remaining_after == 0 or remaining_after >= alloc_min_val:
                            candidates.append(a)
                            if len(candidates) >= 15:
                                break
            
            if candidates:
                amount = candidates[random.randint(0, min(8, len(candidates)) - 1)]
            else:
                valid_amounts = [a for a in range(alloc_min_val, min(target_amount, alloc_max_val) + 1) if is_valid_amount(a)]
                if valid_amounts:
                    amount = valid_amounts[-1]
                else:
                    continue

            allocations.append({
                'person_id': person.id,
                'person_name': person.name,
                'card_id': card.id,
                'card_no': card.card_no[-4:],
                'amount': amount,
                'task_date': task_date.strftime('%Y-%m-%d')
            })
            day_persons.add(person.id)
            card_room -= amount
            remaining -= amount
            card_debug['assigned_count'] += 1
        
        debug_info['card_details'].append(card_debug)

    debug_info['remaining'] = remaining
    debug_info['allocated_count'] = len(allocations)

    if remaining > 0:
        alloc_with_room = [a for a in allocations if a['amount'] < alloc_max_val]
        alloc_with_room.sort(key=lambda x: x['amount'])
        while remaining > 0 and alloc_with_room:
            alloc = alloc_with_room.pop(0)
            
            max_add = alloc_max_val - alloc['amount']
            if max_add <= 0:
                continue
            
            add_amount = min(remaining, max_add)
            
            new_amount = alloc['amount'] + add_amount
            while not is_valid_amount(new_amount) and add_amount > 0:
                add_amount -= 1
                new_amount = alloc['amount'] + add_amount
            
            if is_valid_amount(new_amount) and add_amount > 0:
                alloc['amount'] = new_amount
                remaining -= add_amount

    if remaining > 0 and remaining >= alloc_min_val:
        for card in cards:
            if remaining <= 0:
                break
            card_used = sum(a['amount'] for a in allocations if a['card_id'] == card.id)
            card_room = 60000 - card_used
            if card_room < alloc_min_val:
                continue
            
            for person in persons:
                if remaining <= 0:
                    break
                used_by_person = sum(a['amount'] for a in allocations if a['person_id'] == person.id)
                person_remaining = alloc_max_val - used_by_person
                if person_remaining < alloc_min_val:
                    continue
                
                target = min(remaining, person_remaining, card_room)
                if target < alloc_min_val:
                    continue
                
                valid_amounts = [a for a in range(target, alloc_min_val - 1, -1) if is_valid_amount(a)]
                if valid_amounts:
                    amount = valid_amounts[0]
                    allocations.append({
                        'person_id': person.id,
                        'person_name': person.name,
                        'card_id': card.id,
                        'card_no': card.card_no[-4:],
                        'amount': amount,
                        'task_date': task_date.strftime('%Y-%m-%d')
                    })
                    day_persons.add(person.id)
                    remaining -= amount
                    card_room -= amount

    return allocations, remaining, debug_info

@transfer_task_bp.route('/create', methods=['POST'])
def create_task():
    from models import TransferTask, TaskDetail, Person, Customer, BankCard, Bank
    data = request.json
    
    customer = Customer.query.get(data['customer_id'])
    bank = Bank.query.get(data['bank_id'])
    
    if not customer or not bank:
        return jsonify({'code': 400, 'message': '客户或银行不存在'})
    
    cards = BankCard.query.filter(
        and_(
            BankCard.customer_id == data['customer_id'],
            BankCard.bank_id == data['bank_id'],
            BankCard.status == 1
        )).all()
    
    if not cards:
        return jsonify({'code': 400, 'message': '该客户在此银行没有可用的银行卡，请先添加银行卡'})
    
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
    
    allocations, remaining, debug_info = simulate_allocate(total_amount, cards, persons, TaskDetail, start_date, alloc_min, alloc_max, force_allocate)
    
    if remaining > 0:
        details = []
        details.append(f"日期：{debug_info['task_date']}")
        details.append(f"总人数：{debug_info['total_persons']}人，每日上限：{debug_info['day_cap']}人")
        details.append(f"银行卡数：{debug_info['total_cards']}张")
        
        for card in debug_info['card_details']:
            details.append(f"\n【卡号 ****{card['card_no']}】可用额度: ¥{card['card_room']}, 已分配: {card['assigned_count']}人")
            if card['skipped_reasons']:
                for person_code, reason in card['skipped_reasons'].items():
                    details.append(f"  - {person_code}: {reason}")
        
        detail_str = '\n'.join(details)
        return jsonify({
            'code': 400,
            'message': f'无法完全分配：剩余 ¥{int(remaining)} 未分配\n\n{detail_str}',
            'data': {
                'allocated_count': len(allocations),
                'remaining_amount': int(remaining),
                'preview': allocations[:10],
                'debug_info': debug_info
            }
        })
    
    task = TransferTask(
        task_name=data.get('task_name', f'{customer.name}_{bank.name}_转账任务'),
        customer_id=data['customer_id'],
        bank_id=data['bank_id'],
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
        'message': f'任务创建成功！共分配 {len(allocations)} 条子任务',
        'data': {
            'task_id': task.id,
            'allocated_count': len(allocations),
            'remaining_amount': 0
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
    bank_id = data.get('bank_id')
    task_date = datetime.strptime(data.get('task_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    
    if not customer_id or not bank_id:
        return jsonify({'code': 400, 'message': '请选择客户和银行'})
    
    cards = BankCard.query.filter(
        and_(
            BankCard.customer_id == customer_id,
            BankCard.bank_id == bank_id,
            BankCard.status == 1
        )
    ).all()
    
    if not cards:
        return jsonify({'code': 400, 'message': '该客户在此银行没有可用的银行卡'})
    
    card_ids = [c.id for c in cards]
    
    persons = Person.query.filter_by(status=1).all()
    
    result = []
    for person in persons:
        status = 'available'
        reason = ''
        consecutive_days = 0
        today_customer_count = 0
        
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
                'code': person.code,
                'name': person.name,
                'status': status,
                'reason': reason,
                'consecutive_days': consecutive_days,
                'today_customer_count': today_customer_count
            })
            continue
        
        for card_id in card_ids:
            count = has_consecutive_allocation(person.id, card_id, task_date, TaskDetail, MAX_CONSECUTIVE_DAYS)
            if count:
                consecutive_days = MAX_CONSECUTIVE_DAYS
                status = 'blocked'
                reason = f'已连续{MAX_CONSECUTIVE_DAYS}天分配此卡，今日跳过'
                break
        
        result.append({
            'id': person.id,
            'code': person.code,
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
