import requests
s = requests.Session()

# 登录
r = s.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
print('登录:', r.status_code, r.json())

# 测试 POST /api/tools/
data = {
    'code': 'TEST_CURL_001',
    'drawing_no': 'DWG-CURL-001',
    'name': 'curl测试工装',
    'spec': '规格A',
    'category': '量具',
    'level': 'A类',
    'factory': '',
    'team': '',
    'receiver': '',
    'status': '在库',
    'remark': ''
}
r = s.post('http://127.0.0.1:5000/api/tools/', json=data)
print('新增:', r.status_code, r.json())

# 查询该工装
tool_id = r.json().get('data', {}).get('id')
if tool_id:
    r = s.get(f'http://127.0.0.1:5000/api/tools/{tool_id}')
    print('查询:', r.status_code, r.json())
