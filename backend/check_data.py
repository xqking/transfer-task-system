from app import create_app
from models import BankCard

app = create_app()

with app.app_context():
    cards = BankCard.query.all()
    print(f'总共有 {len(cards)} 条银行卡记录')
    for c in cards:
        customer_name = c.customer.name if c.customer else "无客户"
        bank_name = c.bank.name if c.bank else "无银行"
        print(f'{c.id}: {customer_name} - {bank_name} - {c.card_no} - 状态:{c.status}')
