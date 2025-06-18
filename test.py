import requests
import json

# 替换为你的 API Key（⚠️注意保密）
API_KEY = "sk-uiftOVJz1OysweJtfn6py0COXioQNq92wK17NTYUnwcAarON"
API_URL = "https://api.moonshot.cn/v1/chat/completions"

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 请求体
data = {
    "model": "moonshot-v1-8k",  # 可选模型示例：moonshot-v1-8k 或 moonshot-v1-32k
    "messages": [
        {"role": "user", "content": "你好，Kimi，现在几点了？"}
    ],
    "temperature": 0.7
}

# 发起请求
response = requests.post(API_URL, headers=headers, data=json.dumps(data))

# 处理响应
if response.status_code == 200:
    result = response.json()
    reply = result['choices'][0]['message']['content']
    print("Kimi 回复：", reply)
else:
    print("请求失败:", response.status_code, response.text)
