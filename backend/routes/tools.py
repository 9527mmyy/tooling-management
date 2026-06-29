from flask import Blueprint, request, jsonify, session, send_file, current_app
from models import db, Tool, BorrowRecord, Attachment, Inspection, OperationLog
from routes.auth import login_required, admin_required, edit_required, add_log
from datetime import datetime
import os
import uuid

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/', methods=['GET'])
@login_required
def list_tools():
    """获取工装列表，支持搜索筛选"""
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    factory = request.args.get('factory', '').strip()
    team = request.args.get('team', '').strip()
    exclude_status = request.args.get('exclude_status', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    query = Tool.query

    if keyword:
        query = query.filter(
            db.or_(
                Tool.code.contains(keyword),
                Tool.name.contains(keyword),
                Tool.spec.contains(keyword)
            )
        )
    if status:
        query = query.filter_by(status=status)
    if factory:
        query = query.filter(Tool.factory.contains(factory))
    if team:
        query = query.filter(Tool.team.contains(team))
    if exclude_status:
        # 排除指定状态（如'报废'）
        query = query.filter(Tool.status != exclude_status)

    pagination = query.order_by(Tool.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'data': {
            'items': [t.to_dict() for t in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    })


@tools_bp.route('/<int:tool_id>', methods=['GET'])
@login_required
def get_tool(tool_id):
    """获取工装详情"""
    tool = Tool.query.get_or_404(tool_id)
    data = tool.to_dict()
    # 附带借用记录
    data['borrow_records'] = [r.to_dict() for r in tool.borrow_records]
    # 附带检定记录
    data['inspections'] = [i.to_dict() for i in tool.inspections]
    # 附带附件列表
    data['attachments'] = [a.to_dict() for a in tool.attachments]
    return jsonify({'code': 200, 'data': data})


@tools_bp.route('/', methods=['POST'])
@edit_required
def create_tool():
    """新增工装（管理员）"""
    data = request.get_json()
    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'code': 400, 'msg': '编号和名称不能为空'})

    if Tool.query.filter_by(code=code).first():
        return jsonify({'code': 400, 'msg': '编号已存在'})

    tool = Tool(
        code=code,
        drawing_no=data.get('drawing_no', ''),
        name=name,
        spec=data.get('spec', ''),
        category=data.get('category', ''),
        level=data.get('level', 'A'),
        factory=data.get('factory', ''),
        team=data.get('team', ''),
        receiver=data.get('receiver', ''),
        status=data.get('status', '在库'),
        remark=data.get('remark', '')
    )

    if data.get('purchase_date'):
        tool.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
    if data.get('next_inspection_date'):
        tool.next_inspection_date = datetime.strptime(data['next_inspection_date'], '%Y-%m-%d').date()

    db.session.add(tool)
    db.session.commit()

    add_log('新增工装', f'编号 {code}，名称 {name}')

    return jsonify({'code': 200, 'msg': '新增成功', 'data': tool.to_dict()})


