import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions import db
from models import TransferTask, TaskDetail
from datetime import date

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

def delete_tasks_by_date(target_date):
    with app.app_context():
        # 查找所有指定日期的任务详情
        details = TaskDetail.query.filter(TaskDetail.task_date == target_date).all()
        
        if not details:
            print(f"未找到 {target_date} 的任务记录")
            return 0
        
        # 获取相关的任务ID
        task_ids = set()
        for detail in details:
            task_ids.add(detail.task_id)
        
        print(f"找到 {len(task_ids)} 个任务，共 {len(details)} 条子任务")
        
        # 删除任务详情
        deleted_details = TaskDetail.query.filter(TaskDetail.task_date == target_date).delete()
        
        # 删除任务
        deleted_tasks = 0
        for task_id in task_ids:
            task = TransferTask.query.get(task_id)
            if task:
                db.session.delete(task)
                deleted_tasks += 1
        
        db.session.commit()
        
        print(f"成功删除 {deleted_tasks} 个任务和 {deleted_details} 条子任务")
        return deleted_tasks

if __name__ == '__main__':
    target_date = date(2026, 5, 23)
    delete_tasks_by_date(target_date)