import os
import time
import tempfile
from typing import Generator

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_MODEL_SCRIPT = "gemini-2.5-flash"
_MODEL_TRANSCRIBE = "gemini-2.5-flash"


def _get_api_key() -> str:
    env_val = os.getenv("GEMINI_API_KEY", "")
    if env_val:
        return env_val
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def _get_client() -> genai.Client:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)


def generate_script_stream(
    system_prompt: str,
    user_message: str,
) -> Generator[str, None, None]:
    client = _get_client()
    for chunk in client.models.generate_content_stream(
        model=_MODEL_SCRIPT,
        contents=user_message,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    ):
        if chunk.text:
            yield chunk.text


def transcribe_media(uploaded_file) -> str:
    client = _get_client()

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
        uploaded = client.files.upload(
            file=tmp_path,
            config=types.UploadFileConfig(mime_type=mime_type),
        )

        while uploaded.state.name == "PROCESSING":
            time.sleep(2)
            uploaded = client.files.get(name=uploaded.name)

        if uploaded.state.name == "FAILED":
            raise RuntimeError("Gemini 파일 업로드 처리에 실패했습니다.")

        prompt = (
            "이 영상/오디오에서 말하는 내용을 한국어로 정확하게 받아쓰기해줘. "
            "대본 형태로 줄바꿈을 적절히 넣어서 출력해줘. "
            "타임스탬프나 화자 표시 없이 순수 텍스트만 출력해줘."
        )
        response = client.models.generate_content(
            model=_MODEL_TRANSCRIBE,
            contents=[uploaded, prompt],
        )
        return response.text
    finally:
        os.unlink(tmp_path)
