from flask import Blueprint, request, jsonify, session, send_file, current_app
from models import db, Tool, BorrowRecord, Attachment, Inspection, OperationLog, InStorageRecord, ScrapRequest
from routes.auth import login_required, admin_required, edit_required, add_log
from datetime import datetime
import calendar
import os
import uuid

tools_bp = Blueprint('tools', __name__)


def add_months(d, months):
    """加 N 个月，目标月无该日时对齐月末（避免 8/31 + 6 月溢出成 3/3）。"""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    return d.replace(year=y, month=m, day=min(d.day, last_day))


def calc_next_inspection(level, storage_date):
    """按等级与入库时间推算下次检定日期：A=半年，B=一年，C 级或无基准日不推算。"""
    if not storage_date or level not in ('A', 'B'):
        return None
    return add_months(storage_date, 6 if level == 'A' else 12)


@tools_bp.route('/', methods=['GET'])
@login_required
def list_tools():
    """获取工装列表，支持搜索筛选"""
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    factory = request.args.get('factory', '').strip()
    team = request.args.get('team', '').strip()
    exclude_status = request.args.get('exclude_status', '').strip()
    # 等级筛选：逗号分隔多值，如 levels=A,B（供「A/B类」视图复用本接口）
    levels = request.args.get('levels', '').strip()
    # 2026-11-04 修复：type=int 容错非数字（原裸 int() 传 page=abc 直接 500）；
    # per_page 钳制到 [1,100]，防一次拉全库。
    page = request.args.get('page', 1, type=int) or 1
    per_page = min(max(request.args.get('per_page', 20, type=int) or 20, 1), 100)

    query = Tool.query

    if keyword:
        query = query.filter(
            db.or_(
                Tool.code.contains(keyword),
                Tool.drawing_no.contains(keyword),
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
    if levels:
        lv = [x.strip() for x in levels.split(',') if x.strip()]
        if lv:
            query = query.filter(Tool.level.in_(lv))

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
    # 附带入库记录
    data['in_storage_records'] = [r.to_dict() for r in tool.in_storage_records]
    # 附带检定记录（含各自关联的附件）
    # 2026-11-02 修复：检定弹窗上传的附件挂在 inspection_id 上（tool_id 为空），
    # 此前详情接口不返回它们，详情页检定记录卡片永远看不到附件。
    insp_ids = [i.id for i in tool.inspections]
    insp_atts = {}
    if insp_ids:
        for a in Attachment.query.filter(Attachment.inspection_id.in_(insp_ids)).all():
            insp_atts.setdefault(a.inspection_id, []).append(a.to_dict())
    data['inspections'] = []
    for i in tool.inspections:
        d = i.to_dict()
        d['attachments'] = insp_atts.get(i.id, [])
        data['inspections'].append(d)
    # 附带附件列表
    data['attachments'] = [a.to_dict() for a in tool.attachments]
    return jsonify({'code': 200, 'data': data})


@tools_bp.route('/', methods=['POST'])
@edit_required
def create_tool():
    """新增工装（管理员）"""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'code': 400, 'msg': '编号和名称不能为空'})

    if Tool.query.filter_by(code=code).first():
        return jsonify({'code': 400, 'msg': '编号已存在'})

    universality = (data.get('universality') or '通用').strip()
    product_drawing_no = (data.get('product_drawing_no') or '').strip()
    if universality == '专用' and not product_drawing_no:
        return jsonify({'code': 400, 'msg': '通用性为「专用」时必须填写专用产品图号'})

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
        remark=data.get('remark', ''),
        universality=universality,
        product_drawing_no=product_drawing_no,
        created_by=data.get('created_by', '')
    )

    if data.get('purchase_date'):
        tool.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
    if data.get('storage_date'):
        tool.storage_date = datetime.strptime(data['storage_date'], '%Y-%m-%d').date()
    if data.get('next_inspection_date'):
        tool.next_inspection_date = datetime.strptime(data['next_inspection_date'], '%Y-%m-%d').date()

    # 兜底：A/B 级工装未指定下次检定日期时，按等级与入库时间自动推算
    if not tool.next_inspection_date:
        tool.next_inspection_date = calc_next_inspection(tool.level, tool.storage_date)

    db.session.add(tool)
    db.session.commit()

    add_log('新增工装', f'编号 {code}，名称 {name}')

    return jsonify({'code': 200, 'msg': '新增成功', 'data': tool.to_dict()})


