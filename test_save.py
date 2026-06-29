#!/usr/bin/env python3
"""测试工装保存API"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test():
    # 1. 登录
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = r.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print(f"✅ 登录成功，获取token")
    
    # 2. 获取工装列表
    r = requests.get(f"{BASE_URL}/tools/", headers=headers)
    tools = r.json()["data"]["items"]
    if not tools:
        print("❌ 没有工装数据")
        return
    
    tool = tools[0]
    tool_id = tool["id"]
    print(f"\n📋 测试工装: ID={tool_id}, 编号={tool['code']}")
    print(f"   当前值: 图号={tool.get('drawing_no')!r}, 分类={tool.get('category')!r}, 等级={tool.get('level')!r}")
    
    # 3. 更新测试
    test_data = {
        "drawing_no": "TEST-001-" + str(tool_id),
        "category": "量具",
        "level": "B类"
    }
    print(f"\n📝 发送更新: {test_data}")
    
    r = requests.put(f"{BASE_URL}/tools/{tool_id}", headers=headers, json=test_data)
    result = r.json()
    print(f"   返回: {result.get('msg')}")
    
    # 4. 验证是否保存成功
    r = requests.get(f"{BASE_URL}/tools/{tool_id}", headers=headers)
    updated = r.json()["data"]
    print(f"\n🔍 更新后: 图号={updated.get('drawing_no')!r}, 分类={updated.get('category')!r}, 等级={updated.get('level')!r}")
    
    # 5. 判断结果
    if updated.get('drawing_no') == test_data['drawing_no']:
        print("\n✅ 后端API正常，能正常保存！")
        print("   问题可能在前端：浏览器缓存/字段绑定/发送数据不完整")
    else:
        print("\n❌ 后端API保存失败！")
        print("   需要检查后端代码是否生效")

if __name__ == "__main__":
    test()
