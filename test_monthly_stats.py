#!/usr/bin/env python3
"""测试月度统计API"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# 创建session（保持cookie）
s = requests.Session()

# 1. 登录
print("=" * 50)
print("1. 登录")
r = s.post(f"{BASE_URL}/api/auth/login", 
           json={"username": "admin", "password": "admin123"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"Response: {r.json()}")
else:
    print(f"Error: {r.text}")
    exit(1)

# 2. 测试基础统计API
print("\n" + "=" * 50)
print("2. 测试基础统计API (/api/tools/stats)")
r = s.get(f"{BASE_URL}/api/tools/stats")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
else:
    print(f"Error: {r.text}")

# 3. 测试月度统计API（新增）
print("\n" + "=" * 50)
print("3. 测试月度统计API (/api/tools/stats/monthly) [新增功能]")
r = s.get(f"{BASE_URL}/api/tools/stats/monthly")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # 检查数据格式
    if "data" in data and "labels" in data["data"]:
        labels = data["data"]["labels"]
        new_tools = data["data"]["new_tools"]
        inspections = data["data"]["inspections"]
        scraps = data["data"]["scraps"]
        cumulative = data["data"]["cumulative"]
        
        print(f"\n✅ 月度统计API正常工作！")
        print(f"  - 月份数量: {len(labels)}")
        print(f"  - 第一个月: {labels[0]}")
        print(f"  - 最后一个月: {labels[-1]}")
        print(f"  - 新增工装数据: {new_tools}")
        print(f"  - 检定记录数据: {inspections}")
        print(f"  - 报废工装数据: {scraps}")
        print(f"  - 累计工装数据: {cumulative}")
    else:
        print(f"\n❌ API返回格式错误")
else:
    print(f"Error: {r.text}")

# 4. 测试前端页面
print("\n" + "=" * 50)
print("4. 测试前端页面")
r = s.get(f"{BASE_URL}/")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    html = r.text
    # 检查是否包含ECharts和月度统计相关代码
    checks = {
        "ECharts库": "echarts.min.js" in html,
        "图表容器": "monthlyChart" in html,
        "loadMonthlyStats方法": "loadMonthlyStats" in html,
        "月度统计API调用": "/api/tools/stats/monthly" in html,
    }
    
    print("前端代码检查:")
    all_pass = True
    for name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            all_pass = False
    
    if all_pass:
        print("\n✅ 前端代码正常，包含所有必要组件！")
    else:
        print("\n⚠️ 前端代码可能不完整")
else:
    print(f"Error: {r.text}")

print("\n" + "=" * 50)
print("测试完成！")
print(f"前端访问地址: <ADDRESS> http://172.16.120.79:5000</ADDRESS>")
print(f"登录账号: admin / admin123")
