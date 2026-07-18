import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from app import create_app
from models import Person, Customer, Bank, BankCard, TransferTask, TaskDetail
from extensions import db
from datetime import datetime

app = create_app()

EXCEL_PATH = '/Users/xkq/Desktop/流水任务/客户金额汇总表.xlsx'

CUSTOMER_COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']

BANK_MAP = {
    '工商': '工商银行',
    '建设': '建设银行'
}

PERSON_CODES = {
    '张宇': '001',
    '杜甜甜': '002',
    '张丽萍': '003',
    '王茜': '004',
    '戴': '005',
    '徐斌': '006',
    '徐妹': '007',
    '徐妹夫': '008',
    '杨柳': '009',
    '贾': '010'
}

def import_excel_data():
    with app.app_context():
        print("开始从Excel导入数据...")
        
        df = pd.read_excel(EXCEL_PATH)
        
        header_row = 1
        data_start_row = 2
        
        person_map = {p.name: p for p in Person.query.all()}
        customer_map = {c.name: c for c in Customer.query.all()}
        bank_map = {b.name: b for b in Bank.query.all()}
        
        new_persons = []
        new_customers = []
        new_banks = []
        
        print("解析Excel数据...")
        rows = []
        
        for i in range(data_start_row, len(df)):
            row = df.iloc[i]
            operator = row.iloc[0]
            date_val = row.iloc[1]
            customer_name = row.iloc[2]
            bank_short = row.iloc[3]
            wechat = row.iloc[4]
            alipay = row.iloc[5]
            
            if pd.isna(operator) or pd.isna(date_val) or pd.isna(customer_name):
                continue
            
            bank_name = BANK_MAP.get(bank_short, bank_short)
            
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)
            
            rows.append({
                'operator': str(operator).strip(),
                'date': date_str,
                'customer': str(customer_name).strip(),
                'bank': bank_name,
                'wechat': float(wechat) if not pd.isna(wechat) else 0,
                'alipay': float(alipay) if not pd.isna(alipay) else 0
            })
        
        print(f"共解析到 {len(rows)} 条记录")
        
        print("\n导入人员...")
        for row in rows:
            operator = row['operator']
            if operator not in person_map:
                code = PERSON_CODES.get(operator, f"{len(person_map) + 1:03d}")
                person = Person(
                    code=code,
                    name=operator,
                    daily_limit=6000,
                    single_min=2000,
                    single_max=6000,
                    status=1
                )
                db.session.add(person)
                new_persons.append(operator)
        
        db.session.commit()
        person_map = {p.name: p for p in Person.query.all()}
        if new_persons:
            print(f"新增人员: {', '.join(new_persons)}")
        else:
            print("无新增人员")
        
        print("\n导入客户...")
        for row in rows:
            customer_name = row['customer']
            if customer_name not in customer_map:
                color = CUSTOMER_COLORS[len(customer_map) % len(CUSTOMER_COLORS)]
                customer = Customer(name=customer_name, color=color, status=1)
                db.session.add(customer)
                new_customers.append(customer_name)
        
        db.session.commit()
        customer_map = {c.name: c for c in Customer.query.all()}
        if new_customers:
            print(f"新增客户: {', '.join(new_customers)}")
        else:
            print("无新增客户")
        
        print("\n导入银行...")
        for row in rows:
            bank_name = row['bank']
            if bank_name not in bank_map:
                bank = Bank(name=bank_name)
                db.session.add(bank)
                new_banks.append(bank_name)
        
        db.session.commit()
        bank_map = {b.name: b for b in Bank.query.all()}
        if new_banks:
            print(f"新增银行: {', '.join(new_banks)}")
        else:
            print("无新增银行")
        
        print("\n创建银行卡...")
        card_map = {}
        for card in BankCard.query.all():
            key = (card.customer_id, card.bank_id)
            card_map[key] = card
        
        new_cards = 0
        for row in rows:
            customer = customer_map.get(row['customer'])
            bank = bank_map.get(row['bank'])
            if customer and bank:
                key = (customer.id, bank.id)
                if key not in card_map:
                    card = BankCard(
                        customer_id=customer.id,
                        bank_id=bank.id,
                        card_no=f"{customer.id}{bank.id}0000",
                        status=1
                    )
                    db.session.add(card)
                    card_map[key] = card
                    new_cards += 1
        
        db.session.commit()
        print(f"新增银行卡: {new_cards} 张")
        
        print("\n导入任务...")
        task_count = 0
        for row in rows:
            person = person_map.get(row['operator'])
            customer = customer_map.get(row['customer'])
            bank = bank_map.get(row['bank'])
            
            if not person or not customer or not bank:
                print(f"跳过无效任务: {row}")
                continue
            
            card = card_map.get((customer.id, bank.id))
            if not card:
                print(f"未找到银行卡: {customer.name}-{bank.name}")
                continue
            
            total_amount = row['wechat'] + row['alipay']
            task_date = row['date']
            
            task_name = f"{customer.name}-{bank.name}-{total_amount}-{task_date}"
            
            existing_task = TransferTask.query.filter_by(
                task_name=task_name,
                customer_id=customer.id,
                bank_id=bank.id
            ).first()
            
            if existing_task:
                print(f"跳过重复任务: {task_name}")
                continue
            
            transfer_task = TransferTask(
                customer_id=customer.id,
                bank_id=bank.id,
                task_name=task_name,
                total_amount=total_amount,
                start_date=task_date,
                status='pending'
            )
            db.session.add(transfer_task)
            db.session.flush()
            
            task_detail = TaskDetail(
                task_id=transfer_task.id,
                person_id=person.id,
                card_id=card.id,
                amount=total_amount,
                status='pending',
                task_date=task_date,
                remark=f"微信:{row['wechat']},支付宝:{row['alipay']}"
            )
            db.session.add(task_detail)
            
            task_count += 1
        
        db.session.commit()
        print(f"新增任务: {task_count} 个")
        
        print("\n🎉 所有数据导入完成！")

if __name__ == '__main__':
    import_excel_data()
