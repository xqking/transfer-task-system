from app import create_app
from models import Person

app = create_app()
with app.app_context():
    persons = Person.query.filter_by(status=1).all()
    print("可用人员列表:")
    for p in persons:
        print(f"{p.code} - {p.name}: 单次最小={p.single_min}, 单次最大={p.single_max}")
