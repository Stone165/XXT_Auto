# filepath: core/llm_client.py
from openai import OpenAI
import json
import time
import re

from utils.config_manager import load_config

def call_llm(question, choices_dict=None, max_retries=3):
    config = load_config()
    client = OpenAI(
        api_key=config.get("api_key", ""), 
        base_url=config.get("base_url", ""),
        timeout=15.0
    )
    MODEL_NAME = config.get("model")

    for attempt in range(max_retries):
        try:
            is_true_false = False
            if choices_dict and len(choices_dict) == 2:
                choices_text = "".join(str(v).lower() for v in choices_dict.values())
                tf_keywords = ["对", "错", "正确", "错误", "是", "否", "true", "false"]
                if any(keyword in choices_text for keyword in tf_keywords):
                    is_true_false = True
                
            if not choices_dict:
                # 简答题逻辑
                messages = [
                    {"role": "system", "content": "请简明扼要地回答以下问题，不要输出废话。"},
                    {"role": "user", "content": question}
                ]
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages
                )
                return response.choices[0].message.content.strip()
            
            elif is_true_false:
                # 判断题逻辑
                system_prompt = (
                    "你是一个精准的答题机器人。当前是一道【判断题】。\n"
                    "请直接判断题干中说法的对错，并根据我提供的选项，选出代表正确结果的字母。\n"
                    "必须且只能返回JSON对象：包含 'choices' (一个包含正确选项大写字母的列表，如 [\"A\"] 或 [\"B\"]) "
                    "和 'reason' (一句话简短解释，不要长篇大论的理论)。"
                )
                user_prompt = f"题干说法：{question}\n请匹配以下选项：\n{json.dumps(choices_dict, ensure_ascii=False, indent=2)}"
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages
                )
                return response.choices[0].message.content.strip()

            else:
                # 选择题逻辑 (强制要求输出 JSON)
                system_prompt = "你是一个精准的答题机器人。必须且只能返回JSON对象：包含 'choices' (一个包含正确选项大写字母的列表，单选就1个元素，多选就多个，如 [\"A\"] 或 [\"A\", \"C\", \"D\"]) 和 'reason' (一句话解释)。"
                user_prompt = f"题目：{question}\n选项：\n{json.dumps(choices_dict, ensure_ascii=False, indent=2)}"
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                # 请求 API，启用 JSON 模式
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    response_format={"type": "json_object"} # 强制返回 JSON 格式
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            error_msg = str(e)
            # 硅基流动如果也触发并发/频率限制，通常也是 429
            if "429" in error_msg or "rate limit" in error_msg.lower():
                wait_time = 5 # 硅基流动通常恢复较快，等5秒即可重试
                print(f"触发API限流！等待 {wait_time} 秒后进行第 {attempt + 1} 次重试...")
                time.sleep(wait_time)
            else:
                print(f"API请求发生未知错误: {error_msg}")
                # 遇到死磕不过去的错误，返回兜底格式防止崩溃
                return f'{{"choices": ["A"], "reason": "API请求异常: {error_msg}"}}'
                
    return '{"choices": ["A"], "reason": "重试次数过多，放弃本题"}'

def process_llm_answer(choices_dict, model_output):
    valid_answers = []
    try:
        clean_output = re.sub(r'^```json\s*', '', model_output, flags=re.IGNORECASE)
        clean_output = re.sub(r'```\s*$', '', clean_output).strip()
        data = json.loads(clean_output)
        ans_list = data.get("choices", data.get("choice", []))
    except json.JSONDecodeError:
        ans_list = re.findall(r'(?<![A-Z])[A-Z](?![A-Z])', model_output)

    # 统一清洗和过滤
    if isinstance(ans_list, str):
        ans_list = [c for c in ans_list.upper() if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
    for ans in ans_list:
        ans = str(ans).strip().upper()
        if ans in choices_dict:
            valid_answers.append(ans)
    valid_answers = sorted(list(set(valid_answers)))
    if valid_answers:
        return valid_answers
    # 终极兜底
    return [list(choices_dict.keys())[0]] if choices_dict else ["A"]