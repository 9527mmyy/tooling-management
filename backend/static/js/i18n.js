/**
 * 工装管理系统 - 极简国际化 (v2.0)
 * 只翻译UI固定文本，不翻译业务数据
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'tooling_lang';

    // UI文本字典（仅界面元素，不含业务数据）
    const DICT = {
        // 登录页
        '工装管理系统': { en: 'Tooling Management' },
        '工号': { en: 'User ID' },
        '密码': { en: 'Password' },
        '登 录': { en: 'Login' },
        '登录成功': { en: 'Login successful' },
        '工号或密码错误': { en: 'Invalid credentials' },

        // 侧边栏菜单
        '首页概览': { en: 'Dashboard' },
        '工装台账': { en: 'Tooling' },
        '借用记录': { en: 'Borrowings' },
        '检定记录': { en: 'Inspections' },
        '检定提醒': { en: 'Reminders' },
        '报废审批': { en: 'Scrap Approval' },
        '配置管理': { en: 'Settings' },
        '工装类别': { en: 'Categories' },
        '工厂设置': { en: 'Factory Config' },
        '用户管理': { en: 'Users' },

        
        // 工装详情页
        '返回工装台账': { en: 'Back to Tooling List' },
        '基本信息': { en: 'Basic Info' },
        '快捷操作': { en: 'Quick Actions' },
        '完工资料': { en: 'Attachments' },
        '暂无完工资料': { en: 'No attachments yet' },
        // 按钮/通用
        '新建': { en: 'New' },
        '编辑': { en: 'Edit' },
        '删除': { en: 'Delete' },
        '保存': { en: 'Save' },
        '取消': { en: 'Cancel' },
        '搜索': { en: 'Search' },
        '重置': { en: 'Reset' },
        '导出': { en: 'Export' },
        '导入': { en: 'Import' },
        '下载模板': { en: 'Download Template' },
        '提交': { en: 'Submit' },
        '关闭': { en: 'Close' },
        '详情': { en: 'Details' },
        '操作': { en: 'Actions' },
        '状态': { en: 'Status' },
        '备注': { en: 'Remarks' },
        '暂无备注信息': { en: 'No remarks' },

        // 工装字段
        '工装编号': { en: 'Tool ID' },
        '工装名称': { en: 'Tool Name' },
        '图号': { en: 'Drawing No.' },
        '类别': { en: 'Category' },
        '等级': { en: 'Grade' },
        '分厂': { en: 'Factory' },
        '班组': { en: 'Team' },
        '领用人': { en: 'User' },
        '入库日期': { en: 'Stock Date' },
        '完工日期': { en: 'Complete Date' },
        '入库时间': { en: 'Entry Date' },
        '下次检定': { en: 'Next Inspection' },
        '检定周期': { en: 'Period' },
        '在库': { en: 'In Stock' },
        '借出': { en: 'Borrowed' },
        '报废': { en: 'Scrapped' },

        // 首页统计
        '工装总数': { en: 'Total Tools' },
        '本月新增': { en: 'New This Month' },
        '本月检定': { en: 'Inspected' },
        '本月报废': { en: 'Scrapped' },
        '累计在库': { en: 'Total in Stock' },
        '工装月度统计趋势（过去12个月）': { en: 'Monthly Trend (12 months)' },

        // 借用
        '借用人': { en: 'Borrower' },
        '借用日期': { en: 'Borrow Date' },
        '归还日期': { en: 'Return Date' },
        '借用事由': { en: 'Purpose' },
        '归还': { en: 'Return' },

        // 检定
        '检定日期': { en: 'Inspection Date' },
        '检定结果': { en: 'Result' },
        '合格': { en: 'Pass' },
        '不合格': { en: 'Fail' },
        '检定人': { en: 'Inspector' },

        // 报废
        '报废申请': { en: 'Scrap Request' },
        '报废原因': { en: 'Reason' },
        '申请人': { en: 'Applicant' },
        '申请日期': { en: 'Apply Date' },
        '审批': { en: 'Approve' },
        '驳回': { en: 'Reject' },

        // 用户
        '用户名': { en: 'Username' },
        '角色': { en: 'Role' },
        '管理员': { en: 'Admin' },
        '工艺员': { en: 'Engineer' },
        '操作工': { en: 'Operator' },
        '修改密码': { en: 'Change Password' },
        '退出登录': { en: 'Logout' },

        // 确认提示
        '确定要删除吗？': { en: 'Are you sure to delete?' },
        '确定要报废吗？': { en: 'Are you sure to scrap?' },
        '确定要归还吗？': { en: 'Are you sure to return?' },
        '操作成功': { en: 'Operation successful' },
        '操作失败': { en: 'Operation failed' },
        '网络错误': { en: 'Network error' },
    };

    // 获取当前语言
    function getLang() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved === 'zh' || saved === 'en') return saved;
        const nav = navigator.language || navigator.userLanguage || '';
        return nav.startsWith('zh') ? 'zh' : 'en';
    }

    // 翻译函数
    function t(zhText) {
        if (getLang() === 'zh') return zhText;
        const item = DICT[zhText];
        return item ? item.en : zhText;
    }

    // 自动翻译页面元素
    function translatePage() {
        if (getLang() === 'zh') return; // 中文不处理

        // 翻译带 data-i18n 的元素
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (DICT[key] && DICT[key].en) {
                el.textContent = DICT[key].en;
            }
        });

        // 翻译 placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (DICT[key] && DICT[key].en) {
                el.placeholder = DICT[key].en;
            }
        });
    }

    // 切换语言
    function setLang(lang) {
        localStorage.setItem(STORAGE_KEY, lang);
        location.reload();
    }

    // 暴露全局API
    window.I18N = {
        t: t,
        getLang: getLang,
        setLang: setLang,
        translatePage: translatePage
    };

    // DOM就绪后自动翻译
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', translatePage);
    } else {
        translatePage();
    }
})();
