from flask import Blueprint, jsonify

org_bp = Blueprint('org', __name__)

# 组织架构定义
ORG_STRUCTURE = {
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


@org_bp.route('/structure', methods=['GET'])
def get_structure():
    """获取组织架构（分厂+班组树）"""
    return jsonify({
        'code': 200,
        'data': ORG_STRUCTURE
    })


@org_bp.route('/factories', methods=['GET'])
def get_factories():
    """获取分厂列表"""
    factories = [f['name'] for f in ORG_STRUCTURE['factories']]
    return jsonify({
        'code': 200,
        'data': factories
    })


@org_bp.route('/teams', methods=['GET'])
def get_teams():
    """获取指定分厂的班组列表"""
    from flask import request
    factory = request.args.get('factory', '').strip()
    for f in ORG_STRUCTURE['factories']:
        if f['name'] == factory:
            return jsonify({
                'code': 200,
                'data': f['teams']
            })
    return jsonify({
        'code': 200,
        'data': []
    })
