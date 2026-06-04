from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
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
            'person_code': d.person.code if d.person else '',
            'card_no': d.card.card_no if d.card else '',
            'bank_name': d.card.bank.name if d.card and d.card.bank else '',
            'amount': d.amount,
            'task_date': d.task_date.strftime('%Y-%m-%d') if d.task_date else '',
            'status': d.status,
            'execute_time': d.execute_time.strftime('%Y-%m-%d %H:%M:%S') if d.execute_time else '',
            'remark': d.remark
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
            'person_code': d.person.code if d.person else '',
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
    if customer_id:
        from models import TransferTask
        query = query.join(TransferTask).filter(TransferTask.customer_id == customer_id)
    
    person_id = data.get('person_id')
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
        person_code = d.person.code if d.person else 'unknown'
        if person_code not in persons:
            persons[person_code] = {'code': person_code, 'tasks': {}}
        
        date_str = d.task_date.strftime('%Y-%m-%d')
        if date_str not in persons[person_code]['tasks']:
            persons[person_code]['tasks'][date_str] = []
        
        customer = d.task.customer if d.task else None
        persons[person_code]['tasks'][date_str].append({
            'id': d.id,
            'amount': d.amount,
            'task_date': date_str,
            'task_id': d.task_id,
            'customer_id': customer.id if customer else None,
            'customer_name': customer.name if customer else '',
            'customer_color': customer.color if customer and customer.color else '#409EFF',
            'bank_name': d.card.bank.name if d.card and d.card.bank else '',
            'status': d.status,
            'person_code': person_code
        })
    
    return jsonify({
        'code': 200,
        'data': {
            'dates': dates,
            'persons': persons
        }
    })
