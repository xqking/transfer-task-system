from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from extensions import db

task_detail_bp = Blueprint('task_detail', __name__)

@task_detail_bp.route('/list', methods=['GET'])
def get_all_task_details():
    from models import TaskDetail
    details = TaskDetail.query.order_by(TaskDetail.task_date.desc(), TaskDetail.id.desc()).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': d.id,
            'task_id': d.task_id,
            'person_id': d.person.id if d.person else None,
            'person_name': d.person.name if d.person else '',
            'card_no': d.card.card_no if d.card else '',
            'bank_name': d.card.bank.name if d.card and d.card.bank else '',
            'amount': d.amount,
            'wechat_amount': d.wechat_amount or 0,
            'alipay_amount': d.alipay_amount or 0,
            'task_date': d.task_date.strftime('%Y-%m-%d') if d.task_date else '',
            'status': d.status,
            'execute_time': d.execute_time.strftime('%Y-%m-%d %H:%M:%S') if d.execute_time else '',
            'remark': d.remark,
            'customer_name': d.task.customer.name if d.task and d.task.customer else '',
            'customer_color': d.task.customer.color if d.task and d.task.customer else '#409EFF'
        } for d in details]
    })

@task_detail_bp.route('/list/<int:task_id>', methods=['GET'])
def get_task_details(task_id):
    from models import TaskDetail
    details = TaskDetail.query.filter_by(task_id=task_id).order_by(TaskDetail.task_date, TaskDetail.person_id).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': d.id,
            'person_id': d.person.id if d.person else None,
            'person_name': d.person.name if d.person else '',
            'card_no': d.card.card_no if d.card else '',
            'bank_name': d.card.bank.name if d.card and d.card.bank else '',
            'amount': d.amount,
            'task_date': d.task_date.strftime('%Y-%m-%d') if d.task_date else '',
            'status': d.status,
            'execute_time': d.execute_time.strftime('%Y-%m-%d %H:%M:%S') if d.execute_time else '',
            'remark': d.remark
        } for d in details]
    })

@task_detail_bp.route('/update-status/<int:id>', methods=['PUT'])
def update_detail_status(id):
    from models import TaskDetail, TransferTask
    data = request.json
    detail = TaskDetail.query.get(id)
    if detail:
        detail.status = data.get('status', detail.status)
        if data.get('status') == 'completed':
            detail.execute_time = datetime.now()
        detail.remark = data.get('remark', detail.remark)
        db.session.commit()
        
        task = TransferTask.query.get(detail.task_id)
        if task:
            completed_amount = sum(d.amount for d in task.details if d.status == 'completed')
            task.transferred_amount = completed_amount
            if completed_amount >= task.total_amount:
                task.status = 'completed'
            elif completed_amount > 0:
                task.status = 'executing'
            db.session.commit()
        
        return jsonify({'code': 200, 'message': '更新成功'})
    return jsonify({'code': 400, 'message': '记录不存在'})

@task_detail_bp.route('/update/<int:id>', methods=['PUT'])
def update_task_detail(id):
    from models import TaskDetail, TransferTask, Person, BankCard
    data = request.json
    detail = TaskDetail.query.get(id)
    
    if not detail:
        return jsonify({'code': 400, 'message': '记录不存在'})
    
    if 'person_id' in data:
        person = Person.query.get(data['person_id'])
        if person:
            detail.person_id = person.id
    
    if 'amount' in data:
        detail.amount = data['amount']
    
    if 'wechat_amount' in data:
        detail.wechat_amount = data['wechat_amount']
    
    if 'alipay_amount' in data:
        detail.alipay_amount = data['alipay_amount']
    
    if 'status' in data:
        detail.status = data['status']
        if data['status'] == 'completed':
            detail.execute_time = datetime.now()
    
    if 'task_date' in data:
        detail.task_date = datetime.strptime(data['task_date'], '%Y-%m-%d').date()
    
    if 'remark' in data:
        detail.remark = data['remark']
    
    db.session.commit()
    
    task = TransferTask.query.get(detail.task_id)
    if task:
        completed_amount = sum(d.amount for d in task.details if d.status == 'completed')
        task.transferred_amount = completed_amount
        if completed_amount >= task.total_amount:
            task.status = 'completed'
        elif completed_amount > 0:
            task.status = 'executing'
        else:
            task.status = 'pending'
        db.session.commit()
    
    return jsonify({'code': 200, 'message': '更新成功'})

