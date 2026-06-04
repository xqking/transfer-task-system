from app import create_app
from models import TaskDetail, Person, TransferTask, Customer, BankCard, Bank
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    zhangsan = Customer.query.filter(Customer.name.like('%张三%')).first()
    
    print("=== 张三所有任务(按日期) ===")
    tasks = TransferTask.query.filter(TransferTask.customer_id == zhangsan.id).order_by(TransferTask.start_date).all()
    for t in tasks:
        bank = Bank.query.get(t.bank_id)
        details = TaskDetail.query.filter_by(task_id=t.id).all()
        total_amt = sum(d.amount for d in details)
        persons = [Person.query.get(d.person_id).code for d in details]
        print(f"{t.start_date} | {bank.name:6s} | {t.task_name:15s} | {len(details)}人 | ¥{total_amt:8.0f} | 人员: {persons}")
    
    print("\n=== 按人员统计每张卡的次数 ===")
    gongshang = Bank.query.filter(Bank.name.like('%工商%')).first()
    jianye = Bank.query.filter(Bank.name.like('%建业%')).first()
    
    gongshang_card = BankCard.query.filter(
        BankCard.customer_id == zhangsan.id,
        BankCard.bank_id == gongshang.id
    ).first()
    
    jianye_card = BankCard.query.filter(
        BankCard.customer_id == zhangsan.id,
        BankCard.bank_id == jianye.id
    ).first()
    
    week_start = datetime(2026, 5, 14).date()
    
    print(f"\n【工商卡】ID:{gongshang_card.id if gongshang_card else '无'}")
    for p in Person.query.filter_by(status=1).order_by(Person.code).all():
        ds = TaskDetail.query.filter(
            TaskDetail.person_id == p.id,
            TaskDetail.card_id == gongshang_card.id,
            TaskDetail.task_date >= week_start
        ).count()
        print(f"  {p.code}: {ds}次")
    
    print(f"\n【建业卡】ID:{jianye_card.id if jianye_card else '无'}")
    for p in Person.query.filter_by(status=1).order_by(Person.code).all():
        ds = TaskDetail.query.filter(
            TaskDetail.person_id == p.id,
            TaskDetail.card_id == jianye_card.id,
            TaskDetail.task_date >= week_start
        ).count()
        print(f"  {p.code}: {ds}次")
