import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import Person, Customer, Bank, BankCard, TransferTask, TaskDetail
from extensions import db

app = create_app()

# 人员数据
persons_data = [
    {'code': '001', 'name': '张宇'},
    {'code': '002', 'name': '杜甜甜'},
    {'code': '003', 'name': '张丽萍'},
    {'code': '004', 'name': '王茜'},
    {'code': '005', 'name': '戴'},
    {'code': '006', 'name': '徐斌'},
    {'code': '007', 'name': '徐妹'},
    {'code': '008', 'name': '徐妹夫'},
    {'code': '009', 'name': '杨柳'},
    {'code': '010', 'name': '贾'},
]

# 客户数据
customers_data = [
    {'name': '太尚', 'color': '#409eff'},
    {'name': '骏文', 'color': '#67c23a'},
    {'name': '生财', 'color': '#e6a23c'},
]

# 银行数据
banks_data = [
    {'name': '工商银行'},
    {'name': '建设银行'},
]

# 任务数据
tasks_data = [
    # 001 - 张宇
    {'person_code': '001', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 1488, 'alipay': 1891, 'date': '2026-05-23'},
    {'person_code': '001', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 2813, 'alipay': 3134, 'date': '2026-05-23'},
    {'person_code': '001', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 1670, 'alipay': 1532, 'date': '2026-05-23'},
    {'person_code': '001', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 2775, 'alipay': 1853, 'date': '2026-05-24'},
    {'person_code': '001', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 1687, 'alipay': 4313, 'date': '2026-05-24'},
    {'person_code': '001', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 2333, 'alipay': 2667, 'date': '2026-05-24'},
    
    # 002 - 杜甜甜
    {'person_code': '002', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 3004, 'alipay': 1596, 'date': '2026-05-23'},
    {'person_code': '002', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 1502, 'alipay': 1064, 'date': '2026-05-23'},
    {'person_code': '002', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 2185, 'alipay': 4330, 'date': '2026-05-23'},
    {'person_code': '002', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 3203, 'alipay': 1006, 'date': '2026-05-24'},
    {'person_code': '002', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 1576, 'alipay': 2806, 'date': '2026-05-24'},
    
    # 003 - 张丽萍
    {'person_code': '003', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 3847, 'alipay': 2153, 'date': '2026-05-23'},
    {'person_code': '003', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 1170, 'alipay': 4830, 'date': '2026-05-23'},
    {'person_code': '003', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 3181, 'alipay': 2809, 'date': '2026-05-23'},
    {'person_code': '003', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 4751, 'alipay': 1249, 'date': '2026-05-24'},
    
    # 004 - 王茜
    {'person_code': '004', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 1057, 'alipay': 1566, 'date': '2026-05-23'},
    {'person_code': '004', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 2242, 'alipay': 1668, 'date': '2026-05-23'},
    {'person_code': '004', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 2131, 'alipay': 3869, 'date': '2026-05-23'},
    {'person_code': '004', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 1007, 'alipay': 3026, 'date': '2026-05-24'},
    {'person_code': '004', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 3510, 'alipay': 2490, 'date': '2026-05-24'},
    {'person_code': '004', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 2366, 'alipay': 2634, 'date': '2026-05-24'},
    {'person_code': '004', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 4552, 'alipay': 1448, 'date': '2026-05-24'},
    {'person_code': '004', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 1200, 'alipay': 3474, 'date': '2026-05-24'},
    
    # 005 - 戴
    {'person_code': '005', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 1734, 'alipay': 1664, 'date': '2026-05-23'},
    {'person_code': '005', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 1213, 'alipay': 1214, 'date': '2026-05-23'},
    {'person_code': '005', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 2142, 'alipay': 1289, 'date': '2026-05-23'},
    {'person_code': '005', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 1193, 'alipay': 4807, 'date': '2026-05-24'},
    {'person_code': '005', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 3051, 'alipay': 2835, 'date': '2026-05-24'},
    {'person_code': '005', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 2724, 'alipay': 2518, 'date': '2026-05-24'},
    {'person_code': '005', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 1228, 'alipay': 1585, 'date': '2026-05-24'},
    {'person_code': '005', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 1355, 'alipay': 2230, 'date': '2026-05-24'},
    
    # 006 - 徐斌
    {'person_code': '006', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 4420, 'alipay': 1580, 'date': '2026-05-23'},
    {'person_code': '006', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 3197, 'alipay': 2803, 'date': '2026-05-23'},
    {'person_code': '006', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 1149, 'alipay': 2732, 'date': '2026-05-23'},
    {'person_code': '006', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 1725, 'alipay': 4275, 'date': '2026-05-23'},
    {'person_code': '006', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 1279, 'alipay': 1004, 'date': '2026-05-23'},
    {'person_code': '006', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 1607, 'alipay': 3985, 'date': '2026-05-23'},
    {'person_code': '006', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 1119, 'alipay': 4628, 'date': '2026-05-24'},
    {'person_code': '006', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 1640, 'alipay': 4300, 'date': '2026-05-24'},
    {'person_code': '006', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 3044, 'alipay': 1886, 'date': '2026-05-24'},
    
    # 007 - 徐妹
    {'person_code': '007', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 4592, 'alipay': 1408, 'date': '2026-05-23'},
    {'person_code': '007', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 3070, 'alipay': 2930, 'date': '2026-05-23'},
    {'person_code': '007', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 3364, 'alipay': 1713, 'date': '2026-05-23'},
    {'person_code': '007', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 3983, 'alipay': 1296, 'date': '2026-05-24'},
    {'person_code': '007', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 1681, 'alipay': 3450, 'date': '2026-05-24'},
    {'person_code': '007', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 1857, 'alipay': 1330, 'date': '2026-05-24'},
    {'person_code': '007', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 1814, 'alipay': 2785, 'date': '2026-05-24'},
    {'person_code': '007', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 2041, 'alipay': 2211, 'date': '2026-05-24'},
    
    # 008 - 徐妹夫
    {'person_code': '008', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 1811, 'alipay': 2201, 'date': '2026-05-23'},
    {'person_code': '008', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 2679, 'alipay': 3121, 'date': '2026-05-23'},
    {'person_code': '008', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 2338, 'alipay': 1898, 'date': '2026-05-23'},
    {'person_code': '008', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 1075, 'alipay': 4925, 'date': '2026-05-23'},
    {'person_code': '008', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 2138, 'alipay': 2229, 'date': '2026-05-24'},
    {'person_code': '008', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 2827, 'alipay': 2803, 'date': '2026-05-24'},
    {'person_code': '008', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 3560, 'alipay': 1965, 'date': '2026-05-24'},
    
    # 009 - 杨柳
    {'person_code': '009', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 4168, 'alipay': 1832, 'date': '2026-05-23'},
    {'person_code': '009', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 4020, 'alipay': 1425, 'date': '2026-05-23'},
    {'person_code': '009', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 2188, 'alipay': 2387, 'date': '2026-05-23'},
    {'person_code': '009', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 1098, 'alipay': 4902, 'date': '2026-05-23'},
    {'person_code': '009', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 2541, 'alipay': 3459, 'date': '2026-05-23'},
    {'person_code': '009', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 1555, 'alipay': 1210, 'date': '2026-05-24'},
    {'person_code': '009', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 1307, 'alipay': 1084, 'date': '2026-05-24'},
    {'person_code': '009', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 4970, 'alipay': 1030, 'date': '2026-05-24'},
    {'person_code': '009', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 2991, 'alipay': 2973, 'date': '2026-05-24'},
    
    # 010 - 贾
    {'person_code': '010', 'customer_name': '太尚', 'bank_name': '工商银行', 'wechat': 2878, 'alipay': 3122, 'date': '2026-05-23'},
    {'person_code': '010', 'customer_name': '骏文', 'bank_name': '建设银行', 'wechat': 1823, 'alipay': 4177, 'date': '2026-05-23'},
    {'person_code': '010', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 3380, 'alipay': 2243, 'date': '2026-05-23'},
    {'person_code': '010', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 4337, 'alipay': 1663, 'date': '2026-05-23'},
    {'person_code': '010', 'customer_name': '太尚', 'bank_name': '建设银行', 'wechat': 1701, 'alipay': 4299, 'date': '2026-05-24'},
    {'person_code': '010', 'customer_name': '骏文', 'bank_name': '工商银行', 'wechat': 2849, 'alipay': 2151, 'date': '2026-05-24'},
    {'person_code': '010', 'customer_name': '生财', 'bank_name': '建设银行', 'wechat': 1581, 'alipay': 3391, 'date': '2026-05-24'},
    {'person_code': '010', 'customer_name': '生财', 'bank_name': '工商银行', 'wechat': 1355, 'alipay': 2230, 'date': '2026-05-24'},
]

