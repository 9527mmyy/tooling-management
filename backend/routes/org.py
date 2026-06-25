"""
组织架构路由
支持从数据库读取分厂和班组配置
"""
from flask import Blueprint, jsonify, request, current_app
from models import db, SystemConfig

org_bp = Blueprint('org', __name__)

# 默认组织架构（首次无数据时使用）
DEFAULT_ORG = {
    'factories': [
        {
            'name': '新能源分厂',
            'teams': ['配套班组', '润滑班组', '风冷班组', '储能班组', '试车班组', '布线班组']
        },
        {
            'name': '液冷分厂',
            'teams': ['管焊班组', '装配班组', '试车班组']
        },
        {
            'name': '工业分厂',
            'teams': []
        },
        {
            'name': '配套分厂',
            'teams': []
        },
        {
            'name': '其他',
            'teams': []
        }
    ]
}


def _load_org_from_db():
    """从数据库加载组织架构"""
    try:
        factories = SystemConfig.query.filter_by(config_key='factory').order_by(SystemConfig.sort_order, SystemConfig.id).all()
        teams = SystemConfig.query.filter_by(config_key='team').order_by(SystemConfig.sort_order, SystemConfig.id).all()
        
        if not factories and not teams:
            return None  # 返回None表示无数据，使用默认
        
        # 按分厂分组班组
        factory_teams = {}
        for t in teams:
            # 班组格式: "分厂名/班组名" 或纯班组名
            if '/' in t.config_value:
                parts = t.config_value.split('/', 1)
                factory_name = parts[0]
                team_name = parts[1]
            else:
                # 没有分厂前缀的班组：分配给"默认分厂"或第一个分厂
                team_name = t.config_value
                factory_name = '_default_'  # 标记为默认分组
            
            if factory_name not in factory_teams:
                factory_teams[factory_name] = []
            if team_name:
                factory_teams[factory_name].append(team_name)
        
        # 构建组织结构
        result = {'factories': []}
        for f in factories:
            teams_for_factory = factory_teams.get(f.config_value, factory_teams.get('_default_', []))
            factory_obj = {
                'name': f.config_value,
                'teams': teams_for_factory
            }
            result['factories'].append(factory_obj)
        
        # 如果有班组使用默认分组但没有分厂，创建"其他"分厂
        if '_default_' in factory_teams and not factories:
            result['factories'].append({
                'name': '其他',
                'teams': factory_teams['_default_']
            })
        
        # 如果有班组没有对应的分厂，自动创建
        all_teams = set()
        for t in teams:
            if '/' in t.config_value:
                all_teams.add(t.config_value.split('/', 1)[1])
        
        return result
    except Exception as e:
        print(f"加载组织架构失败: {e}")
        return None


@org_bp.route('/structure', methods=['GET'])
def get_structure():
    """获取组织架构（分厂+班组树）"""
    # 尝试从数据库加载
    org_data = _load_org_from_db()
    if org_data:
        return jsonify({
            'code': 200,
            'data': org_data
        })
    
    # 检查数据库是否有配置但格式不兼容
    db_factories = SystemConfig.query.filter_by(config_key='factory').count()
    if db_factories > 0:
        # 有数据但可能格式不对，仍返回
        org_data = _load_org_from_db()
        if org_data:
            return jsonify({
                'code': 200,
                'data': org_data
            })
    
    # 无数据或加载失败，使用默认
    return jsonify({
        'code': 200,
        'data': DEFAULT_ORG
    })


@org_bp.route('/factories', methods=['GET'])
def get_factories():
    """获取分厂列表"""
    # 尝试从数据库加载
    factories = SystemConfig.query.filter_by(config_key='factory').order_by(SystemConfig.sort_order, SystemConfig.id).all()
    
    if factories:
        return jsonify({
            'code': 200,
            'data': [{'name': f.config_value} for f in factories]
        })
    
    # 使用默认
    return jsonify({
        'code': 200,
        'data': [{'name': f['name']} for f in DEFAULT_ORG['factories']]
    })


@org_bp.route('/teams', methods=['GET'])
def get_teams():
    """获取所有班组或指定分厂的班组"""
    factory = request.args.get('factory', '').strip()
    
    # 从数据库加载
    all_teams = SystemConfig.query.filter_by(config_key='team').order_by(SystemConfig.sort_order, SystemConfig.id).all()
    
    if all_teams:
        if factory:
            # 返回指定分厂的班组
            result = []
            for t in all_teams:
                if '/' in t.config_value:
                    parts = t.config_value.split('/', 1)
                    if parts[0] == factory:
                        result.append(parts[1])
                elif factory == t.config_value:
                    result.append(t.config_value)
            return jsonify({
                'code': 200,
                'data': list(set(result))
            })
        else:
            # 返回所有班组（去重）
            all_team_names = []
            for t in all_teams:
                if '/' in t.config_value:
                    all_team_names.append(t.config_value.split('/', 1)[1])
                else:
                    all_team_names.append(t.config_value)
            return jsonify({
                'code': 200,
                'data': list(set(all_team_names))
            })
    
    # 使用默认
    if factory:
        for f in DEFAULT_ORG['factories']:
            if f['name'] == factory:
                return jsonify({
                    'code': 200,
                    'data': f['teams']
                })
        return jsonify({
            'code': 200,
            'data': []
        })
    
    # 返回所有班组
    all_default_teams = []
    for f in DEFAULT_ORG['factories']:
        all_default_teams.extend(f['teams'])
    return jsonify({
        'code': 200,
        'data': list(set(all_default_teams))
    })