@task_detail_bp.route('/batch-update-status', methods=['PUT'])
def batch_update_status():
    from models import TaskDetail, TransferTask
    data = request.json
    ids = data.get('ids', [])
    status = data.get('status', 'pending')
    
    if not ids:
        return jsonify({'code': 400, 'message': '请选择要更新的记录'})
    
    updated_count = 0
    task_ids = set()
    
    for id in ids:
        detail = TaskDetail.query.get(id)
        if detail:
            detail.status = status
            if status == 'completed':
                detail.execute_time = datetime.now()
            db.session.commit()
            updated_count += 1
            task_ids.add(detail.task_id)
    
    for task_id in task_ids:
        task = TransferTask.query.get(task_id)
        if task:
            completed_amount = sum(d.amount for d in task.details if d.status == 'completed')
            task.transferred_amount = completed_amount
            if completed_amount >= task.total_amount:
                task.status = 'completed'
            elif completed_amount > 0:
                task.status = 'executing'
            else:
                task.status = 'pending'
            db.session.commit()
    
    return jsonify({'code': 200, 'message': f'成功更新 {updated_count} 条记录'})

@task_detail_bp.route('/batch-delete', methods=['DELETE'])
def batch_delete_details():
    from models import TaskDetail, TransferTask
    data = request.json
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({'code': 400, 'message': '请选择要删除的记录'})
    
    deleted_count = 0
    task_ids = set()
    
    for id in ids:
        detail = TaskDetail.query.get(id)
        if detail:
            task_ids.add(detail.task_id)
            db.session.delete(detail)
            db.session.commit()
            deleted_count += 1
    
    for task_id in task_ids:
        task = TransferTask.query.get(task_id)
        if task:
            remaining_details = TaskDetail.query.filter_by(task_id=task_id).count()
            if remaining_details == 0:
                db.session.delete(task)
            else:
                task.total_amount = sum(d.amount for d in task.details)
                completed_amount = sum(d.amount for d in task.details if d.status == 'completed')
                task.transferred_amount = completed_amount
                if completed_amount >= task.total_amount:
                    task.status = 'completed'
                elif completed_amount > 0:
                    task.status = 'executing'
                else:
                    task.status = 'pending'
            db.session.commit()
    
    return jsonify({'code': 200, 'message': f'成功删除 {deleted_count} 条记录'})

@task_detail_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_task_detail(id):
    from models import TaskDetail, TransferTask
    detail = TaskDetail.query.get(id)
    
    if not detail:
        return jsonify({'code': 400, 'message': '记录不存在'})
    
    task_id = detail.task_id
    task = TransferTask.query.get(task_id)
    
    db.session.delete(detail)
    db.session.commit()
    
    if task:
        remaining_details = TaskDetail.query.filter_by(task_id=task_id).count()
        if remaining_details == 0:
            db.session.delete(task)
        else:
            task.total_amount = sum(d.amount for d in task.details)
            completed_amount = sum(d.amount for d in task.details if d.status == 'completed')
            task.transferred_amount = completed_amount
            if completed_amount >= task.total_amount:
                task.status = 'completed'
            elif completed_amount > 0:
                task.status = 'executing'
            else:
                task.status = 'pending'
        db.session.commit()
    
    return jsonify({'code': 200, 'message': '删除成功'})

