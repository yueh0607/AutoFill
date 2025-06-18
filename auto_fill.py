from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
from dotenv import load_dotenv
import requests
import re
from pydantic import BaseModel, ValidationError, validator
from typing import List
import json

def read_answers_from_file(filename):
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"错误：找不到答案文件 {filename}")
        return []

def main():
    pageId = input("请输入页面ID（答题页面URL最后面一串数字）:")
    
    # 创建 Chrome 选项
    options = Options()
    
    # 使用固定的用户数据目录，保证多次运行复用同一 Chrome profile
    user_data_dir = os.path.join(os.path.expanduser("~"), ".auto_fill_chrome")
    options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # 禁用自动化控制检测
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # 其他有用的选项
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    COOKIE_PATH = 'cookies.pkl'
    LS_PATH = 'local_storage.json'

    def load_local_storage(d):
        if not os.path.exists(LS_PATH):
            return
        try:
            with open(LS_PATH, 'r', encoding='utf-8') as f:
                items = json.load(f)
            for k, v in items.items():
                d.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", k, v)
            print('已加载本地 localStorage')
        except Exception as e:
            print(f'加载 localStorage 失败: {e}')

    def save_local_storage(d):
        try:
            items = d.execute_script("var s={}; for (var i=0;i<localStorage.length;i++){var k=localStorage.key(i); s[k]=localStorage.getItem(k);} return s;")
            with open(LS_PATH, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False)
            print('localStorage 已保存')
        except Exception as e:
            print(f'保存 localStorage 失败: {e}')

    driver.get('http://www.ztplus.cn')  # 先访问基础域名才能写入 Cookie / storage

    # 加载 localStorage (需先访问域名)
    load_local_storage(driver)

    # 加载 Cookie
    if os.path.exists(COOKIE_PATH):
        try:
            with open(COOKIE_PATH, 'rb') as cf:
                saved = pickle.load(cf)
            for c in saved:
                # selenium 要求 cookie 字典中必须有 name/value
                driver.add_cookie(c)
            driver.refresh()
            print('已加载本地登录 Cookie，尝试自动登录...')
        except Exception as e:
            print(f'加载 Cookie 失败: {e}')
    else:
        print("检测到已登录状态，直接继续...")
    
    # 打开测试页面
    driver.get('http://www.ztplus.cn/pc/index.html#/paper/testing/'+pageId)
 
    # 等待页面加载完成
    WebDriverWait(driver, 10000000).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'paper-content'))
    )

    # 新增：从页面提取题目
    questions = extract_questions(driver)
    print(f"已提取 {len(questions)} 道题目，正在向 DeepSeek 请求答案...")

    try:
        answers = get_consensus_answers(questions)
    except Exception as api_err:
        print(api_err)
        input("获取答案失败，按回车键退出...")
        return

    if len(answers) != len(questions):
        print(f"警告：DeepSeek 返回的答案数量({len(answers)})与题目数量({len(questions)})不匹配！")

    # 获取所有题目容器
    question_containers = driver.find_elements(By.CLASS_NAME, 'sub-content')

    # 遍历题目并填写答案
    for i, container in enumerate(question_containers):
        if i >= len(answers):
            break
        answer = answers[i]
        question_type = container.find_element(By.CLASS_NAME, 'quer-type').text
        options = container.find_elements(By.CLASS_NAME, 'el-radio')
        for option in options:
            label = option.find_element(By.CLASS_NAME, 'el-radio__label').text
            # 判断题
            if question_type == '判断题':
                if answer == 'A' and '正确' in label:
                    safe_click(driver, option)
                    break
                elif answer == 'B' and '错误' in label:
                    safe_click(driver, option)
                    break
            else:  # 单选题 A/B/C/D
                if label.startswith(answer):
                    safe_click(driver, option)
                    break

    # 将题目写入文件
    with open('question.txt', 'w', encoding='utf-8') as qf:
        for idx, q in enumerate(questions, start=1):
            if q['type'] == '判断题':
                opt_str = 'A、正确  B、错误'
            else:
                opt_str = ' '.join(q['options'])
            qf.write(f"{idx}. {q['text']}  选项: {opt_str}\n")

    print("题目已保存至 question.txt")

    # 保存答案到文件
    with open('answer.txt', 'w', encoding='utf-8') as af:
        for idx, ans in enumerate(answers, start=1):
            af.write(f"{idx}. {ans}\n")

    print("答案已保存至 answer.txt")

    input("答题完成，按回车键退出...")