@tools_bp.route('/inspection-reminders', methods=['GET'])
@login_required
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


@tools_bp.route('/summary', methods=['GET'])
@login_required
def tool_summary():
    """工装汇总：按图号聚合（2026-11-02）。一个图号可能对应多个工装编号；
    返回每图号的数量、名称/规格（取组内众数口径：第一条非空值）与状态分布。"""
    from collections import OrderedDict

    keyword = request.args.get('keyword', '').strip()
    factory = request.args.get('factory', '').strip()
    status = request.args.get('status', '').strip()
    include_scrapped = request.args.get('include_scrapped', type=int)  # 0/1，默认0（不合计报废）
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Tool.query
    if keyword:
        query = query.filter(
            db.or_(
                Tool.code.contains(keyword),
                Tool.drawing_no.contains(keyword),
                Tool.name.contains(keyword),
                Tool.spec.contains(keyword)
            )
        )
    if factory:
        query = query.filter(Tool.factory.contains(factory))
    if status:
        query = query.filter_by(status=status)
    elif not include_scrapped:
        query = query.filter(Tool.status != '报废')

    tools = query.order_by(Tool.id.asc()).all()

    # 内存聚合（数据量为数百条级，一次取全量即可，无需 GROUP BY 分页两跳）
    groups = OrderedDict()
    for t in tools:
        # 图号为空归到「无图号」组，避免散落成多行
        key = (t.drawing_no or '').strip() or '（无图号）'
        g = groups.setdefault(key, {
            'drawing_no': key, 'name': '', 'spec': '', 'category': '',
            'count': 0, 'in_stock': 0, 'borrowed': 0, 'repairing': 0, 'scrapped': 0,
        })
        g['count'] += 1
        if t.status in ('在库', '借出', '维修', '报废'):
            g[{'在库': 'in_stock', '借出': 'borrowed', '维修': 'repairing', '报废': 'scrapped'}[t.status]] += 1
        # 名称/规格/类别取组内第一条非空值
        if not g['name'] and t.name:
            g['name'] = t.name
        if not g['spec'] and (t.spec or '').strip():
            g['spec'] = t.spec
        if not g['category'] and (t.category or '').strip():
            g['category'] = t.category

    items_all = list(groups.values())
    total = len(items_all)
    start = (page - 1) * per_page
    items = items_all[start:start + per_page]

    return jsonify({
        'code': 200,
        'data': {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })


@tools_bp.route('/summary/detail', methods=['GET'])
@login_required
def tool_summary_detail():
    """工装汇总下钻（2026-11-02）：查某图号下全部工装编号及其当前借用信息。
    借用信息取每条工装最近一条借用记录（借用中则显示借用人/分厂/时间，已归还显示最近一次）。"""
    drawing_no = (request.args.get('drawing_no') or '').strip()
    if not drawing_no:
        return jsonify({'code': 400, 'msg': '请指定图号'})

    query = Tool.query
    if drawing_no == '（无图号）':
        # 汇总页把空图号归为「（无图号）」组，下钻时按空值查询
        query = query.filter(db.or_(Tool.drawing_no == '', Tool.drawing_no.is_(None)))
    else:
        query = query.filter(Tool.drawing_no == drawing_no)
    include_scrapped = request.args.get('include_scrapped', type=int)
    if not include_scrapped:
        query = query.filter(Tool.status != '报废')
    tools = query.order_by(Tool.code.asc()).all()

    # 2026-11-04 修复：原实现用 status.desc() 让「借用中」优先，但 Unicode 里
    # '已'(U+5DF2) > '借'(U+501F)，'已归还' 反而排在前面，借出中的工装会显示成已归还。
    # 改为一次取回本图号下全部借用记录，在 Python 里按「借用中优先、否则最近一条」挑选。
    tool_ids = [t.id for t in tools]
    borrows_by_tool = {}
    if tool_ids:
        for b in BorrowRecord.query.filter(
                BorrowRecord.tool_id.in_(tool_ids)).order_by(BorrowRecord.id.desc()).all():
            borrows_by_tool.setdefault(b.tool_id, []).append(b)

    items = []
    for t in tools:
        d = t.to_dict()
        recs = borrows_by_tool.get(t.id, [])
        last_borrow = next((b for b in recs if b.status == '借用中'), None) or (recs[0] if recs else None)
        if last_borrow:
            d['last_borrow'] = {
                'borrower': last_borrow.borrower,
                'factory': last_borrow.factory or '',
                'team': last_borrow.team or '',
                'receiver': last_borrow.receiver or '',
                'borrow_time': last_borrow.borrow_time.strftime('%Y-%m-%d %H:%M') if last_borrow.borrow_time else '',
                'status': last_borrow.status,
            }
        else:
            d['last_borrow'] = None
        items.append(d)

    return jsonify({'code': 200, 'data': {'drawing_no': drawing_no, 'items': items}})


@tools_bp.route('/<int:tool_id>', methods=['PUT'])
@edit_required
def update_tool(tool_id):
    """更新工装（admin/employee可编辑）"""
    tool = Tool.query.get_or_404(tool_id)
    data = request.get_json() or {}

    # 通用性校验前置（在任何字段赋值之前），避免改了一半再回滚。
    # 取「本次传入值，否则沿用库中现值」作为生效值。
    eff_universality = (data.get('universality', tool.universality) or '通用').strip()
    eff_product_drawing_no = (data.get('product_drawing_no', tool.product_drawing_no) or '').strip()
    if eff_universality == '专用' and not eff_product_drawing_no:
        return jsonify({'code': 400, 'msg': '通用性为「专用」时必须填写专用产品图号'})

    old_level = tool.level
    old_storage_date = tool.storage_date

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
    if 'universality' in data:
        tool.universality = (data['universality'] or '通用').strip()
    if 'product_drawing_no' in data:
        tool.product_drawing_no = (data['product_drawing_no'] or '').strip()
    if 'purchase_date' in data and data['purchase_date']:
        tool.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
    elif 'purchase_date' in data and not data['purchase_date']:
        tool.purchase_date = None
    if 'next_inspection_date' in data and data['next_inspection_date']:
        tool.next_inspection_date = datetime.strptime(data['next_inspection_date'], '%Y-%m-%d').date()
    if 'storage_date' in data and data['storage_date']:
        tool.storage_date = datetime.strptime(data['storage_date'], '%Y-%m-%d').date()
    elif 'storage_date' in data and not data['storage_date']:
        tool.storage_date = None

    # 下次检定兜底（2026-11-05 修复）：详情页编辑表单会把空的「下次检定」原样提交，
    # 原实现遇到空值直接置 None 并跳过重算，导致 B 类填了入库日期仍显示「-」。
    # 现在：显式传值以其为准；未传/传空时，未被检定记录覆盖过的工装按等级+入库日期重算
    #（A=半年、B=1 年、C 级不推算）；有检定记录的仅在显式清空时置空。
    if not data.get('next_inspection_date'):
        has_inspection = Inspection.query.filter_by(tool_id=tool_id).count() > 0
        changed = (tool.level != old_level) or (tool.storage_date != old_storage_date)
        if not has_inspection and (changed or not tool.next_inspection_date):
            tool.next_inspection_date = calc_next_inspection(tool.level, tool.storage_date)
        elif 'next_inspection_date' in data:
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


def cleanup_tool_resources(tool):
    """删除工装及其全部关联资源（2026-11-04 统一，供两条删除路径共用）。

    原实现在 routes/tools.py 与 routes/scraps.py 各写一份，且 tools.py 那份
    只删附件文件、不删 attachments 表记录；SQLite 外键默认关闭不会报错，
    于是留下 tool_id 指向已删工装的孤儿记录。
    """
    for rec in tool.in_storage_records:
        db.session.delete(rec)
    for br in tool.borrow_records:
        db.session.delete(br)
    for req in ScrapRequest.query.filter_by(tool_id=tool.id).all():
        db.session.delete(req)

    for att in tool.attachments:
        try:
            if os.path.exists(att.file_path):
                os.remove(att.file_path)
        except OSError:
            pass
        db.session.delete(att)

    if tool.photo_path:
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], tool.photo_path)
        try:
            if os.path.exists(photo_path):
                os.remove(photo_path)
            photo_dir = os.path.dirname(photo_path)
            if os.path.exists(photo_dir) and not os.listdir(photo_dir):
                os.rmdir(photo_dir)
        except OSError:
            pass

    db.session.delete(tool)