@tools_bp.route('/inspection-reminders', methods=['GET'])
def get_inspection_reminders():
    """获取检定提醒列表"""
    filter_type = request.args.get('filter', 'overdue')  # overdue, 30, 60, all
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    today = datetime.now().date()
    from datetime import timedelta
    
    # 构建查询（排除已报废的工装）
    query = Tool.query.filter(
        Tool.next_inspection_date != None,
        Tool.status != '报废'
    )
    
    if filter_type == 'overdue':
        # 已逾期
        query = query.filter(Tool.next_inspection_date < today)
    elif filter_type == '30':
        # 30天内到期
        query = query.filter(
            Tool.next_inspection_date >= today,
            Tool.next_inspection_date <= today + timedelta(days=30)
        )
    elif filter_type == '60':
        # 60天内到期
        query = query.filter(
            Tool.next_inspection_date >= today,
            Tool.next_inspection_date <= today + timedelta(days=60)
        )
    elif filter_type == 'all':
        # 全部（有检定日期的）
        pass
    
    # 分页
    total = query.count()
    tools = query.order_by(Tool.next_inspection_date.asc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    # 计算剩余天数
    result = []
    for tool in tools.items:
        tool_dict = tool.to_dict()
        next_date = tool.next_inspection_date
        if next_date:
            days_until = (next_date - today).days
            tool_dict['days_until_inspection'] = days_until
        else:
            tool_dict['days_until_inspection'] = None
        result.append(tool_dict)
    
    return jsonify({
        'code': 200,
        'data': {
            'items': result,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@tools_bp.route('/<int:tool_id>', methods=['PUT'])
@edit_required
def update_tool(tool_id):
    """更新工装（admin/employee可编辑）"""
    tool = Tool.query.get_or_404(tool_id)
    data = request.get_json()

    if 'code' in data:
        new_code = data['code'].strip()
        if new_code != tool.code and Tool.query.filter_by(code=new_code).first():
            return jsonify({'code': 400, 'msg': '编号已存在'})
        tool.code = new_code
    if 'name' in data:
        tool.name = data['name'].strip()
    if 'drawing_no' in data:
        tool.drawing_no = data['drawing_no'] or ''
    if 'spec' in data:
        tool.spec = data['spec'] or ''
    if 'category' in data:
        tool.category = data['category'] or ''
    if 'level' in data:
        tool.level = data['level'] or 'A'
    if 'factory' in data:
        tool.factory = data['factory'] or None
    if 'team' in data:
        tool.team = data['team'] or None
    if 'receiver' in data:
        tool.receiver = data['receiver'] or None
    if 'status' in data:
        tool.status = data['status']
    if 'remark' in data:
        tool.remark = data['remark'] or ''
    if 'purchase_date' in data and data['purchase_date']:
        tool.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
    elif 'purchase_date' in data and not data['purchase_date']:
        tool.purchase_date = None
    if 'next_inspection_date' in data and data['next_inspection_date']:
        tool.next_inspection_date = datetime.strptime(data['next_inspection_date'], '%Y-%m-%d').date()
    elif 'next_inspection_date' in data and not data['next_inspection_date']:
        tool.next_inspection_date = None

    db.session.commit()

    add_log('更新工装', f'编号 {tool.code}，名称 {tool.name}')

    return jsonify({'code': 200, 'msg': '更新成功', 'data': tool.to_dict()})


@tools_bp.route('/<int:tool_id>/photo', methods=['POST'])
@edit_required
def upload_photo(tool_id):
    """上传工装照片"""
    tool = Tool.query.get_or_404(tool_id)

    if 'photo' not in request.files:
        return jsonify({'code': 400, 'msg': '请选择照片'})

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '请选择照片'})

    # 校验文件类型
    allowed = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        return jsonify({'code': 400, 'msg': '仅支持 jpg/png/gif/webp 格式'})

    # 目录：uploads/photos/{tool_code}/
    base_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'photos', tool.code)
    os.makedirs(base_dir, exist_ok=True)

    # 删除旧照片（如果有）
    if tool.photo_path:
        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], tool.photo_path)
        if os.path.exists(old_path):
            os.remove(old_path)

    # 保存新照片，固定名为 photo{ext}
    unique_name = f'photo{ext}'
    file_path = os.path.join(base_dir, unique_name)
    file.save(file_path)

    # 更新 photo_path（相对路径：photos/{code}/photo{ext}）
    rel_path = f'photos/{tool.code}/{unique_name}'
    tool.photo_path = rel_path
    db.session.commit()

    add_log('上传照片', f'工装 {tool.code} {tool.name}')

    return jsonify({'code': 200, 'msg': '照片上传成功', 'data': {'photo_path': rel_path}})


@tools_bp.route('/<int:tool_id>/photo-delete', methods=['POST'])
@edit_required
def delete_photo(tool_id):
    """删除工装照片"""
    tool = Tool.query.get_or_404(tool_id)

    if not tool.photo_path:
        return jsonify({'code': 400, 'msg': '暂无照片'})

    abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], tool.photo_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)

    tool.photo_path = None
    db.session.commit()

    add_log('删除照片', f'工装 {tool.code} {tool.name}')

    return jsonify({'code': 200, 'msg': '照片已删除'})


@tools_bp.route('/<int:tool_id>/photo', methods=['GET'])
@login_required
def get_photo(tool_id):
    """获取工装照片"""
    tool = Tool.query.get_or_404(tool_id)

    if not tool.photo_path:
        return jsonify({'code': 404, 'msg': '暂无照片'})

    abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], tool.photo_path)
    if not os.path.exists(abs_path):
        # 路径记录与文件不一致，清理
        tool.photo_path = None
        db.session.commit()
        return jsonify({'code': 404, 'msg': '照片文件不存在'})

    return send_file(abs_path)


