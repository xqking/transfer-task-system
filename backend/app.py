from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from extensions import db
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app)
    db.init_app(app)
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    from routes.person import person_bp
    from routes.customer import customer_bp
    from routes.bankcard import bankcard_bp
    from routes.transfer_task import transfer_task_bp
    from routes.task_detail import task_detail_bp
    
    app.register_blueprint(person_bp, url_prefix='/api/person')
    app.register_blueprint(customer_bp, url_prefix='/api/customer')
    app.register_blueprint(bankcard_bp, url_prefix='/api/bankcard')
    app.register_blueprint(transfer_task_bp, url_prefix='/api/task')
    app.register_blueprint(task_detail_bp, url_prefix='/api/task-detail')
    
    # 上传文件服务
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    with app.app_context():
        db.create_all()
        migrate_db()
    
    return app

def migrate_db():
    from sqlalchemy import inspect, text
    from models import Customer
    from routes.customer import CUSTOMER_COLORS

    inspector = inspect(db.engine)
    if 'customers' not in inspector.get_table_names():
        return

    columns = [c['name'] for c in inspector.get_columns('customers')]
    if 'color' not in columns:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE customers ADD COLUMN color VARCHAR(20)"))

    customers = Customer.query.filter_by(status=1).order_by(Customer.id).all()
    for index, customer in enumerate(customers):
        if not customer.color:
            customer.color = CUSTOMER_COLORS[index % len(CUSTOMER_COLORS)]
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)