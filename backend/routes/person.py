from flask import Blueprint, request, jsonify
from extensions import db

person_bp = Blueprint('person', __name__)

@person_bp.route('/list', methods=['GET'])
def get_person_list():
    from models import Person
    persons = Person.query.filter_by(status=1).order_by(Person.code).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': p.id,
            'code': p.code,
            'name': p.name,
            'daily_limit': p.daily_limit,
            'single_min': p.single_min,
            'single_max': p.single_max
        } for p in persons]
    })

@person_bp.route('/add', methods=['POST'])
def add_person():
    from models import Person
    data = request.json
    person = Person(
        code=data['code'],
        name=data.get('name', ''),
        daily_limit=data.get('daily_limit', 6000),
        single_min=data.get('single_min', 2000),
        single_max=data.get('single_max', 6000)
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
        person.single_min = data.get('single_min', person.single_min)
        person.single_max = data.get('single_max', person.single_max)
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
