from app import create_app
from extensions import db
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('bank_cards')]
    
    if 'receive_code' not in columns:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE bank_cards ADD COLUMN receive_code VARCHAR(100)"))
        print('已添加 receive_code 字段')
    else:
        print('receive_code 字段已存在')
