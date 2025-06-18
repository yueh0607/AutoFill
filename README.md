# AutoFill 智能答题脚本

> 基于 Selenium + DeepSeek + Kimi(Moonshot) 自动完成 100 道选择/判断题，并可持久化登录态。

---

## 1. 环境准备

# Windows 环境示例（cmd）：
```bat
# 1. 克隆仓库并进入
git clone https://github.com/yueh0607/AutoFill.git
cd AutoFill

# 2. 创建虚拟环境 (Python 3.9+) 并激活
python -m venv .venv
call .\.venv\Scripts\activate.bat

# 3. 安装依赖
pip install -r requirements.txt
```

## 2. 创建 `.env`文件

```env
DEEPSEEK_API_KEY=sk-xxxxxxxx
KIMI_API_KEY=sk-yyyyyyyy
CONSENSUS_ROUNDS=3
```
## 3. 首次运行 & 登录

```bash
$ python auto_fill.py
```

1. 启动后输入测试页面 `pageId`（即答题 URL 最末尾数字）。
2. 脚本会自动打开 Chrome：  
   • 若已保存 Cookie/localStorage ⇒ 将复用登录态。  
   • 否则手动登录后在终端按任意键继续，脚本自动保存凭证到 `cookies.pkl` & `local_storage.json`，下次免登录。

---

如有问题可在 Issues 提问或 PR 改进 🌟 
