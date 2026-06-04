from app import create_app
from models import BankCard, Customer, Person, Bank

app = create_app()
with app.app_context():
    cards = BankCard.query.filter_by(status=1).all()
    print(f'可用银行卡数量: {len(cards)}')
    for c in cards:
        print(f'ID:{c.id}, 客户ID:{c.customer_id}, 银行ID:{c.bank_id}, 卡号:{c.card_no}')
    
    customers = Customer.query.all()
    print(f'\n客户数量: {len(customers)}')
    for cust in customers:
        print(f'ID:{cust.id}, 名称:{cust.name}')
    
    persons = Person.query.filter_by(status=1).all()
    print(f'\n可用人员数量: {len(persons)}')
    
    banks = Bank.query.all()
    print(f'\n银行数量: {len(banks)}')
    for b in banks:
        print(f'ID:{b.id}, 名称:{b.name}')
