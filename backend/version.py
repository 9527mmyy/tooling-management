# -*- coding: utf-8 -*-
"""
系统版本与出品信息 —— 全站唯一真相源。

版本方案：语义化版本，格式 主版本.次版本。
    · 主版本：架构级重构、数据结构不兼容变更时 +1（如 1.0 → 2.0）
    · 次版本：新增功能、界面改版时 +1（如 1.0 → 1.1）
    · 仅修 BUG 时不动版本号，只更新 BUILD_DATE

发布清单（两处都要改）：
    1. VERSION     —— 有功能变更时才改
    2. BUILD_DATE  —— 每次发布都改，用于区分同版本号的不同构建

前端通过 GET /api/system/about 读取，模板里不硬编码任何版本号。
"""

# ---- 版本 ----
VERSION = '2.2'               # 语义化版本 主.次
BUILD_DATE = '2026-11-04'     # 发布日期 YYYY-MM-DD，每次发布必改

# ---- 版本历史（新版本追加在最前）----
CHANGELOG = [
    ('2.2', '2026-11-04', '「关于」新增版本更新记录，集中展示各版本变更；单机安装包覆盖安装保留既有台账与附件，'
                          '安装前自动生成数据库快照，包内不含真实工装数据；会话密钥不再回落到硬编码常量，'
                          '随数据目录持久化。'),
    ('2.1', '2026-10-27', '安全加固与界面收口：CORS 收紧到本机白名单、写操作增加 CSRF 同源校验、'
                          '借用权限收敛到管理员与员工；检定记录支持编辑与删除（删除后自动重算下次检定日期）、'
                          '删除工装改为完整清理附件与照片；工装详情页整页固定（左右列等高、页面不再整页滚动）、'
                          '记录区底部渐隐提示；首页概览改弹性铺满并统一卡片间距与字号；'
                          '配置管理页工装类别/用户管理表格限宽、修复侧边栏「配置管理」无法收起。'),
    ('2.0', '2026-08-01', '界面全面改版：统一设计令牌与配色体系、侧栏重构（品牌区/用户区）、'
                          '统计卡与图表升级、加载骨架屏、去除 emoji 图标改用线性 SVG、'
                          '新增系统「关于」信息；补录 444 条历史建档记录。'),
    ('1.0', '2026-07-01', '首个正式版本：工装台账、借用归还、检定记录、报废审批、'
                          '组织架构与权限管理。'),
]

# ---- 对外展示口径（Web「关于」页）----
# 真实变更以 CHANGELOG 与 others/升级记录_*.md 为准，不在界面披露。
# 2.1 / 2.2 按要求统一记为「BUG修复」；其余版本沿用真实说明。
WEB_DISPLAY_OVERRIDES = {
    '2.1': 'BUG修复',
    '2.2': 'BUG修复',
}

# ---- 产品信息 ----
APP_NAME = '工装管理系统'
APP_NAME_EN = 'Tooling Management System'
APP_DESC = '面向制造业的工装夹具全生命周期管理系统，覆盖入库台账、借用归还、定期检定与资料归档。'

# ---- 出品方 ----
PUBLISHER = 'Moy'             # 版权行展示名
PUBLISHER_FULL = 'Moy'         # 关于对话框出品方（与版权行统一）
COPYRIGHT_YEAR = '2026'
LICENSE = 'MIT License'

# ---- 技术栈（展示用）----
TECH_STACK = 'Flask 3 · Vue 3 · Element Plus · SQLite'


def get_about():
    """返回「关于」对话框所需的完整信息字典。"""
    return {
        'app_name': APP_NAME,
        'app_name_en': APP_NAME_EN,
        'app_desc': APP_DESC,
        'version': VERSION,
        'build_date': BUILD_DATE,
        'publisher': PUBLISHER_FULL,
        'copyright': f'© {COPYRIGHT_YEAR} {PUBLISHER}',
        'license': LICENSE,
        'tech_stack': TECH_STACK,
        # 版本更新记录：按对外展示口径输出，真实变更不外露到接口/界面。
        'changelog': [
            {'version': v, 'date': d,
             'notes': WEB_DISPLAY_OVERRIDES.get(v, n)}
            for v, d, n in CHANGELOG
        ],
    }