@tools_bp.route('/<int:tool_id>', methods=['DELETE'])
@admin_required
def delete_tool(tool_id):
    """删除工装（管理员）"""
    tool = Tool.query.get_or_404(tool_id)

    # 检查是否有未归还的借用
    active_borrow = BorrowRecord.query.filter_by(
        tool_id=tool_id, status='借用中'
    ).first()
    if active_borrow:
        return jsonify({'code': 400, 'msg': '该工装有未归还的借用记录，不能删除'})

    # 检查是否有检定记录
    inspection = Inspection.query.filter_by(tool_id=tool_id).first()
    if inspection:
        return jsonify({'code': 400, 'msg': '该工装有检定记录，请先删除检定记录后再删除工装'})

    add_log('删除工装', f'编号 {tool.code}，名称 {tool.name}')

    # 删除关联附件文件
    for att in tool.attachments:
        if os.path.exists(att.file_path):
            os.remove(att.file_path)

    # 删除照片文件
    if tool.photo_path:
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], tool.photo_path)
        if os.path.exists(photo_path):
            os.remove(photo_path)
        # 删除照片目录（如果为空）
        photo_dir = os.path.dirname(photo_path)
        if os.path.exists(photo_dir) and not os.listdir(photo_dir):
            os.rmdir(photo_dir)

    db.session.delete(tool)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '删除成功'})


@tools_bp.route('/stats', methods=['GET'])
@login_required
def tool_stats():
    """工装统计"""
    total = Tool.query.count()
    in_stock = Tool.query.filter_by(status='在库').count()
    borrowed = Tool.query.filter_by(status='借出').count()
    repairing = Tool.query.filter_by(status='维修').count()
    scrapped = Tool.query.filter_by(status='报废').count()

    # 即将到期检定（30天内）
    today = datetime.now().date()
    from datetime import timedelta
    due_soon = Tool.query.filter(
        Tool.next_inspection_date != None,
        Tool.next_inspection_date <= today + timedelta(days=30),
        Tool.next_inspection_date >= today
    ).count()

    overdue = Tool.query.filter(
        Tool.next_inspection_date != None,
        Tool.next_inspection_date < today
    ).count()

    return jsonify({
        'code': 200,
        'data': {
            'total': total,
            'in_stock': in_stock,
            'borrowed': borrowed,
            'repairing': repairing,
            'scrapped': scrapped,
            'due_soon': due_soon,
            'overdue': overdue
        }
    })


@tools_bp.route('/stats/monthly', methods=['GET'])
@login_required
def tool_stats_monthly():
    """月度统计 - 过去12个月的新增、鉴定、报废趋势"""
    from datetime import timedelta
    from sqlalchemy import func
    
    today = datetime.now()
    
    # 生成过去12个月的日期范围
    months = []
    for i in range(11, -1, -1):
        # 计算第i个月的第一天和最后一天
        target_month = today.replace(day=1) - timedelta(days=i * 30)
        first_day = target_month.replace(day=1)
        if target_month.month == 12:
            last_day = target_month.replace(year=target_month.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1)
        months.append({
            'label': target_month.strftime('%Y年%m月'),
            'year_month': target_month.strftime('%Y-%m'),
            'start': first_day,
            'end': last_day
        })
    
    # 查询新增工装数量（按月份）
    new_tools = {}
    for m in months:
        count = Tool.query.filter(
            Tool.created_at >= m['start'],
            Tool.created_at < m['end'] + timedelta(days=1)
        ).count()
        new_tools[m['year_month']] = count
    
    # 查询检定记录数量（按月份）
    inspections = {}
    for m in months:
        count = Inspection.query.filter(
            Inspection.inspect_date >= m['start'].date(),
            Inspection.inspect_date <= m['end'].date()
        ).count()
        inspections[m['year_month']] = count
    
    # 查询报废工装数量（按月份，基于scrap_requests已批准的）
    from models import ScrapRequest
    scraps = {}
    for m in months:
        count = ScrapRequest.query.filter(
            ScrapRequest.status == '已批准',
            ScrapRequest.reviewed_at >= m['start'],
            ScrapRequest.reviewed_at < m['end'] + timedelta(days=1)
        ).count()
        scraps[m['year_month']] = count
    
    # 组装返回数据
    labels = [m['label'] for m in months]
    new_data = [new_tools.get(m['year_month'], 0) for m in months]
    inspection_data = [inspections.get(m['year_month'], 0) for m in months]
    scrap_data = [scraps.get(m['year_month'], 0) for m in months]
    
    # 计算累计工装数量
    cumulative = []
    running_total = 0
    # 从最早月份开始累计
    for m in months:
        running_total += new_tools.get(m['year_month'], 0)
        cumulative.append(running_total)
    
    return jsonify({
        'code': 200,
        'data': {
            'labels': labels,
            'new_tools': new_data,
            'inspections': inspection_data,
            'scraps': scrap_data,
            'cumulative': cumulative
        }
    })
