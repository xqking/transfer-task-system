from app import create_app
from models import TaskDetail, Person, TransferTask, Customer, BankCard, Bank
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    print("=== 张三的所有银行卡 ===")
    zhangsan = Customer.query.filter(Customer.name.like('%张三%')).first()
    if zhangsan:
        cards = BankCard.query.filter_by(customer_id=zhangsan.id).all()
        print(f"客户: {zhangsan.name} (ID: {zhangsan.id})")
        for card in cards:
            bank = Bank.query.get(card.bank_id)
            print(f"  卡号: {card.card_no}, 银行: {bank.name}, 状态: {card.status}")
    
    print("\n=== 张三工商5月20日任务 ===")
    tasks = TransferTask.query.filter(
        TransferTask.customer_id == zhangsan.id,
        TransferTask.start_date == datetime(2026, 5, 20).date()
    ).all()
    for t in tasks:
        bank = Bank.query.get(t.bank_id)
        print(f"\n任务{t.id}: {t.task_name}, 银行: {bank.name}, 金额: {t.total_amount}")
        details = TaskDetail.query.filter_by(task_id=t.id).all()
        print(f"  分配数: {len(details)}")
        total = sum(d.amount for d in details)
        print(f"  已分配金额: {total}")
        for d in details:
            p = Person.query.get(d.person_id)
            card = BankCard.query.get(d.card_id)
            print(f"    {p.code}: ¥{d.amount} (卡****{card.card_no[-4:]})")
    
    print("\n=== 每人对张三工商卡的周统计(截止5月20日) ===")
    gongshang = Bank.query.filter(Bank.name.like('%工商%')).first()
    gongshang_cards = BankCard.query.filter(
        BankCard.customer_id == zhangsan.id,
        BankCard.bank_id == gongshang.id
    ).all()
    
    week_start = datetime(2026, 5, 14).date()  # 5月20日往前6天
    for card in gongshang_cards:
        print(f"\n【工商卡 ****{card.card_no[-4:]}】(ID:{card.id})")
        for p in Person.query.filter_by(status=1).order_by(Person.code).all():
            ds = TaskDetail.query.filter(
                TaskDetail.person_id == p.id,
                TaskDetail.card_id == card.id,
                TaskDetail.task_date >= week_start
            ).count()
            if ds > 0:
                dates_list = [x.task_date.strftime('%m-%d') for x in TaskDetail.query.filter(
                    TaskDetail.person_id == p.id,
                    TaskDetail.card_id == card.id,
                    TaskDetail.task_date >= week_start
                ).order_by(TaskDetail.task_date).all()]
                status = "❌ 达限" if ds >= 5 else "✅ 可用"
                print(f"  {p.code}: {ds}次 {dates_list} {status}")
            else:
                print(f"  {p.code}: 0次 (空闲 ✅)")
