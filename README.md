# AutoFill 智能答题脚本

> 基于 Selenium + DeepSeek + Kimi(Moonshot) 自动完成 100 道选择/判断题，并可持久化登录态。

---

## 1. 环境准备

# Windows 环境示例（cmd）：
```bat
# 1. 克隆仓库并进入
git clone <repo_url> AutoFill
cd AutoFill

# 2. 创建虚拟环境 (Python 3.9+) 并激活
python -m venv .venv
call .\.venv\Scripts\activate.bat

# 3. 安装依赖
pip install -r requirements.txt
#   requirements.txt 内容示例：
#   selenium webdriver-manager python-dotenv requests pydantic

# 4. 确保已安装 Chrome (版本 ≥114) 且 chrome.exe 在 PATH
```

## 2. 创建 `.env`

```env
# DeepSeek
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1   # 如无特殊需求可省略

# KIMI / Moonshot
KIMI_API_KEY=sk-yyyyyyyy
KIMI_BASE_URL=https://api.moonshot.cn/v1        # 末尾不要带 /chat/completions
KIMI_MODEL=moonshot-v1-8k                      # 或 moonshot-v1-32k

# 共识轮次数 (可选，默认 3)
CONSENSUS_ROUNDS=3
```

> ⚠️ **API Key 请务必保密**，不要提交到版本控制。

## 3. 首次运行 & 登录

```bash
$ python auto_fill.py
```

1. 启动后输入测试页面 `pageId`（即答题 URL 最末尾数字）。
2. 脚本会自动打开 Chrome：  
   • 若已保存 Cookie/localStorage ⇒ 将复用登录态。  
   • 否则手动登录后在终端按任意键继续，脚本自动保存凭证到 `cookies.pkl` & `local_storage.json`，下次免登录。

## 4. 自动答题流程

脚本完整步骤：
1. 解析页面获取 100 道题目信息，写入 `question.txt`。
2. 发送题目给 DeepSeek 生成初始答案。
3. 调用 Kimi 校对，循环直至答案一致或达到 `CONSENSUS_ROUNDS` 次数。
4. 校验答案格式 (Pydantic) 并保存 `answer.txt`。
5. 依次滚动并点击页面选项完成答题。
6. 终端提示完成，浏览器保持打开，可自行核对。

## 5. 常见问题

| 问题 | 解决 |
|------|------|
| `ElementClickInterceptedException` | 已通过 `safe_click` 使用 JS 点击并滚动到视口中央解决 |
| DeepSeek 400/404 | 检查 `DEEPSEEK_API_KEY` 是否正确，`DEEPSEEK_BASE_URL` 末尾**不要**带 `/chat/completions` |
| KIMI 404 | 使用正确域名 `https://api.moonshot.cn/v1` 且模型名 `moonshot-v1-8k` / `moonshot-v1-32k` |

## 6. 重要文件

| 文件 | 说明 |
|------|------|
| `auto_fill.py` | 主脚本 |
| `cookies.pkl`  | 登录 Cookie 持久化 |
| `local_storage.json` | 页面 `localStorage` 持久化 |
| `question.txt` | 抓取的题目文本 |
| `answer.txt`   | 共识后的最终答案 |

---

如有问题可在 Issues 提问或 PR 改进 🌟 