from app import create_app
from models import BankCard, Customer, Bank
import os
import uuid

app = create_app()

# 收款码图片目录
QR_CODE_DIR = '/Users/eva/Desktop/test-project/Payment QR code'

# 映射文件名中的客户名
CUSTOMER_MAP = {
    '太尚': '太尚',
    '骏文': '骏文',
    '俊文': '骏文',  # 处理错别字
    '生财': '生财'
}

# 映射文件名中的银行名
BANK_MAP = {
    '建设': '建设银行',
    '工商': '工商银行'
}

def parse_filename(filename):
    """解析文件名，提取客户名和银行名"""
    # 去掉扩展名
    name = filename
    while '.' in name:
        name = name.rsplit('.', 1)[0]
    
    # 查找客户名
    customer_name = None
    for key in CUSTOMER_MAP:
        if key in name:
            customer_name = CUSTOMER_MAP[key]
            break
    
    # 查找银行名
    bank_name = None
    for key in BANK_MAP:
        if key in name:
            bank_name = BANK_MAP[key]
            break
    
    return customer_name, bank_name

with app.app_context():
    # 获取所有收款码文件
    if not os.path.exists(QR_CODE_DIR):
        print(f'错误：目录不存在 {QR_CODE_DIR}')
        exit()
    
    files = [f for f in os.listdir(QR_CODE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    print(f'找到 {len(files)} 个收款码文件')
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    success_count = 0
    failed_count = 0
    
    for filename in files:
        customer_name, bank_name = parse_filename(filename)
        
        if not customer_name or not bank_name:
            print(f'跳过无法识别的文件: {filename}')
            failed_count += 1
            continue
        
        # 查找客户
        customer = Customer.query.filter_by(name=customer_name).first()
        if not customer:
            print(f'客户不存在: {customer_name}')
            failed_count += 1
            continue
        
        # 查找银行
        bank = Bank.query.filter_by(name=bank_name).first()
        if not bank:
            print(f'银行不存在: {bank_name}')
            failed_count += 1
            continue
        
        # 查找对应的银行卡
        card = BankCard.query.filter_by(
            customer_id=customer.id,
            bank_id=bank.id,
            status=1
        ).first()
        
        if not card:
            print(f'未找到银行卡: {customer_name} - {bank_name}')
            failed_count += 1
            continue
        
        # 复制图片到上传目录
        src_path = os.path.join(QR_CODE_DIR, filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4().hex}.{ext}"
        dst_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        
        # 读取并保存文件
        with open(src_path, 'rb') as f:
            content = f.read()
        with open(dst_path, 'wb') as f:
            f.write(content)
        
        # 更新银行卡记录
        card.receive_code = f"/uploads/{new_filename}"
        from extensions import db
        db.session.commit()
        
        print(f'✓ 成功: {filename} -> {customer_name} - {bank_name}')
        success_count += 1
    
    print(f'\n批量导入完成：成功 {success_count} 个，失败 {failed_count} 个')
