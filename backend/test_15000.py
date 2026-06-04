from app import create_app
from models import TransferTask, TaskDetail, Person, Customer, BankCard, Bank
from datetime import datetime
from routes.transfer_task import simulate_allocate, get_alloc_limits

app = create_app()
with app.app_context():
    customer_id = 2  # 骏文
    bank_id = 1      # 建设银行
    total_amount = 15000
    task_date = datetime.now().date()
    
    customer = Customer.query.get(customer_id)
    bank = Bank.query.get(bank_id)
    
    print(f"客户: {customer.name if customer else '不存在'}")
    print(f"银行: {bank.name if bank else '不存在'}")
    
    cards = BankCard.query.filter(
        BankCard.customer_id == customer_id,
        BankCard.bank_id == bank_id,
        BankCard.status == 1
    ).all()
    
    print(f"\n可用银行卡: {len(cards)}张")
    for card in cards:
        print(f"  - 卡号: ****{card.card_no[-4:]}")
    
    persons = Person.query.filter_by(status=1).all()
    print(f"\n可用人员: {len(persons)}人")
    
    alloc_min, alloc_max = get_alloc_limits(total_amount)
    print(f"\n金额配置: 最小{alloc_min}, 最大{alloc_max}")
    
    print("\n开始模拟分配...")
    allocations, remaining, debug_info = simulate_allocate(total_amount, cards, persons, TaskDetail, task_date)
    
    print(f"\n分配结果:")
    print(f"  已分配: {len(allocations)}条")
    print(f"  剩余金额: ¥{remaining}")
    
    if allocations:
        print("\n分配详情:")
        total_allocated = 0
        for i, alloc in enumerate(allocations, 1):
            person = Person.query.get(alloc['person_id'])
            total_allocated += alloc['amount']
            print(f"  {i}. {person.code if person else '未知'} - ¥{alloc['amount']}")
        print(f"\n  合计: ¥{total_allocated}")
    
    if remaining > 0:
        print("\n调试信息:")
        for card in debug_info['card_details']:
            print(f"\n卡号 ****{card['card_no']}:")
            print(f"  可用额度: ¥{card['card_room']}")
            print(f"  已分配人数: {card['assigned_count']}")
            if card['skipped_reasons']:
                print("  跳过原因:")
                for reason in card['skipped_reasons'].values():
                    print(f"    - {reason}")
