(async () => {

const { createApp, ref, reactive, computed, onMounted, watch } = Vue;

const api = axios.create({ 
    baseURL: '/api', 
    withCredentials: true,
    timeout: 10000  // 10秒超时
});

api.interceptors.response.use(res => res, err => {
    if (err.code === 'ECONNABORTED') {
        ElMessage.error('请求超时，请检查网络');
    }
    if (err.response && err.response.status === 401) {
        app.loggedIn = false;
        ElMessage.error('登录已过期，请重新登录');
    }
    return Promise.reject(err);
});

const app = createApp({
    setup() {
        const loggedIn = ref(false);
        const loginLoading = ref(false);
        const loginForm = reactive({ username: '', password: '' });
        const currentUser = reactive({ username: '', role: '' });
        const currentPage = ref('dashboard');
        const saving = ref(false);

        const isAdmin = computed(() => currentUser.role === 'admin');
        const pageTitle = computed(() => {
            const map = { dashboard: '首页概览', tools: '工装台账', borrows: '借用记录', inspections: '鉴定记录', users: '用户管理', scraps: '报废审批' }; return map[currentPage.value] || '';
        });

        // 统计
        const stats = reactive({ total: 0, in_stock: 0, borrowed: 0, repairing: 0, scrapped: 0, due_soon: 0, overdue: 0 });
        const loadStats = async () => { try { const r = await api.get('/tools/stats'); Object.assign(stats, r.data.data); } catch(e) {} };

        // 工装
        const tools = ref([]);
        const toolTotal = ref(0);
        const toolSearch = reactive({ keyword: '', status: '', page: 1 });
        const toolDialogVisible = ref(false);
        const toolDetailVisible = ref(false);
        const currentTool = ref(null);
        const uploadFileType = ref('入库资料');
        const toolForm = reactive({ id: null, code: '', name: '', spec: '', status: '在库', purchase_date: '', next_inspection_date: '', remark: '' });

        const loadTools = async () => {
            try {
                const r = await api.get('/tools/', { params: toolSearch });
                tools.value = r.data.data.items;
                toolTotal.value = r.data.data.total;
            } catch(e) { ElMessage.error('加载失败'); }
        };

        const openToolDialog = (tool = null) => {
            if (tool) { Object.assign(toolForm, { id: tool.id, code: tool.code, name: tool.name, spec: tool.spec, status: tool.status, purchase_date: tool.purchase_date, next_inspection_date: tool.next_inspection_date, remark: tool.remark }); }
            else { Object.assign(toolForm, { id: null, code: '', name: '', spec: '', status: '在库', purchase_date: '', next_inspection_date: '', remark: '' }); }
            toolDialogVisible.value = true;
        };

        const saveTool = async () => {
            if (!toolForm.code || !toolForm.name) { ElMessage.warning('编号和名称不能为空'); return; }
            saving.value = true;
            try {
                const res = toolForm.id 
                    ? await api.put(`/tools/${toolForm.id}`, toolForm)
                    : await api.post('/tools/', toolForm);
                console.log('保存响应:', res);
                if (res.data.code === 200) {
                    ElMessage.success('保存成功');
                    toolDialogVisible.value = false;
                    loadTools();
                    loadStats();
                } else {
                    ElMessage.error(res.data.msg || '保存失败');
                }
            } catch(e) { 
                console.error('保存失败:', e);
                ElMessage.error(e.response?.data?.msg || e.message || '保存失败'); 
            } finally {
                saving.value = false;
            }
        };

        const deleteTool = async (tool) => {
            try { 
                await ElMessageBox.confirm(`确定删除工装 ${tool.code} ${tool.name}？`, '确认', { type: 'warning' }); 
            } catch { 
                return; 
            }
            try { 
                const res = await api.delete(`/tools/${tool.id}`);
                console.log('删除响应:', res);
                if (res.data.code === 200) {
                    ElMessage.success('删除成功'); 
                    loadTools(); 
                    loadStats();
                } else {
                    ElMessage.error(res.data.msg || '删除失败');
                }
            } catch(e) { 
                console.error('删除失败:', e);
                ElMessage.error(e.response?.data?.msg || '删除失败'); 
            }
        };

        const viewTool = async (tool) => {
            try { const r = await api.get(`/tools/${tool.id}`); currentTool.value = r.data.data; toolDetailVisible.value = true; } catch(e) { ElMessage.error('加载失败'); }
        };

        // 借用
        const borrows = ref([]);
        const borrowTotal = ref(0);
        const borrowSearch = reactive({ status: '', borrower: '', page: 1 });
        const borrowDialogVisible = ref(false);
        const borrowForm = reactive({ tool_id: null, tool_code: '', tool_name: '', borrower: '' });

        const loadBorrows = async () => {
            try { const r = await api.get('/borrows/', { params: borrowSearch }); borrows.value = r.data.data.items; borrowTotal.value = r.data.data.total; } catch(e) { ElMessage.error('加载失败'); }
        };

        const openBorrowDialog = (tool) => {
            Object.assign(borrowForm, { tool_id: tool.id, tool_code: tool.code, tool_name: tool.name, borrower: currentUser.username });
            borrowDialogVisible.value = true;
        };

        const submitBorrow = async () => {
            saving.value = true;
            try { 
                const res = await api.post('/borrows/', borrowForm);
                console.log('借用响应:', res);
                if (res.data.code === 200) {
                    ElMessage.success('借用成功'); 
                    borrowDialogVisible.value = false; 
                    loadTools(); 
                    loadBorrows(); 
                    loadStats();
                } else {
                    ElMessage.error(res.data.msg || '借用失败');
                }
            } catch(e) { 
                console.error('借用失败:', e);
                ElMessage.error(e.response?.data?.msg || '借用失败'); 
            } finally {
                saving.value = false;
            }
        };

        const returnTool = async (record) => {
            try { await api.post(`/borrows/${record.id}/return`); ElMessage.success('归还成功'); loadBorrows(); loadTools(); loadStats(); } catch(e) { ElMessage.error(e.response?.data?.msg || '归还失败'); }
        };

        // 鉴定
        const inspections = ref([]);
        const inspectionTotal = ref(0);
        const inspectionSearch = reactive({ result: '', page: 1 });
        const scrapDialogVisible = ref(false);
        const scrapForm = reactive({ tool_id: null, tool_code: '', tool_name: '', reason: '' });
        const scrapSearch = reactive({ status: '', page: 1 });
        const scraps = ref([]);
        const scrapTotal = ref(0);

        const inspectionDialogVisible = ref(false);
        const inspectionForm = reactive({ tool_id: null, tool_code: '', tool_name: '', inspect_date: '', result: '合格', next_date: '', inspector: '', remark: '' });

        const loadInspections = async () => {
            try { const r = await api.get('/inspections/', { params: inspectionSearch }); inspections.value = r.data.data.items; inspectionTotal.value = r.data.data.total; } catch(e) { ElMessage.error('加载失败'); }
        };

        // 报废
        const scrapTool = async (tool) => {
            if (isAdmin.value) {
                // admin: 直接报废
                try { await ElMessageBox.confirm(\`确定报废工装 \${tool.code} \${tool.name}？\`, '确认报废', { type: 'warning' }); } catch { return; }
                try {
                    const res = await api.post('/scraps/', { tool_id: tool.id, reason: 'admin直接报废' });
                    if (res.data.code === 200) { ElMessage.success(res.data.msg); loadTools(); loadStats(); }
                    else { ElMessage.error(res.data.msg); }
                } catch(e) { ElMessage.error(e.response?.data?.msg || '报废失败'); }
            } else {
                // 普通员工: 提交报废申请
                Object.assign(scrapForm, { tool_id: tool.id, tool_code: tool.code, tool_name: tool.name, reason: '' });
                scrapDialogVisible.value = true;
            }
        };

        const submitScrap = async () => {
            saving.value = true;
            try {
                const res = await api.post('/scraps/', scrapForm);
                if (res.data.code === 200) { ElMessage.success(res.data.msg); scrapDialogVisible.value = false; loadTools(); loadStats(); }
                else { ElMessage.error(res.data.msg); }
            } catch(e) { ElMessage.error(e.response?.data?.msg || '提交失败'); }
            saving.value = false;
        };

        const loadScraps = async () => {
            try { const r = await api.get('/scraps/', { params: scrapSearch }); scraps.value = r.data.data.items; scrapTotal.value = r.data.data.total; } catch(e) { ElMessage.error('加载失败'); }
        };

        const approveScrap = async (req) => {
            try { await ElMessageBox.confirm(\`批准报废工装 \${req.tool_code} \${req.tool_name}？\`, '确认批准', { type: 'warning' }); } catch { return; }
            try {
                const res = await api.put(\`/scraps/\${req.id}/approve\`);
                if (res.data.code === 200) { ElMessage.success(res.data.msg); loadScraps(); loadTools(); loadStats(); }
                else { ElMessage.error(res.data.msg); }
            } catch(e) { ElMessage.error(e.response?.data?.msg || '审批失败'); }
        };

        const rejectScrap = async (req) => {
            try { await ElMessageBox.confirm(\`拒绝报废工装 \${req.tool_code} \${req.tool_name}？\`, '确认拒绝', { type: 'warning' }); } catch { return; }
            try {
                const res = await api.put(\`/scraps/\${req.id}/reject\`, { reject_reason: '管理员拒绝' });
                if (res.data.code === 200) { ElMessage.success(res.data.msg); loadScraps(); loadTools(); }
                else { ElMessage.error(res.data.msg); }
            } catch(e) { ElMessage.error(e.response?.data?.msg || '审批失败'); }
        };

        const openInspectionDialog = (tool) => {
            Object.assign(inspectionForm, { tool_id: tool.id, tool_code: tool.code, tool_name: tool.name, inspect_date: '', result: '合格', next_date: '', inspector: '', remark: '' });
            inspectionDialogVisible.value = true;
        };

        const submitInspection = async () => {
            if (!inspectionForm.inspect_date || !inspectionForm.result) { ElMessage.warning('请填写鉴定日期和结果'); return; }
            saving.value = true;
            try { 
                const res = await api.post('/inspections/', inspectionForm);
                console.log('鉴定响应:', res);
                if (res.data.code === 200) {
                    ElMessage.success('鉴定记录添加成功'); 
                    inspectionDialogVisible.value = false; 
                    loadTools(); 
                    loadInspections(); 
                    loadStats();
                } else {
                    ElMessage.error(res.data.msg || '添加失败');
                }
            } catch(e) { 
                console.error('鉴定失败:', e);
                ElMessage.error(e.response?.data?.msg || '添加失败'); 
            } finally {
                saving.value = false;
            }
        };

        // 附件
        const onUploadSuccess = (response) => {
            if (response.code === 200) { ElMessage.success('上传成功'); viewTool(currentTool.value); }
            else { ElMessage.error(response.msg || '上传失败'); }
        };
        const beforeUpload = (file) => { return true; };
        const downloadFile = (att) => { window.open(`/api/attachments/${att.id}/download`); };
        const deleteAttachment = async (att) => {
            try { await ElMessageBox.confirm('确定删除此附件？', '确认', { type: 'warning' }); } catch { return; }
            try { await api.delete(`/attachments/${att.id}`); ElMessage.success('删除成功'); viewTool(currentTool.value); } catch(e) { ElMessage.error('删除失败'); }
        };

        // 用户
        const users = ref([]);
        const userDialogVisible = ref(false);
        const userForm = reactive({ id: null, username: '', password: '', role: 'employee' });

        const loadUsers = async () => {
            try { const r = await api.get('/auth/users'); users.value = r.data.data; } catch(e) {}
        };

        const openUserDialog = (user = null) => {
            if (user) { Object.assign(userForm, { id: user.id, username: user.username, password: '', role: user.role }); }
            else { Object.assign(userForm, { id: null, username: '', password: '', role: 'employee' }); }
            userDialogVisible.value = true;
        };

        const saveUser = async () => {
            if (!userForm.id && !userForm.password) { ElMessage.warning('请输入密码'); return; }
            saving.value = true;
            try {
                if (userForm.id) { await api.put(`/auth/users/${userForm.id}`, userForm); }
                else { await api.post('/auth/users', userForm); }
                ElMessage.success('保存成功');
                userDialogVisible.value = false;
                loadUsers();
            } catch(e) { ElMessage.error(e.response?.data?.msg || '保存失败'); }
            saving.value = false;
        };

        const deleteUser = async (user) => {
            try { await ElMessageBox.confirm(`确定删除用户 ${user.username}？`, '确认', { type: 'warning' }); } catch { return; }
            try { await api.delete(`/auth/users/${user.id}`); ElMessage.success('删除成功'); loadUsers(); } catch(e) { ElMessage.error(e.response?.data?.msg || '删除失败'); }
        };

        // 登录/登出
        const handleLogin = async () => {
            if (!loginForm.username || !loginForm.password) { ElMessage.warning('请输入用户名和密码'); return; }
            loginLoading.value = true;
            try {
                const r = await api.post('/auth/login', loginForm);
                if (r.data.code === 200) {
                    loggedIn.value = true;
                    Object.assign(currentUser, r.data.data);
                    loadStats();
                    ElMessage.success('登录成功');
                } else { ElMessage.error(r.data.msg); }
            } catch(e) { ElMessage.error(e.response?.data?.msg || '登录失败'); }
            loginLoading.value = false;
        };

        const handleLogout = async () => {
            try { await api.post('/auth/logout'); } catch {}
            loggedIn.value = false;
            currentPage.value = 'dashboard';
        };

        // 工具函数
        const statusTagType = (status) => ({ '在库': 'success', '借出': 'warning', '维修': 'danger', '报废': 'info' }[status] || '');
        const isOverdue = (dateStr) => { if (!dateStr) return false; return new Date(dateStr) < new Date(); };

        // 页面切换加载
        watch(currentPage, (page) => {
            if (page === 'dashboard') loadStats();
            if (page === 'tools') loadTools();
            if (page === 'borrows') loadBorrows();
            if (page === 'inspections') loadInspections();
            if (page === 'users') loadUsers();
        });

        onMounted(() => {
            api.get('/auth/info').then(r => { if (r.data.code === 200) { loggedIn.value = true; Object.assign(currentUser, r.data.data); loadStats(); } }).catch(() => {});
        });

        return {
            loggedIn, loginLoading, loginForm, currentUser, currentPage, saving, isAdmin, pageTitle,
            stats, loadStats,
            tools, toolTotal, toolSearch, loadTools, toolDialogVisible, toolDetailVisible, currentTool, toolForm, openToolDialog, saveTool, deleteTool, viewTool, uploadFileType, onUploadSuccess, beforeUpload, downloadFile, deleteAttachment,
            borrows, borrowTotal, borrowSearch, loadBorrows, borrowDialogVisible, borrowForm, openBorrowDialog, submitBorrow, returnTool,
            scrapDialogVisible, scrapForm, scrapSearch, scraps, scrapTotal,
            loadScraps, approveScrap, rejectScrap, scrapTool, submitScrap,
            inspections, inspectionTotal, inspectionSearch, loadInspections, inspectionDialogVisible, inspectionForm, openInspectionDialog, submitInspection,
            users, loadUsers, userDialogVisible, userForm, openUserDialog, saveUser, deleteUser,
            handleLogin, handleLogout, statusTagType, isOverdue
        };
    }
});

const { ElMessage, ElMessageBox } = ElementPlus;

app.use(ElementPlus);
app.mount('#app');

})();
