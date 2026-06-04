from app import create_app
from models import BankCard, Customer, Bank

app = create_app()

with app.app_context():
    # 找到太尚客户
    customer = Customer.query.filter_by(name='太尚').first()
    if not customer:
        print('客户太尚不存在')
        exit()
    
    # 找到工商银行
    bank = Bank.query.filter_by(name='工商银行').first()
    if not bank:
        print('工商银行不存在')
        exit()
    
    # 找到太尚的工商银行卡
    card = BankCard.query.filter_by(
        customer_id=customer.id,
        bank_id=bank.id,
        status=1
    ).first()
    
    if not card:
        print('太尚的工商银行卡不存在')
        exit()
    
    # 更新收款码（从图片中提取的编号）
    card.receive_code = '1705021000029'
    
    from extensions import db
    db.session.commit()
    
    print(f'成功更新太尚工商银行收款码: {card.receive_code}')
    print(f'银行卡号: {card.card_no}')
