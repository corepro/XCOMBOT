from __future__ import annotations
import os
import requests
from .logger import logger
from .config import CONFIG

# 固定 SiliconFlow 端点
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"
SILICONFLOW_DEFAULT_URL = "https://api.siliconflow.cn/v1/chat/completions"


def siliconflow_chat(messages, model: str | None = None, temperature: float | None = None, max_tokens: int | None = None) -> str:
    token = (CONFIG.comment.hf_api_key or "").strip()
    if not token:
        raise RuntimeError("未配置 AI API Key（CONFIG.comment.hf_api_key）。请在 UI 保存后重试。")
    url = SILICONFLOW_DEFAULT_URL
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": (model or (CONFIG.comment.model or "Qwen/QwQ-32B")),
        "messages": messages,
        "temperature": (temperature if temperature is not None else CONFIG.comment.temperature),
        "max_tokens": (max_tokens if max_tokens is not None else CONFIG.comment.max_tokens),
    }
    logger.info("调用 SiliconFlow 模型：{}", model)
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.warning("SiliconFlow 返回结构未预期：{}", data)
        return "不错！"


def hf_chat(messages, model: str, temperature: float = 0.9, max_tokens: int = 100) -> str:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("未设置环境变量 HF_TOKEN。请设置你的 HuggingFace 访问令牌。")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "messages": messages,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    logger.info("调用 HF Chat 模型：{}", model)
    resp = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.warning("HF 返回结构未预期：{}", data)
        return "不错！"


def generate_comment_with_ai(context_text: str, lang: str = "zh") -> str:
    """生成AI评论的别名函数，用于向后兼容"""
    return gen_comment_by_ai(context_text, lang)


def gen_comment_by_ai(context_text: str, lang: str = "zh") -> str:
    # 提示词：小红书风格、真实自然、100字以内
    # 生成提示词：优先使用用户配置的模版，默认为小红书风格
    default_template = """请你扮演小红书用户，针对以下内容生成一条真实自然的评论(100字以内)。
要求：
1. 语言活泼自然，符合小红书用户习惯
2. 可以使用适当的emoji表情
3. 不要有明显的AI痕迹
4. 评论要有针对性，体现对内容的理解
5. 字数控制在100字以内

内容：{content}"""

    tpl = getattr(CONFIG.comment, "prompt_template", default_template)
    prompt = tpl.replace("{content}", (context_text or "")[:300])  # 增加内容长度限制
    messages = [{"role": "user", "content": prompt}]

    # 优先使用 SiliconFlow（固定 URL + Qwen/QwQ-32B），否则回退到 HF Router（用环境变量）
    try:
        if CONFIG.comment.hf_api_key:
            # 固定 SiliconFlow 路径与模型，增加max_tokens以支持100字评论
            max_tokens = min(CONFIG.comment.max_tokens, 200)  # 最多200 tokens，确保100字以内
            text = siliconflow_chat(messages, model="Qwen/QwQ-32B", temperature=CONFIG.comment.temperature, max_tokens=max_tokens)
        else:
            # 仍保留原 HF 路由的后备方案
            system = {"role": "system", "content": "你是一名小红书用户。生成真实自然的中文评论，100字以内。"}
            text = hf_chat([system] + messages, model="deepseek-ai/DeepSeek-V3:novita", temperature=0.8, max_tokens=200)

        # 截断到100字以内（中文字符）
        cleaned_text = text.strip()
        if len(cleaned_text) > 100:
            cleaned_text = cleaned_text[:100]
            # 如果截断位置不是句号或感叹号，尝试找到最近的标点符号
            for i in range(len(cleaned_text)-1, max(0, len(cleaned_text)-20), -1):
                if cleaned_text[i] in '。！？～':
                    cleaned_text = cleaned_text[:i+1]
                    break

        logger.info("AI生成评论({} 字): {}", len(cleaned_text), cleaned_text)
        return cleaned_text

    except Exception as e:
        logger.warning("AI 生成失败，将回退为本地评论：{}", e)
        return "这条信息很有价值，感谢分享"