@tools_bp.route('/<int:tool_id>', methods=['DELETE'])
@admin_required
def delete_tool(tool_id):
    """删除工装（管理员）"""
    tool = Tool.query.get_or_404(tool_id)

    active_borrow = BorrowRecord.query.filter_by(
        tool_id=tool_id, status='借用中'
    ).first()
    if active_borrow:
        return jsonify({'code': 400, 'msg': '该工装有未归还的借用记录，不能删除'})

    inspection = Inspection.query.filter_by(tool_id=tool_id).first()
    if inspection:
        return jsonify({'code': 400, 'msg': '该工装有检定记录，请先删除检定记录后再删除工装'})

    add_log('删除工装', f'编号 {tool.code}，名称 {tool.name}')
    cleanup_tool_resources(tool)
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
    from datetime import timedelta, date
    from sqlalchemy import func

    today = datetime.now()
    base_month = today.replace(day=1)

    def add_months(d, delta):
        """返回 d 偏移 delta 个月后的 1 号（正确处理跨年/闰年）"""
        total = (d.year * 12 + (d.month - 1)) + delta
        y, m = divmod(total, 12)
        return date(y, m + 1, 1)

    # 生成过去12个月（含本月）的真实自然月边界（原实现用 timedelta(days=i*30) 会错位月份）
    months = []
    for i in range(11, -1, -1):
        first_day = add_months(base_month, -i)
        if first_day.month == 12:
            last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = first_day.replace(month=first_day.month + 1, day=1) - timedelta(days=1)
        months.append({
            'label': first_day.strftime('%Y年%m月'),
            'year_month': first_day.strftime('%Y-%m'),
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
            Inspection.inspect_date >= m['start'],
            Inspection.inspect_date <= m['end']
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
    
    # 查询借出（出库）数量（按月份，基于 BorrowRecord 的 borrow_time）
    borrows = {}
    for m in months:
        count = BorrowRecord.query.filter(
            BorrowRecord.borrow_time >= m['start'],
            BorrowRecord.borrow_time < m['end'] + timedelta(days=1)
        ).count()
        borrows[m['year_month']] = count

    # 组装返回数据
    labels = [m['label'] for m in months]
    new_data = [new_tools.get(m['year_month'], 0) for m in months]
    inspection_data = [inspections.get(m['year_month'], 0) for m in months]
    scrap_data = [scraps.get(m['year_month'], 0) for m in months]
    borrow_data = [borrows.get(m['year_month'], 0) for m in months]

    # 计算累计工装数量（2026-11-04 修复）：
    # 原实现从 0 起只累计窗口内 12 个月的新增，前端标为「总数」——库里 459 件
    # 却只显示窗口增量，口径错。正确做法：以「窗口起点之前的历史存量」为基数累计。
    window_start = months[0]['start']
    running_total = Tool.query.filter(Tool.created_at < window_start).count()
    cumulative = []
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
            'borrows': borrow_data,
            'cumulative': cumulative
        }
    })


