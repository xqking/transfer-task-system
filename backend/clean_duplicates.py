import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import Customer, BankCard, TransferTask, TaskDetail

app = create_app()

with app.app_context():
    name_counts = {}
    for c in Customer.query.all():
        name_counts[c.name] = name_counts.get(c.name, 0) + 1
    print('客户统计:', name_counts)
    
    duplicates = {}
    for c in Customer.query.all():
        if c.name not in duplicates:
            duplicates[c.name] = []
        duplicates[c.name].append(c)
    
    for name, customers in duplicates.items():
        if len(customers) > 1:
            print(f'清理重复客户: {name}, 数量: {len(customers)}')
            keep = customers[0]
            for c in customers[1:]:
                for card in BankCard.query.filter_by(customer_id=c.id).all():
                    card.customer_id = keep.id
                for task in TransferTask.query.filter_by(customer_id=c.id).all():
                    task.customer_id = keep.id
                db.session.delete(c)
    
    db.session.commit()
    print('清理完成!')
    print('剩余客户:', [c.name for c in Customer.query.all()])
