from flask import Blueprint, request, jsonify
from extensions import db

customer_bp = Blueprint('customer', __name__)

CUSTOMER_COLORS = [
    '#409EFF',
    '#67C23A',
    '#E6A23C',
    '#F56C6C',
    '#9B59B6',
    '#00CED1',
    '#FF85C0',
    '#909399',
]

def pick_customer_color():
    from models import Customer
    used = {c.color for c in Customer.query.filter_by(status=1).all() if c.color}
    for color in CUSTOMER_COLORS:
        if color.upper() not in {u.upper() for u in used}:
            return color
    return CUSTOMER_COLORS[len(used) % len(CUSTOMER_COLORS)]

def customer_to_dict(customer):
    return {
        'id': customer.id,
        'name': customer.name,
        'color': customer.color or '#409EFF',
    }

@customer_bp.route('/list', methods=['GET'])
def get_customer_list():
    from models import Customer
    customers = Customer.query.filter_by(status=1).all()
    return jsonify({
        'code': 200,
        'data': [customer_to_dict(c) for c in customers]
    })

@customer_bp.route('/colors', methods=['GET'])
def get_color_palette():
    return jsonify({'code': 200, 'data': CUSTOMER_COLORS})

@customer_bp.route('/add', methods=['POST'])
def add_customer():
    from models import Customer
    data = request.json
    color = data.get('color') or pick_customer_color()
    customer = Customer(name=data['name'], color=color)
    db.session.add(customer)
    db.session.commit()
    return jsonify({'code': 200, 'message': '添加成功', 'data': customer_to_dict(customer)})

@customer_bp.route('/update/<int:id>', methods=['PUT'])
def update_customer(id):
    from models import Customer
    data = request.json
    customer = Customer.query.get(id)
    if customer:
        customer.name = data.get('name', customer.name)
        if data.get('color'):
            customer.color = data['color']
        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功', 'data': customer_to_dict(customer)})
    return jsonify({'code': 400, 'message': '客户不存在'})

@customer_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_customer(id):
    from models import Customer
    customer = Customer.query.get(id)
    if customer:
        customer.status = 0
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    return jsonify({'code': 400, 'message': '客户不存在'})

@customer_bp.route('/batch-delete', methods=['DELETE'])
def batch_delete_customer():
    from models import Customer
    data = request.json
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'code': 400, 'message': '请选择要删除的客户'})
    
    count = 0
    for id in ids:
        customer = Customer.query.get(id)
        if customer:
            customer.status = 0
            count += 1
    
    db.session.commit()
    return jsonify({'code': 200, 'message': f'成功删除 {count} 个客户'})

@customer_bp.route('/banks', methods=['GET'])
def get_banks():
    from models import Bank
    banks = Bank.query.filter_by(status=1).all()
    return jsonify({
        'code': 200,
        'data': [{'id': b.id, 'name': b.name, 'code': b.code} for b in banks]
    })

@customer_bp.route('/cards', methods=['GET'])
def get_customer_cards():
    from models import BankCard, Bank
    customer_id = request.args.get('customer_id')
    if not customer_id:
        return jsonify({'code': 400, 'message': '请选择客户'})
    
    cards = BankCard.query.filter_by(
        customer_id=int(customer_id),
        status=1
    ).all()
    
    result = []
    for card in cards:
        bank = Bank.query.get(card.bank_id)
        result.append({
            'id': card.id,
            'bank_id': card.bank_id,
            'bank_name': bank.name if bank else '',
            'bank_color': bank.color if bank and hasattr(bank, 'color') else '#666',
            'card_number': card.card_no,
            'card_tail': card.card_no[-4:] if card.card_no else ''
        })
    
    return jsonify({
        'code': 200,
        'data': result
    })
