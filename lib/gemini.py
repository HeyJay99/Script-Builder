import os
from typing import Generator

import anthropic
from dotenv import load_dotenv

load_dotenv()

_MODEL = "claude-opus-4-7"


def _get_api_key() -> str:
    env_val = os.getenv("ANTHROPIC_API_KEY", "")
    if env_val:
        return env_val
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return ""


def _get_client() -> anthropic.Anthropic:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
    return anthropic.Anthropic(api_key=api_key)


def generate_script_stream(
    system_prompt: str,
    user_message: str,
) -> Generator[str, None, None]:
    client = _get_client()
    with client.messages.stream(
        model=_MODEL,
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            yield text


def transcribe_media(uploaded_file) -> str:
    raise NotImplementedError(
        "영상/오디오 스크립트 추출 기능은 Claude API에서 지원되지 않습니다.\n"
        "이 기능을 사용하려면 Gemini API 키가 필요합니다."
    )
