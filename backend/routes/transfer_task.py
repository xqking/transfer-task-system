from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import and_
import random
from extensions import db

ALLOC_MIN = 2000
ALLOC_MAX = 6000
DAILY_PERSON_MIN = 6
DAILY_PERSON_MAX = 10
MAX_CONSECUTIVE_DAYS = 2
WEEKLY_MAX_TASKS = 5

transfer_task_bp = Blueprint('transfer_task', __name__)

def _parse_date(d):
    if isinstance(d, str):
        return datetime.strptime(d, '%Y-%m-%d').date()
    return d

def get_person_task_dates(person_id, TaskDetail, pending_allocs):
    dates = set()
    for d in TaskDetail.query.filter(
        and_(TaskDetail.person_id == person_id, TaskDetail.status != 'cancelled')
    ).all():
        dates.add(d.task_date)
    for a in pending_allocs:
        if a['person_id'] == person_id:
            dates.add(_parse_date(a['task_date']))
    return sorted(dates)

def get_consecutive_count(person_id, task_date, TaskDetail, pending_allocs, card_id=None):
    if card_id:
        dates = set()
        for d in TaskDetail.query.filter(
            and_(TaskDetail.person_id == person_id, TaskDetail.card_id == card_id, TaskDetail.status != 'cancelled')
        ).all():
            dates.add(d.task_date)
        for a in pending_allocs:
            if a['person_id'] == person_id and a.get('card_id') == card_id:
                dates.add(_parse_date(a['task_date']))
    else:
        dates = get_person_task_dates(person_id, TaskDetail, pending_allocs)
    
    if not dates:
        return 0
    if task_date in dates:
        dates.remove(task_date)
    count = 0
    d = task_date - timedelta(days=1)
    while d in dates:
        count += 1
        d -= timedelta(days=1)
    return count

def get_weekly_task_count(person_id, task_date, TaskDetail, pending_allocs, card_id=None):
    week_start = task_date - timedelta(days=6)
    if card_id:
        dates = set()
        for d in TaskDetail.query.filter(
            and_(TaskDetail.person_id == person_id, TaskDetail.card_id == card_id, TaskDetail.status != 'cancelled')
        ).all():
            dates.add(d.task_date)
        for a in pending_allocs:
            if a['person_id'] == person_id and a.get('card_id') == card_id:
                dates.add(_parse_date(a['task_date']))
        return sum(1 for d in dates if week_start <= d <= task_date)
    else:
        dates = get_person_task_dates(person_id, TaskDetail, pending_allocs)
        return sum(1 for d in dates if week_start <= d <= task_date)

def can_assign_person(person_id, task_date, day_person_set, TaskDetail, pending_allocs, card_id=None):
    if person_id in day_person_set:
        return False
    cons = get_consecutive_count(person_id, task_date, TaskDetail, pending_allocs, card_id)
    if cons >= MAX_CONSECUTIVE_DAYS:
        return False
    weekly = get_weekly_task_count(person_id, task_date, TaskDetail, pending_allocs, card_id)
    if weekly >= WEEKLY_MAX_TASKS:
        return False
    return True

def get_alloc_limits(total_amount):
    if total_amount <= 30000:
        return 2000, 6000
    elif total_amount <= 60000:
        return 4000, 12000
    else:
        return 4000, 12000

def calc_amount(remaining, person, card_room, total_amount):
    alloc_min, alloc_max = get_alloc_limits(total_amount)
    
    caps = [remaining]
    if card_room is not None:
        caps.append(int(card_room))
    
    mx = min(caps + [alloc_max])
    mn = max(int(person.single_min), alloc_min)
    
    if mx < mn:
        return 0
    
    if remaining <= mx and remaining >= mn:
        return remaining
    
    valid = []
    for a in range(mn, mx + 1):
        if (remaining - a) == 0 or (remaining - a) >= alloc_min:
            valid.append(a)
    
    if valid:
        return max(valid)
    
    return random.randint(mn, mx)

def simulate_allocate(total_amount, cards, persons, TaskDetail, task_date=None):
    allocations = []
    remaining = int(total_amount)
    task_date = task_date or datetime.now().date()

    day_cap = min(DAILY_PERSON_MAX, len(persons))
    day_persons = set()
    shuffled = list(persons)
    random.shuffle(shuffled)
    
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

        for person in shuffled:
            if remaining <= 0:
                break
            if len(day_persons) >= day_cap:
                card_debug['skipped_reasons']['day_cap_reached'] = f'已达到每日上限{day_cap}人'
                break
            alloc_min, _ = get_alloc_limits(total_amount)
            if card_room < alloc_min:
                card_debug['skipped_reasons']['card_full'] = f'卡额度不足(剩余{card_room}<{alloc_min})'
                break
            
            reason = None
            cons = get_consecutive_count(person.id, task_date, TaskDetail, allocations, card.id)
            if cons >= MAX_CONSECUTIVE_DAYS:
                reason = f'该卡连续{cons}天已达上限'
            
            weekly = get_weekly_task_count(person.id, task_date, TaskDetail, allocations, card.id)
            if weekly >= WEEKLY_MAX_TASKS:
                reason = f'该卡本周已{weekly}次达上限'
            
            if reason:
                card_debug['skipped_reasons'][person.code] = reason
                continue

            amount = calc_amount(remaining, person, card_room, total_amount)
            alloc_min, _ = get_alloc_limits(total_amount)
            if amount < alloc_min:
                card_debug['skipped_reasons'][person.code] = f'金额计算失败(amount={amount})'
                continue

            allocations.append({
                'person_id': person.id,
                'person_code': person.code,
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
        for alloc in allocations:
            if remaining <= 0:
                break
            
            current_amount = alloc['amount']
            max_add = ALLOC_MAX - current_amount
            if max_add <= 0:
                continue
            
            room = min(max_add, 60000)
            if room <= 0:
                continue
            
            add = min(remaining, room)
            new_amount = current_amount + add
            
            alloc['amount'] = new_amount
            remaining -= add

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
    
    if len(persons) < DAILY_PERSON_MIN:
        return jsonify({'code': 400, 'message': f'人员不足，每天需要{DAILY_PERSON_MIN}-{DAILY_PERSON_MAX}人，当前仅{len(persons)}人'})
    
    start_date = datetime.strptime(data.get('task_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    total_amount = int(data['total_amount'])
    
    max_capacity = DAILY_PERSON_MAX * ALLOC_MAX * len(cards)
    if total_amount > max_capacity:
        return jsonify({
            'code': 400,
            'message': f'任务金额 ¥{total_amount} 超出最大容量 ¥{max_capacity}（{DAILY_PERSON_MAX}人 x ¥{ALLOC_MAX}/人 x {len(cards)}张卡）'
        })
    
    allocations, remaining, debug_info = simulate_allocate(total_amount, cards, persons, TaskDetail, start_date)
    
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
    tasks = TransferTask.query.order_by(TransferTask.created_at.desc()).all()
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
        row = {'person_code': person.code, 'dates': {}}
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
