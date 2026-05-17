import os
import time
import tempfile
from typing import Generator

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_MODEL_SCRIPT = "gemini-2.0-flash"
_MODEL_TRANSCRIBE = "gemini-2.0-flash"


def _get_api_key() -> str:
    env_val = os.getenv("GEMINI_API_KEY", "")
    if env_val:
        return env_val
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def _get_client() -> None:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
    genai.configure(api_key=api_key)


def generate_script_stream(
    system_prompt: str,
    user_message: str,
) -> Generator[str, None, None]:
    _get_client()
    model = genai.GenerativeModel(
        model_name=_MODEL_SCRIPT,
        system_instruction=system_prompt,
    )
    response = model.generate_content(user_message, stream=True)
    for chunk in response:
        if chunk.text:
            yield chunk.text


def transcribe_media(uploaded_file) -> str:
    """영상/오디오 파일을 받아 한국어 대본(전사 텍스트)을 반환한다."""
    _get_client()

    suffix = os.path.splitext(uploaded_file.name)[-1].lower()
    mime_map = {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".wav": "audio/wav",
    }
    mime_type = mime_map.get(suffix, "application/octet-stream")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        uploaded = genai.upload_file(tmp_path, mime_type=mime_type)

        # 파일 처리 완료 대기
        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = genai.get_file(uploaded.name)

        if uploaded.state.name == "FAILED":
            raise RuntimeError("Gemini 파일 업로드 처리에 실패했습니다.")

        model = genai.GenerativeModel(_MODEL_TRANSCRIBE)
        prompt = (
            "이 영상/오디오에서 말하는 내용을 한국어로 정확하게 받아쓰기해줘. "
            "대본 형태로 줄바꿈을 적절히 넣어서 출력해줘. "
            "타임스탬프나 화자 표시 없이 순수 텍스트만 출력해줘."
        )
        response = model.generate_content([uploaded, prompt])
        return response.text
    finally:
        os.unlink(tmp_path)
