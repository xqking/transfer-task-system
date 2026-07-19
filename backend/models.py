from extensions import db
from datetime import datetime

class Bank(db.Model):
    __tablename__ = 'banks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True, comment='银行名称')
    code = db.Column(db.String(20), nullable=False, unique=True, comment='银行代码')
    status = db.Column(db.Integer, default=1, comment='状态 1-启用 0-禁用')
    created_at = db.Column(db.DateTime, default=datetime.now)

class Person(db.Model):
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), unique=True, nullable=False, comment='人员编号')
    name = db.Column(db.String(50), default='', comment='人员姓名')
    status = db.Column(db.Integer, default=1, comment='状态 1-可用 0-不可用')
    daily_limit = db.Column(db.Float, default=6000, comment='单日转账上限')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='客户名称')
    color = db.Column(db.String(20), default='#409EFF', comment='标识颜色')
    status = db.Column(db.Integer, default=1, comment='状态 1-正常 0-停用')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    cards = db.relationship('BankCard', backref='customer', lazy=True)

class BankCard(db.Model):
    __tablename__ = 'bank_cards'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)
    card_no = db.Column(db.String(30), nullable=False, comment='银行卡号')
    receive_code = db.Column(db.String(255), comment='收款码（图片路径或文本）')
    status = db.Column(db.Integer, default=1, comment='状态 1-正常 0-停用')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    bank = db.relationship('Bank', backref='cards')

class TransferTask(db.Model):
    __tablename__ = 'transfer_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_name = db.Column(db.String(100), comment='任务名称')
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False, comment='任务总金额')
    transferred_amount = db.Column(db.Float, default=0, comment='已转账金额')
    task_type = db.Column(db.String(20), default='daily', comment='任务类型 daily-单日 weekly-周任务')
    start_date = db.Column(db.Date, nullable=False, comment='开始日期')
    end_date = db.Column(db.Date, comment='结束日期')
    status = db.Column(db.String(20), default='pending', comment='状态 pending-待执行 executing-执行中 completed-已完成 cancelled-已取消')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    customer = db.relationship('Customer', backref='tasks')
    bank = db.relationship('Bank', backref='tasks')
    details = db.relationship('TaskDetail', backref='task', lazy=True)

class TaskDetail(db.Model):
    __tablename__ = 'task_details'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('transfer_tasks.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('bank_cards.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False, comment='转账金额')
    wechat_amount = db.Column(db.Float, default=0, comment='微信金额')
    alipay_amount = db.Column(db.Float, default=0, comment='支付宝金额')
    task_date = db.Column(db.Date, nullable=False, comment='任务日期')
    status = db.Column(db.String(20), default='pending', comment='状态 pending-待执行 completed-已完成 failed-失败')
    execute_time = db.Column(db.DateTime, comment='实际执行时间')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    person = db.relationship('Person', backref='task_details')
    card = db.relationship('BankCard', backref='task_details')