@task_detail_bp.route('/create', methods=['POST'])
def create_task_detail():
    from models import TaskDetail, TransferTask, Person, BankCard, Customer, Bank
    data = request.json
    
    person_id = data.get('person_id')
    customer_id = data.get('customer_id')
    bank_id = data.get('bank_id')
    amount = data.get('amount')
    wechat_amount = data.get('wechat_amount', 0)
    alipay_amount = data.get('alipay_amount', 0)
    task_date = data.get('task_date')
    remark = data.get('remark', '')
    
    if not person_id or not customer_id or not bank_id or not amount or not task_date:
        return jsonify({'code': 400, 'message': '缺少必要参数'})
    
    person = Person.query.get(person_id)
    if not person:
        return jsonify({'code': 400, 'message': '人员不存在'})
    
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'code': 400, 'message': '客户不存在'})
    
    bank = Bank.query.get(bank_id)
    if not bank:
        return jsonify({'code': 400, 'message': '银行不存在'})
    
    card = BankCard.query.filter_by(customer_id=customer_id, bank_id=bank_id).first()
    if not card:
        return jsonify({'code': 400, 'message': '该客户在该银行下没有银行卡'})
    
    card_id = card.id
    
    task_name = f'{customer.name}_{bank.name}_手动任务_{task_date}'
    task = TransferTask.query.filter_by(
        customer_id=customer_id,
        bank_id=bank_id,
        task_type='manual',
        start_date=datetime.strptime(task_date, '%Y-%m-%d').date()
    ).first()
    
    if not task:
        task = TransferTask(
            task_name=task_name,
            customer_id=customer_id,
            bank_id=bank_id,
            total_amount=amount,
            transferred_amount=0,
            task_type='manual',
            start_date=datetime.strptime(task_date, '%Y-%m-%d').date(),
            status='pending',
            remark=remark or '手动添加'
        )
        db.session.add(task)
        db.session.commit()
    else:
        task.total_amount += amount
        db.session.commit()
    
    task_date_obj = datetime.strptime(task_date, '%Y-%m-%d').date()
    
    status = data.get('status', 'pending')
    
    detail = TaskDetail(
        task_id=task.id,
        person_id=person.id,
        card_id=card_id,
        amount=amount,
        wechat_amount=wechat_amount,
        alipay_amount=alipay_amount,
        task_date=task_date_obj,
        status=status,
        remark=remark
    )
    
    db.session.add(detail)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': {
            'id': detail.id,
            'task_id': task.id,
            'person_id': person.id,
            'person_name': person.name,
            'card_no': card.card_no,
            'bank_name': card.bank.name,
            'amount': amount,
            'task_date': task_date,
            'status': status,
            'remark': remark,
            'customer_name': card.customer.name,
            'customer_color': card.customer.color
        }
    })

@task_detail_bp.route('/calendar', methods=['POST'])
def get_calendar_data():
    from models import TaskDetail
    data = request.json
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    
    query = TaskDetail.query.filter(
        TaskDetail.task_date >= start_date,
        TaskDetail.task_date <= end_date
    )
    
    customer_id = data.get('customer_id')
    person_id = data.get('person_id')
    bank_id = data.get('bank_id')
    
    if customer_id:
        from models import TransferTask
        query = query.join(TransferTask)
        query = query.filter(TransferTask.customer_id == customer_id)
    
    if bank_id:
        from models import BankCard
        query = query.join(BankCard, TaskDetail.card_id == BankCard.id)
        query = query.filter(BankCard.bank_id == bank_id)
    
    if person_id:
        query = query.filter(TaskDetail.person_id == person_id)
    
    details = query.all()
    
    persons = {}
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    for d in details:
        person_id = d.person.id if d.person else 0
        person_name = d.person.name if d.person else '未知'
        if person_id not in persons:
            persons[person_id] = {'id': person_id, 'name': person_name, 'tasks': {}}
        
        date_str = d.task_date.strftime('%Y-%m-%d')
        if date_str not in persons[person_id]['tasks']:
            persons[person_id]['tasks'][date_str] = []
        
        customer = d.task.customer if d.task else None
        persons[person_id]['tasks'][date_str].append({
            'id': d.id,
            'amount': d.amount,
            'wechat_amount': d.wechat_amount or 0,
            'alipay_amount': d.alipay_amount or 0,
            'task_date': date_str,
            'task_id': d.task_id,
            'customer_id': customer.id if customer else None,
            'customer_name': customer.name if customer else '',
            'customer_color': customer.color if customer and customer.color else '#409EFF',
            'bank_id': d.card.bank_id if d.card else None,
            'bank_name': d.card.bank.name if d.card and d.card.bank else '',
            'status': d.status,
            'person_id': person_id,
            'person_name': person_name,
            'remark': d.remark or ''
        })
    
    return jsonify({
        'code': 200,
        'data': {
            'dates': dates,
            'persons': persons
        }
    })