@tools_bp.route('/stats/recent', methods=['GET'])
@login_required
def recent_activities():
    """首页近期动态 - 合并最近借用/归还/新增工装事件，按时间倒序"""
    limit = min(request.args.get('limit', 6, type=int), 20)
    events = []

    # 借用事件
    for b in BorrowRecord.query.order_by(BorrowRecord.borrow_time.desc()).limit(8).all():
        events.append({
            'full_time': b.borrow_time.strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'borrow',
            'tool_id': b.tool_id,
            'text': f"{b.borrower} 借出 {b.tool.name if b.tool else ''}"
        })

    # 归还事件
    for b in BorrowRecord.query.filter(BorrowRecord.return_time != None).order_by(BorrowRecord.return_time.desc()).limit(8).all():
        events.append({
            'full_time': b.return_time.strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'return',
            'tool_id': b.tool_id,
            'text': f"{b.return_operator or b.borrower} 归还 {b.tool.name if b.tool else ''}"
        })

    # 新增工装事件
    for t in Tool.query.order_by(Tool.created_at.desc()).limit(8).all():
        events.append({
            'full_time': t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'create',
            'tool_id': t.id,
            'text': f"新增工装 {t.name}"
        })

    # 按时间倒序合并，取前 limit 条；显示时间格式 MM-DD HH:MM
    events.sort(key=lambda e: e['full_time'], reverse=True)
    for e in events[:limit]:
        e['time'] = e['full_time'][5:16]

    return jsonify({'code': 200, 'data': {'items': events[:limit]}})
