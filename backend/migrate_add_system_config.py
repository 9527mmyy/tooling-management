"""
迁移脚本：初始化分厂-班组层级数据
"""
from app import app, db
from models import SystemConfig

with app.app_context():
    # 清空现有数据
    SystemConfig.query.delete()
    db.session.commit()
    
    # 初始化分厂
    factories = [
        ('factory', '液冷分厂'),
        ('factory', '新能源分厂'),
    ]
    
    # 初始化班组（格式：分厂名/班组名）
    teams = [
        # 液冷分厂
        ('team', '液冷分厂/装配班组'),
        ('team', '液冷分厂/布线班组'),
        ('team', '液冷分厂/测试班组'),
        ('team', '液冷分厂/管焊班组'),
        # 新能源分厂
        ('team', '新能源分厂/风冷班组'),
        ('team', '新能源分厂/布线班组'),
        ('team', '新能源分厂/测试班组'),
        ('team', '新能源分厂/润滑班组'),
        ('team', '新能源分厂/储能班组'),
        # 通用班组
        ('team', '液冷分厂/配套班组'),
        ('team', '新能源分厂/配套班组'),
    ]
    
    # 初始化类别
    categories = [
        ('category', '焊接类'),
        ('category', '装配类'),
        ('category', '测试类'),
        ('category', '机加类'),
        ('category', '检测类'),
        ('category', '其他类'),
    ]
    
    for key, value in factories + teams + categories:
        config = SystemConfig(config_key=key, config_value=value)
        db.session.add(config)
    
    db.session.commit()
    print("分厂-班组层级数据初始化成功！")
    print(f"分厂数: {len(factories)}")
    print(f"班组数: {len(teams)}")
    print(f"类别数: {len(categories)}")
