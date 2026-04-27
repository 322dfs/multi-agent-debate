import requests
import json

# 测试获取辩手列表
print("测试获取辩手列表...")
response = requests.get("http://localhost:8000/api/debaters")
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")
print()

# 测试开始辩论
print("测试开始辩论...")
start_data = {
    "topic": "AI会取代程序员吗？",
    "debaters": ["phoenix_riser", "zhangxuefeng"]
}
response = requests.post("http://localhost:8000/api/debate/start", json=start_data)
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")
session_id = response.json().get("session_id")
print()

# 测试运行轮次
if session_id:
    print("测试运行轮次...")
    round_data = {
        "session_id": session_id
    }
    response = requests.post("http://localhost:8000/api/debate/round", json=round_data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    print()

# 测试主持人总结
if session_id:
    print("测试主持人总结...")
    moderate_data = {
        "session_id": session_id
    }
    response = requests.post("http://localhost:8000/api/debate/moderate", json=moderate_data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    print()

# 测试裁判裁决
if session_id:
    print("测试裁判裁决...")
    judge_data = {
        "session_id": session_id
    }
    response = requests.post("http://localhost:8000/api/debate/judge", json=judge_data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    print()

# 测试用户消息
if session_id:
    print("测试用户消息...")
    user_message_data = {
        "session_id": session_id,
        "message": "我认为AI会辅助程序员，但不会完全取代他们"
    }
    response = requests.post("http://localhost:8000/api/debate/user-message", json=user_message_data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    print()

# 测试下一轮
if session_id:
    print("测试下一轮...")
    next_round_data = {
        "session_id": session_id
    }
    response = requests.post("http://localhost:8000/api/debate/next-round", json=next_round_data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
