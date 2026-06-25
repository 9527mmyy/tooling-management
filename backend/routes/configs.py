"""
系统配置路由
支持对类别、分厂、班组等字段的可配置管理
"""
from flask import Blueprint, request, jsonify
from models import db, SystemConfig
from routes.auth import admin_required

configs_bp = Blueprint('configs', __name__)


@configs_bp.route('/', methods=['GET'])
def get_configs():
    """获取所有配置，按key分组"""
    configs = SystemConfig.query.order_by(SystemConfig.config_key, SystemConfig.sort_order, SystemConfig.id).all()
    
    # 按key分组
    result = {}
    for config in configs:
        if config.config_key not in result:
            result[config.config_key] = []
        result[config.config_key].append(config.to_dict())
    
    return jsonify({'success': True, 'data': result})


@configs_bp.route('/<key>', methods=['GET'])
def get_config_by_key(key):
    """获取指定key的所有配置值"""
    configs = SystemConfig.query.filter_by(config_key=key).order_by(SystemConfig.sort_order, SystemConfig.id).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in configs]
    })


@configs_bp.route('/', methods=['POST'])
@admin_required
def add_config():
    """新增配置项"""
    data = request.get_json()
    
    if not data or not data.get('config_key') or not data.get('config_value'):
        return jsonify({'success': False, 'message': '缺少必填字段'}), 400
    
    # 检查是否已存在
    existing = SystemConfig.query.filter_by(
        config_key=data['config_key'],
        config_value=data['config_value']
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': '配置项已存在'}), 400
    
    config = SystemConfig(
        config_key=data['config_key'],
        config_value=data['config_value'],
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(config)
    db.session.commit()
    
    return jsonify({'success': True, 'data': config.to_dict()})


@configs_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def update_config(id):
    """更新配置项"""
    config = SystemConfig.query.get_or_404(id)
    data = request.get_json()
    
    if data.get('config_value'):
        # 检查是否与其他冲突
        existing = SystemConfig.query.filter(
            SystemConfig.id != id,
            SystemConfig.config_key == config.config_key,
            SystemConfig.config_value == data['config_value']
        ).first()
        if existing:
            return jsonify({'success': False, 'message': '配置值已存在'}), 400
        config.config_value = data['config_value']
    
    if 'sort_order' in data:
        config.sort_order = data['sort_order']
    
    db.session.commit()
    return jsonify({'success': True, 'data': config.to_dict()})


@configs_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_config(id):
    """删除配置项"""
    config = SystemConfig.query.get_or_404(id)
    db.session.delete(config)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'})