@task_detail_bp.route('/merge-tasks', methods=['POST'])
def merge_tasks():
    from models import TransferTask, TaskDetail
    data = request.json
    
    from_task_id = data.get('from_task_id')
    to_task_id = data.get('to_task_id')
    
    if not from_task_id or not to_task_id:
        return jsonify({'code': 400, 'message': '缺少必要参数'})
    
    from_task = TransferTask.query.get(from_task_id)
    to_task = TransferTask.query.get(to_task_id)
    
    if not from_task:
        return jsonify({'code': 400, 'message': '源任务不存在'})
    
    if not to_task:
        return jsonify({'code': 400, 'message': '目标任务不存在'})
    
    if from_task.id == to_task.id:
        return jsonify({'code': 400, 'message': '不能合并到自身'})
    
    TaskDetail.query.filter_by(task_id=from_task_id).update({'task_id': to_task_id})
    
    to_task.total_amount += from_task.total_amount
    to_task.transferred_amount += from_task.transferred_amount
    
    db.session.delete(from_task)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '合并成功', 'data': {'merged_amount': from_task.total_amount}})

@task_detail_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    from models import TaskDetail, Customer, BankCard, Bank
    
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    customers = Customer.query.filter_by(status=1).all()
    
    result = []
    
    for customer in customers:
        cards = BankCard.query.filter_by(customer_id=customer.id, status=1).all()
        
        customer_total = 0
        customer_completed = 0
        customer_failed = 0
        
        card_data = []
        for card in cards:
            bank = Bank.query.get(card.bank_id)
            
            card_total = TaskDetail.query.filter(
                TaskDetail.card_id == card.id,
                TaskDetail.task_date >= start_date_obj,
                TaskDetail.task_date <= end_date_obj
            ).with_entities(func.sum(TaskDetail.amount)).scalar() or 0
            
            card_completed = TaskDetail.query.filter(
                TaskDetail.card_id == card.id,
                TaskDetail.task_date >= start_date_obj,
                TaskDetail.task_date <= end_date_obj,
                TaskDetail.status == 'completed'
            ).with_entities(func.sum(TaskDetail.amount)).scalar() or 0
            
            card_failed = TaskDetail.query.filter(
                TaskDetail.card_id == card.id,
                TaskDetail.task_date >= start_date_obj,
                TaskDetail.task_date <= end_date_obj,
                TaskDetail.status == 'failed'
            ).with_entities(func.sum(TaskDetail.amount)).scalar() or 0
            
            card_data.append({
                'card_id': card.id,
                'bank_id': bank.id,
                'bank_name': bank.name,
                'card_no': card.card_no[-4:],
                'total_amount': card_total,
                'completed_amount': card_completed,
                'pending_amount': card_total - card_completed - card_failed,
                'failed_amount': card_failed
            })
            
            customer_total += card_total
            customer_completed += card_completed
            customer_failed += card_failed
        
        result.append({
            'customer_id': customer.id,
            'customer_name': customer.name,
            'customer_color': customer.color,
            'total_amount': customer_total,
            'completed_amount': customer_completed,
            'pending_amount': customer_total - customer_completed - customer_failed,
            'failed_amount': customer_failed,
            'cards': card_data
        })
    
    return jsonify({
        'code': 200,
        'data': {
            'start_date': start_date,
            'end_date': end_date,
            'customers': result,
            'grand_total': sum(c['total_amount'] for c in result),
            'grand_completed': sum(c['completed_amount'] for c in result),
            'grand_pending': sum(c['pending_amount'] for c in result),
            'grand_failed': sum(c['failed_amount'] for c in result)
        }
    })
