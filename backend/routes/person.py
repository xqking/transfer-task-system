from flask import Blueprint, request, jsonify
from extensions import db

person_bp = Blueprint('person', __name__)

@person_bp.route('/list', methods=['GET'])
def get_person_list():
    from models import Person
    persons = Person.query.filter_by(status=1).order_by(Person.id).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': p.id,
            'name': p.name,
            'daily_limit': p.daily_limit
        } for p in persons]
    })

@person_bp.route('/add', methods=['POST'])
def add_person():
    from models import Person
    data = request.json
    name = data.get('name', '')
    
    if not name:
        return jsonify({'code': 400, 'message': '请输入姓名'})
    
    existing = Person.query.filter_by(name=name).first()
    if existing and existing.status == 0:
        existing.status = 1
        existing.daily_limit = data.get('daily_limit', existing.daily_limit)
        db.session.commit()
        return jsonify({'code': 200, 'message': '添加成功'})
    
    if existing and existing.status == 1:
        return jsonify({'code': 400, 'message': '该人员已存在'})
    
    max_id = db.session.query(db.func.max(Person.id)).scalar() or 0
    person = Person(
        code=f'P{max_id + 1:03d}',
        name=name,
        daily_limit=data.get('daily_limit', 6000)
    )
    db.session.add(person)
    db.session.commit()
    return jsonify({'code': 200, 'message': '添加成功'})

@person_bp.route('/update/<int:id>', methods=['PUT'])
def update_person(id):
    from models import Person
    data = request.json
    person = Person.query.get(id)
    if person:
        person.name = data.get('name', person.name)
        person.daily_limit = data.get('daily_limit', person.daily_limit)
        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功'})
    return jsonify({'code': 400, 'message': '人员不存在'})

@person_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_person(id):
    from models import Person
    person = Person.query.get(id)
    if person:
        person.status = 0
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    return jsonify({'code': 400, 'message': '人员不存在'})