# 新增：从页面提取题目信息
def extract_questions(driver):
    """提取当前页面所有题目文本及选项
    返回列表，每个元素为 dict: {"type": "单选题"|"判断题", "text": "...", "options": ["A、xxx", "B、yyy", ...]}"""
    questions = []
    containers = driver.find_elements(By.CLASS_NAME, 'sub-content')
    for container in containers:
        try:
            q_type = container.find_element(By.CLASS_NAME, 'quer-type').text.strip()
            # 第二个 <p> 标签是题干
            p_tags = container.find_elements(By.TAG_NAME, 'p')
            q_text = ''
            if len(p_tags) >= 2:
                q_text = p_tags[1].text.strip()
            # 选项
            option_elems = container.find_elements(By.CLASS_NAME, 'el-radio__label')
            option_texts = [opt.text.strip() for opt in option_elems]
            questions.append({
                'type': q_type,
                'text': q_text,
                'options': option_texts
            })
        except Exception as e:
            print(f"提取题目时出错: {e}")
    return questions

# ---------------- LLM 交互相关工具 ----------------
class AnswersSchema(BaseModel):
    answers: List[str]

    @validator('answers')
    def _validate_each(cls, v):
        allowed = {'A', 'B', 'C', 'D'}
        if not v:
            raise ValueError('答案列表不能为空')
        for a in v:
            if a not in allowed:
                raise ValueError(f'非法答案: {a}')
        return v

def _build_prompt(questions, answers: List[str] | None = None, review: bool = False):
    """构造发送给 LLM 的 prompt。若 answers 提供且 review=True，则要求模型对答案进行校正。"""
    header = ("你是专业的考试助手，输出题目的最优答案。输出格式严格如下：\n"
              "1. A\n2. B\n...\n只输出答案，不要解释。")
    if review:
        header = ("你是资深校对老师。已有人给出了答案，请检查每题并修正错误，若无错误保持原答案。"
                  "输出同样格式，仅包含最终答案。")
    lines = [header]
    for idx, q in enumerate(questions, start=1):
        if q['type'] == '判断题':
            opts = 'A、正确  B、错误'
        else:
            opts = ' '.join(q['options'])
        q_line = f"{idx}. {q['text']}  选项: {opts}"
        if answers and not review:
            q_line += f" 当前答案: {answers[idx-1]}"
        lines.append(q_line)
    if answers and review:
        ans_str = '\n'.join([f"{i}. {a}" for i, a in enumerate(answers,1)])
        lines.append("当前答案如下，请依据题目内容进行纠正：")
        lines.append(ans_str)
    return '\n'.join(lines)
    

def _call_llm(api_key: str, prompt: str, base_url: str, model: str):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    # 确保调用路径正确：{base_url}/chat/completions
    url = base_url.rstrip('/') + '/chat/completions'
    resp = requests.post(url, headers=headers, data=json.dumps(body))
    if resp.status_code != 200:
        raise RuntimeError(f"LLM API 请求失败: {resp.status_code} {resp.text}")
    return resp.json()['choices'][0]['message']['content']

def _parse_answers(text: str):
    answers = []
    for line in text.strip().split('\n'):
        m = re.match(r"\s*\d+\.\s*([A-D])", line.strip(), re.IGNORECASE)
        if m:
            answers.append(m.group(1).upper())
    # pydantic 校验
    AnswersSchema(answers=answers)
    return answers

def get_consensus_answers(questions):
    load_dotenv()
    deeptoken = os.getenv('DEEPSEEK_API_KEY')
    kimikey = os.getenv('KIMI_API_KEY')
    if not deeptoken or not kimikey:
        raise RuntimeError('缺少 DEEPSEEK_API_KEY 或 KIMI_API_KEY')

    # DeepSeek 首次作答
    prompt = _build_prompt(questions)
    deep_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    deep_content = _call_llm(deeptoken, prompt, deep_url, 'deepseek-chat')
    answers = _parse_answers(deep_content)

    # 与 KIMI 进行校对循环，可通过环境变量控制轮次
    max_rounds = int(os.getenv('CONSENSUS_ROUNDS', '3'))
    kimi_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
    kimi_model = os.getenv('KIMI_MODEL', 'moonshot-v1-8k')
    for _ in range(max_rounds):
        review_prompt = _build_prompt(questions, answers, review=True)
        kimi_content = _call_llm(kimikey, review_prompt, kimi_url, kimi_model)
        kimi_answers = _parse_answers(kimi_content)
        if kimi_answers == answers:
            break
        answers = kimi_answers
    return answers

# 安全点击，避免顶部悬浮元素遮挡
def safe_click(drv, element):
    drv.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    drv.execute_script("arguments[0].click();", element)

if __name__ == '__main__':
    main()