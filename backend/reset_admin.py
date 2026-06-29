import sys
sys.path.insert(0, r'D:\tooling-management\backend')
from app import app
from models import db, User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # 创建 admin
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        print('✅ 创建 admin 用户')
    else:
        admin.set_password('admin123')
        print('✅ 重置 admin 密码为 admin123')
    db.session.commit()
    print('所有用户:')
    for u in User.query.all():
        print(f'  {u.username} ({u.role})')
