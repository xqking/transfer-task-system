from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import and_, func
import random
import os
import subprocess
from extensions import db
from models import BankCard, TaskDetail, Person, TransferTask, Customer, Bank

ALLOC_MIN = 2000
MAX_CONSECUTIVE_DAYS = 2
MAX_CUSTOMERS_PER_PERSON = 2

transfer_task_bp = Blueprint('transfer_task', __name__)

def _backup_database():
    """删除操作前自动备份数据库"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f'pre_delete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql')
        cmd = f"mysqldump -uroot -p'MySql123!' -h localhost account_transactions > {backup_file}"
        subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
        return True
    except Exception as e:
        print(f"备份失败: {e}")
        return False

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
    return alloc_min or ALLOC_MIN, alloc_max or None

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

def simulate_allocate_pack(card_amounts, persons, TaskDetail, task_date=None, alloc_min=None, alloc_max=None, force_allocate=False, specified_person_ids=None):
    """
    按客户打包分配：一个人同时接该客户所有银行卡的任务
    alloc_min: 单卡每次分配最低金额
    alloc_max: 单卡每次分配最高金额
    单人单日总额受系统ALLOC_MAX限制
    
    新算法：根据每人剩余容量动态分配，考虑已有任务
    """
    allocations = []
    task_date = task_date or datetime.now().date()
    
    valid_card_amounts = [ca for ca in card_amounts if ca.get('amount') and ca['amount'] > 0]
    if not valid_card_amounts:
        return [], 0, {'error': '没有有效的银行金额'}
    
    card_total = {ca['card_id']: int(ca['amount']) for ca in valid_card_amounts}
    card_map = {ca['card_id']: BankCard.query.get(ca['card_id']) for ca in valid_card_amounts}
    card_ids = list(card_total.keys())
    n_cards = len(card_ids)
    
    if specified_person_ids:
        persons = [p for p in persons if p.id in specified_person_ids]
    
    alloc_min_val = alloc_min or ALLOC_MIN
    alloc_max_val = alloc_max or None
    total_amount = sum(card_total.values())
    min_pack_total = n_cards * alloc_min_val
    
    # 计算每人今日是否可接新客户（只检查客户数量，不检查金额上限）
    person_info = {}
    for p in persons:
        # 客户数量检查
        customer_count = db.session.query(func.count(func.distinct(BankCard.customer_id)))\
            .select_from(TaskDetail)\
            .join(BankCard, TaskDetail.card_id == BankCard.id)\
            .filter(
                TaskDetail.person_id == p.id,
                TaskDetail.task_date == task_date,
                TaskDetail.status.in_(['pending', 'completed'])
            ).scalar() or 0
        
        # 连续分配检查
        consecutive_issue = False
        if not force_allocate:
            for cid in card_ids:
                if has_consecutive_allocation(p.id, cid, task_date, TaskDetail):
                    consecutive_issue = True
                    break
        
        can_take = True
        if not force_allocate and customer_count >= MAX_CUSTOMERS_PER_PERSON:
            can_take = False
        
        person_info[p.id] = {
            'person': p,
            'customer_count': customer_count,
            'consecutive_issue': consecutive_issue,
            'can_take': can_take
        }
    
    # 按客户数量升序排列（优先分给客户少的人）
    available = [(pid, info) for pid, info in person_info.items() if info['can_take'] and not info['consecutive_issue']]
    available.sort(key=lambda x: x[1]['customer_count'])
    
    skipped_reasons = {}
    for pid, info in person_info.items():
        if not info['can_take']:
            if info['customer_count'] >= MAX_CUSTOMERS_PER_PERSON:
                skipped_reasons[f'{pid}_{info["person"].name}'] = f'今日已分配{info["customer_count"]}个客户'
        elif info['consecutive_issue']:
            skipped_reasons[f'{pid}_{info["person"].name}'] = f'已连续{MAX_CONSECUTIVE_DAYS}天分配'
    
    debug_info = {
        'task_date': task_date.strftime('%Y-%m-%d'),
        'total_cards': len(valid_card_amounts),
        'total_persons': len(persons),
        'available_persons': len(available),
        'skipped_reasons': skipped_reasons,
        'card_total_initial': dict(card_total)
    }
    
    if not available:
        return [], total_amount, debug_info
    
    # === 动态分配 ===
    remaining_by_card = dict(card_total)
    assigned_persons = set()
    
    while sum(remaining_by_card.values()) > 0 and available:
        progress_made = False
        
        for idx, (pid, info) in enumerate(available):
            if sum(remaining_by_card.values()) <= 0:
                break
            if pid in assigned_persons:
                continue
            
            person = info['person']
            total_remaining = sum(remaining_by_card.values())
            
            # 计算每卡分配金额（按比例）
            pack_amt = {}
            total_assigned_in_pack = 0
            can_assign = True
            
            for cid in card_ids:
                if remaining_by_card[cid] <= 0:
                    continue
                
                ratio = card_total[cid] / total_amount if total_amount > 0 else 1.0 / n_cards
                target = int(total_remaining * ratio)
                
                amt = min(target, remaining_by_card[cid])
                if alloc_max_val:
                    amt = min(amt, alloc_max_val)
                if amt < alloc_min_val and remaining_by_card[cid] >= alloc_min_val:
                    amt = min(alloc_min_val, remaining_by_card[cid])
                
                if amt < 1:
                    can_assign = False
                    break
                
                if amt % 100 == 0 and amt > 0:
                    amt -= 1
                
                pack_amt[cid] = amt
                total_assigned_in_pack += amt
            
            if not can_assign or total_assigned_in_pack < min_pack_total:
                continue
            
            # 分配
            for cid, amt in pack_amt.items():
                card = card_map[cid]
                bank = Bank.query.get(card.bank_id)
                allocations.append({
                    'person_id': person.id,
                    'person_name': person.name,
                    'card_id': cid,
                    'card_no': card.card_no[-4:] if card.card_no else '',
                    'amount': amt,
                    'task_date': task_date.strftime('%Y-%m-%d')
                })
                remaining_by_card[cid] -= amt
            
            assigned_persons.add(pid)
            progress_made = True
        
        if not progress_made:
            break
    
    # 尾差合并：将小额余额合并到已有分配中
    for cid in card_ids:
        if remaining_by_card[cid] > 0:
            extra = remaining_by_card[cid]
            candidates = [(i, a) for i, a in enumerate(allocations) if a['card_id'] == cid]
            if candidates:
                idx, target = max(candidates, key=lambda x: x[1]['amount'])
                new_amt = target['amount'] + extra
                # 检查是否超alloc_max（如果设置了的话）
                if not alloc_max_val or new_amt <= alloc_max_val:
                    allocations[idx]['amount'] = new_amt
                    remaining_by_card[cid] = 0
                else:
                    # 分多次加
                    remaining = extra
                    for i, a in candidates:
                        room = (alloc_max_val or float('inf')) - a['amount']
                        if room > 0 and remaining > 0:
                            add = min(room, remaining)
                            allocations[i]['amount'] += add
                            remaining -= add
                    remaining_by_card[cid] = remaining
    
    remaining_total = sum(remaining_by_card.values())
    
    debug_info['allocated_count'] = len(allocations)
    debug_info['remaining_by_card'] = remaining_by_card
    
    return allocations, remaining_total, debug_info

def adjust_parts_valid(parts, min_val, max_val):
    """
    调整金额分配列表为有效金额（不以00结尾），总和不变，遵守min/max约束
    """
    n = len(parts)
    if n == 0:
        return []
    
    result = list(parts)
    total = sum(result)
    
    # 先把每个值调整为有效且在范围内
    for i in range(n):
        if not is_valid_amount(result[i]) or result[i] < min_val or result[i] > max_val:
            valid_near = find_nearest_valid(result[i], min_val, max_val)
            result[i] = valid_near
    
    # 校验总和并修正
    current_total = sum(result)
    diff = total - current_total
    
    if diff > 0:
        # 需要增加：找空间最大的那份逐步增加
        remaining_add = diff
        for round_i in range(n):
            if remaining_add <= 0:
                break
            # 找有空间的
            candidates = sorted(range(n), key=lambda i: result[i], reverse=True)
            for idx in candidates:
                room = max_val - result[idx]
                if room <= 0:
                    continue
                # 找最大的有效增量
                for delta in range(min(room, remaining_add), 0, -1):
                    if is_valid_amount(result[idx] + delta):
                        result[idx] += delta
                        remaining_add -= delta
                        break
                if remaining_add <= 0:
                    break
            if remaining_add <= 0:
                break
        
        # 兜底：放宽max限制也尽量分配完
        if remaining_add > 0:
            for idx in range(n):
                if is_valid_amount(result[idx] + remaining_add):
                    result[idx] += remaining_add
                    remaining_add = 0
                    break
            if remaining_add > 0:
                result[-1] += remaining_add
                remaining_add = 0
    
    elif diff < 0:
        # 需要减少
        need_reduce = abs(diff)
        for round_i in range(n):
            if need_reduce <= 0:
                break
            candidates = sorted(range(n), key=lambda i: result[i])
            for idx in candidates:
                floor = min_val
                # 最后一份可以突破min
                if idx == n - 1:
                    floor = 1
                available = result[idx] - floor
                if available <= 0:
                    continue
                for delta in range(min(available, need_reduce), 0, -1):
                    if is_valid_amount(result[idx] - delta):
                        result[idx] -= delta
                        need_reduce -= delta
                        break
                if need_reduce <= 0:
                    break
            if need_reduce <= 0:
                break
        
        if need_reduce > 0:
            result[-1] -= need_reduce
            need_reduce = 0
    
    return result

def find_nearest_valid(amount, min_val, max_val):
    """找最近的有效金额"""
    if amount < min_val:
        amount = min_val
    if amount > max_val:
        amount = max_val
    if is_valid_amount(amount):
        return amount
    
    # 向下找
    for offset in range(1, 100):
        if amount - offset >= min_val and is_valid_amount(amount - offset):
            return amount - offset
        if amount + offset <= max_val and is_valid_amount(amount + offset):
            return amount + offset
    
    # 兜底
    for a in range(max(min_val, amount - 200), min(max_val, amount + 200) + 1):
        if is_valid_amount(a):
            return a
    return max(min_val, min(max_val, amount))

@transfer_task_bp.route('/create', methods=['POST'])
def create_task():
    from models import TransferTask, TaskDetail, Person, Customer, BankCard, Bank
    data = request.json
    
    customer_id = data.get('customer_id')
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'code': 400, 'message': '客户不存在'})
    
    # 获取银行金额数组
    bank_amounts = data.get('bank_amounts', [])
    # 过滤出有效的（有金额的）
    valid_bank_amounts = [ba for ba in bank_amounts if ba.get('card_id') and ba.get('amount') and int(ba['amount']) > 0]
    
    if not valid_bank_amounts:
        return jsonify({'code': 400, 'message': '请至少指定一个银行的金额'})
    
    # 校验每张卡是否属于该客户
    cards_info = []
    total_amount = 0
    first_bank_id = None
    for ba in valid_bank_amounts:
        card = BankCard.query.get(int(ba['card_id']))
        if not card:
            return jsonify({'code': 400, 'message': f'银行卡不存在'})
        if card.customer_id != int(customer_id):
            return jsonify({'code': 400, 'message': f'银行卡不属于该客户'})
        if card.status != 1:
            return jsonify({'code': 400, 'message': f'卡号****{card.card_no[-4:]}已停用'})
        amt = int(ba['amount'])
        total_amount += amt
        cards_info.append({
            'card_id': card.id,
            'bank_id': card.bank_id,
            'amount': amt
        })
        if first_bank_id is None:
            first_bank_id = card.bank_id
    
    if total_amount <= 0:
        return jsonify({'code': 400, 'message': '总金额必须大于0'})
    
    # 获取人员列表
    excluded_person_ids = data.get('excluded_person_ids', []) or []
    specified_person_ids = data.get('person_ids', []) or []
    
    persons_query = Person.query.filter(Person.status == 1)
    if excluded_person_ids:
        persons_query = persons_query.filter(Person.id.not_in(excluded_person_ids))
    persons = persons_query.all()
    
    if not persons:
        return jsonify({'code': 400, 'message': '没有可用的人员，请先添加人员'})
    
    # 如果指定了人员，检查是否存在
    if specified_person_ids:
        valid_specified = [p.id for p in persons if p.id in specified_person_ids]
        if not valid_specified:
            return jsonify({'code': 400, 'message': '指定的人员中没有可用人员'})
    
    start_date = datetime.strptime(data.get('task_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    
    alloc_min = data.get('alloc_min')
    alloc_max = data.get('alloc_max')
    force_allocate = data.get('force_allocate', False)
    if alloc_min:
        alloc_min = int(alloc_min)
    if alloc_max:
        alloc_max = int(alloc_max)
    
    # 自动补全：用户指定了max但未指定min时，设合理的min
    if alloc_max and not alloc_min:
        alloc_min = max(100, min(alloc_max, 200))
    
    # 预检查：约束可行性
    alloc_min_check = alloc_min or ALLOC_MIN
    alloc_max_check = alloc_max or None
    for ci in cards_info:
        if ci['amount'] < alloc_min_check:
            return jsonify({'code': 400, 'message': f'卡号****{BankCard.query.get(ci["card_id"]).card_no[-4:]}金额¥{ci["amount"]}低于单卡最低分配额¥{alloc_min_check}'})
        if alloc_max_check and ci['amount'] < alloc_min_check:
            return jsonify({'code': 400, 'message': f'卡号****{BankCard.query.get(ci["card_id"]).card_no[-4:]}金额¥{ci["amount"]}低于分配额度下限'})
    
    # 使用新的打包分配逻辑
    allocations, remaining, debug_info = simulate_allocate_pack(
        cards_info, persons, TaskDetail, start_date, 
        alloc_min, alloc_max, force_allocate,
        specified_person_ids if specified_person_ids else None
    )
    
    if remaining > 0 or not allocations:
        details = []
        details.append(f"日期：{debug_info.get('task_date', start_date.strftime('%Y-%m-%d'))}")
        details.append(f"总人数：{debug_info.get('total_persons', len(persons))}人")
        details.append(f"银行卡数：{debug_info.get('total_cards', len(cards_info))}张")
        details.append(f"总金额：¥{total_amount}")
        
        if debug_info.get('card_remaining_initial'):
            details.append(f"\n各卡初始金额：")
            for cid, amt in debug_info['card_remaining_initial'].items():
                card = BankCard.query.get(cid)
                tail = card.card_no[-4:] if card else cid
                details.append(f"  - ****{tail}: ¥{amt}")
        
        if debug_info.get('card_remaining_final') and sum(debug_info['card_remaining_final'].values()) > 0:
            details.append(f"\n各卡剩余未分配：")
            for cid, amt in debug_info['card_remaining_final'].items():
                if amt > 0:
                    card = BankCard.query.get(cid)
                    tail = card.card_no[-4:] if card else cid
                    details.append(f"  - ****{tail}: ¥{amt}")
        
        if debug_info.get('skipped_reasons'):
            details.append(f"\n人员跳过原因（最多显示10条）：")
            count = 0
            for person_key, reason in debug_info['skipped_reasons'].items():
                if count >= 10:
                    break
                details.append(f"  - {person_key}: {reason}")
                count += 1
        
        detail_str = '\n'.join(details)
        return jsonify({
            'code': 400,
            'message': f'无法完全分配：剩余 ¥{int(remaining)} 未分配\n\n{detail_str}',
            'data': {
                'allocated_count': len(allocations),
                'remaining_amount': int(remaining),
                'preview': allocations[:20],
                'debug_info': debug_info
            }
        })
    
    # 生成任务名称（包含所有银行名）
    bank_names = []
    for ci in cards_info:
        bank = Bank.query.get(ci['bank_id'])
        if bank and bank.name not in bank_names:
            bank_names.append(bank.name)
    task_name = f"{customer.name}_{'_'.join(bank_names)}_转账任务"
    
    task = TransferTask(
        task_name=data.get('task_name', task_name),
        customer_id=customer_id,
        bank_id=first_bank_id,  # 用第一个银行作为主银行
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
    
    task.transferred_amount = 0
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
        _backup_database()
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
        
        customer_count = db.session.query(func.count(func.distinct(BankCard.customer_id)))\
            .select_from(TaskDetail)\
            .join(BankCard, TaskDetail.card_id == BankCard.id)\
            .filter(
                TaskDetail.person_id == person.id,
                TaskDetail.task_date == task_date,
                TaskDetail.status.in_(['pending', 'completed'])
            )\
            .scalar()
        today_customer_count = customer_count
        
        if customer_count > MAX_CUSTOMERS_PER_PERSON:
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
                
                customer_count = db.session.query(func.count(func.distinct(BankCard.customer_id)))\
                    .select_from(TaskDetail)\
                    .join(BankCard, TaskDetail.card_id == BankCard.id)\
                    .filter(
                        TaskDetail.person_id == person.id,
                        TaskDetail.task_date == task_date,
                        TaskDetail.status.in_(['pending', 'completed'])
                    )\
                    .scalar()
                
                if customer_count > MAX_CUSTOMERS_PER_PERSON:
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
    
    _backup_database()
    
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
