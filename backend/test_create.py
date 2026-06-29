import requests, json
s = requests.Session()
r = s.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
print('登录:', r.json())

# 用普通 JSON 发送，不依赖 data=
data = {
    'code': 'TEST_CURL_009',
    'drawing_no': 'DWG-CURL-002',
    'name': 'curl测试2',
    'spec': '规格B',
    'category': '量具',
    'level': 'B类',
    'factory': '新能源',
    'team': '一组',
    'receiver': '张三',
    'status': '在库',
    'remark': 'test'
}
print('发送的 JSON:', json.dumps(data, ensure_ascii=False))
r = s.post('http://127.0.0.1:5000/api/tools/', data=json.dumps(data, ensure_ascii=False), headers={'Content-Type': 'application/json'})
print('响应:', r.status_code, json.dumps(r.json(), ensure_ascii=False, indent=2))