def import_data():
    with app.app_context():
        print("开始导入数据...")
        
        # 导入人员
        print("导入人员...")
        for p in persons_data:
            existing = Person.query.filter_by(code=p['code']).first()
            if not existing:
                person = Person(
                    code=p['code'],
                    name=p['name'],
                    daily_limit=6000,
                    single_min=2000,
                    single_max=6000,
                    status=1
                )
                db.session.add(person)
        db.session.commit()
        print(f"人员导入完成，共 {len(persons_data)} 人")
        
        # 导入客户
        print("导入客户...")
        for c in customers_data:
            existing = Customer.query.filter_by(name=c['name']).first()
            if not existing:
                customer = Customer(name=c['name'], color=c['color'], status=1)
                db.session.add(customer)
        db.session.commit()
        print(f"客户导入完成，共 {len(customers_data)} 个")
        
        # 导入银行
        print("导入银行...")
        for b in banks_data:
            existing = Bank.query.filter_by(name=b['name']).first()
            if not existing:
                bank = Bank(name=b['name'])
                db.session.add(bank)
        db.session.commit()
        print(f"银行导入完成，共 {len(banks_data)} 个")
        
        # 创建银行卡
        print("创建银行卡...")
        customers = Customer.query.all()
        banks = Bank.query.all()
        for customer in customers:
            for bank in banks:
                existing = BankCard.query.filter_by(customer_id=customer.id, bank_id=bank.id).first()
                if not existing:
                    card = BankCard(
                        customer_id=customer.id,
                        bank_id=bank.id,
                        card_number=f"{customer.id}{bank.id}0000",
                        status=1
                    )
                    db.session.add(card)
        db.session.commit()
        print("银行卡创建完成")
        
        # 导入任务
        print("导入任务...")
        person_map = {p.code: p for p in Person.query.all()}
        customer_map = {c.name: c for c in Customer.query.all()}
        bank_map = {b.name: b for b in Bank.query.all()}
        card_map = {}
        for card in BankCard.query.all():
            key = (card.customer_id, card.bank_id)
            card_map[key] = card
        
        task_count = 0
        for task_data in tasks_data:
            person = person_map.get(task_data['person_code'])
            customer = customer_map.get(task_data['customer_name'])
            bank = bank_map.get(task_data['bank_name'])
            
            if not person or not customer or not bank:
                print(f"跳过无效任务: {task_data}")
                continue
            
            card = card_map.get((customer.id, bank.id))
            if not card:
                print(f"未找到银行卡: {customer.name}-{bank.name}")
                continue
            
            total_amount = task_data['wechat'] + task_data['alipay']
            task_name = f"{customer.name}-{bank.name}-{total_amount}-{task_data['date']}"
            
            # 创建转账任务
            transfer_task = TransferTask(
                customer_id=customer.id,
                bank_id=bank.id,
                task_name=task_name,
                total_amount=total_amount,
                start_date=task_data['date'],
                status='pending'
            )
            db.session.add(transfer_task)
            db.session.flush()
            
            # 创建任务详情
            task_detail = TaskDetail(
                task_id=transfer_task.id,
                person_id=person.id,
                card_id=card.id,
                amount=total_amount,
                status='pending',
                task_date=task_data['date']
            )
            db.session.add(task_detail)
            
            task_count += 1
        
        db.session.commit()
        print(f"任务导入完成，共 {task_count} 个")
        
        print("所有数据导入完成！")

if __name__ == '__main__':
    import_data()