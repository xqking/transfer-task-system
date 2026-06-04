from app import create_app
from extensions import db
from models import Bank

def init_db():
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
        if not Bank.query.first():
            banks = [
                Bank(name='建设银行', code='CCB', status=1),
                Bank(name='工商银行', code='ICBC', status=1)
            ]
            db.session.add_all(banks)
            db.session.commit()
            print('✅ 初始化银行数据成功')
        
        print('✅ 数据库表创建成功')

if __name__ == '__main__':
    init_db()