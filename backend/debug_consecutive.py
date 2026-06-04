from app import create_app
from models import TaskDetail, Person, Customer, BankCard, Bank
from datetime import datetime

app = create_app()
with app.app_context():
    zhangsan = Customer.query.filter(Customer.name.like('%张三%')).first()
    gongshang = Bank.query.filter(Bank.name.like('%工商%')).first()
    gongshang_card = BankCard.query.filter(
        BankCard.customer_id == zhangsan.id,
        BankCard.bank_id == gongshang.id
    ).first()

    print("=== 张三工商卡 每人连续天数检查(5月20日) ===\n")
    
    target_date = datetime(2026, 5, 20).date()
    
    for p in Person.query.filter_by(status=1).order_by(Person.code).all():
        details = TaskDetail.query.filter(
            TaskDetail.person_id == p.id,
            TaskDetail.card_id == gongshang_card.id,
            TaskDetail.task_date <= target_date
        ).order_by(TaskDetail.task_date.desc()).limit(3).all()
        
        if details:
            dates = [d.task_date for d in details]
            consecutive = 0
            check_date = target_date
            
            # 检查前两天是否有任务
            d1 = target_date - __import__('datetime').timedelta(days=1)
            d2 = target_date - __import__('datetime').timedelta(days=2)
            
            has_d1 = any(d.task_date == d1 for d in details)
            has_d2 = any(d.task_date == d2 for d in details)
            
            if has_d1 and has_d2:
                status = "❌ 连续2天，第3天被拦截"
            elif has_d1:
                status = "⚠️ 连续1天，还可以1天"
            else:
                status = "✅ 可分配"
            
            date_strs = [d.strftime('%m-%d') for d in dates]
            print(f"  {p.code}: 最近任务 {date_strs} -> {status}")
        else:
            print(f"  {p.code}: 无历史任务 -> ✅ 可分配")
