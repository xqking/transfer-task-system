from flask import Blueprint, request, jsonify, send_from_directory
from extensions import db
import os
import uuid

bankcard_bp = Blueprint('bankcard', __name__)

@bankcard_bp.route('/list', methods=['GET'])
def get_card_list():
    from models import BankCard
    cards = BankCard.query.filter_by(status=1).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': c.id,
            'customer_id': c.customer_id,
            'customer_name': c.customer.name if c.customer else '',
            'bank_name': c.bank.name if c.bank else '',
            'card_no': c.card_no,
            'receive_code': c.receive_code if c.receive_code else ''
        } for c in cards]
    })

@bankcard_bp.route('/add', methods=['POST'])
def add_card():
    from models import BankCard
    from app import create_app
    
    app = create_app()
    
    # 处理表单数据
    customer_id = request.form.get('customer_id')
    bank_id = request.form.get('bank_id')
    card_no = request.form.get('card_no')
    receive_code = request.form.get('receive_code', '')
    
    # 处理文件上传
    if 'receive_code_file' in request.files:
        file = request.files['receive_code_file']
        if file and file.filename:
            # 确保上传目录存在
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            # 生成唯一文件名
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            receive_code = f"/uploads/{filename}"
    
    card = BankCard(
        customer_id=customer_id,
        bank_id=bank_id,
        card_no=card_no,
        receive_code=receive_code
    )
    db.session.add(card)
    db.session.commit()
    return jsonify({'code': 200, 'message': '添加成功'})

@bankcard_bp.route('/update/<int:id>', methods=['POST'])
def update_card(id):
    from models import BankCard
    from app import create_app
    
    app = create_app()
    card = BankCard.query.get(id)
    
    if card:
        # 处理表单数据
        if 'receive_code' in request.form:
            card.receive_code = request.form['receive_code']
        
        # 处理文件上传
        if 'receive_code_file' in request.files:
            file = request.files['receive_code_file']
            if file and file.filename:
                # 删除旧文件
                if card.receive_code and card.receive_code.startswith('/uploads/'):
                    old_file = os.path.join(app.config['UPLOAD_FOLDER'], card.receive_code[9:])
                    if os.path.exists(old_file):
                        os.remove(old_file)
                
                # 确保上传目录存在
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # 保存新文件
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                card.receive_code = f"/uploads/{filename}"
        
        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功'})
    return jsonify({'code': 400, 'message': '银行卡不存在'})

@bankcard_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_card(id):
    from models import BankCard
    from app import create_app
    
    app = create_app()
    card = BankCard.query.get(id)
    
    if card:
        # 删除关联的图片文件
        if card.receive_code and card.receive_code.startswith('/uploads/'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], card.receive_code[9:])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        card.status = 0
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    return jsonify({'code': 400, 'message': '银行卡不存在'})
