import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from lib.gemini import transcribe_media
from lib import database as db

st.set_page_config(page_title="스크립트 추출", page_icon="🎬", layout="wide")
st.title("🎬 영상 / 오디오에서 스크립트 추출")
st.caption("MP4, MOV, MP3, M4A, WAV 파일을 업로드하면 Gemini가 말하는 내용을 텍스트로 추출합니다.")

# ── DB 연결 ────────────────────────────────────────────────────────────────────
try:
    companies = db.list_companies()
    db_available = True
except Exception as e:
    st.warning(f"DB 연결 실패: {e}\n레퍼런스 저장 기능을 사용할 수 없습니다.")
    companies = []
    db_available = False

# ── 입력 영역 ─────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("파일 업로드")
    media_file = st.file_uploader(
        "영상 또는 오디오 파일",
        type=["mp4", "mov", "mp3", "m4a", "wav"],
        help="파일 크기가 크면 처리에 시간이 걸릴 수 있습니다.",
    )

    if media_file:
        file_size_mb = len(media_file.getvalue()) / (1024 * 1024)
        st.info(f"파일명: {media_file.name}  |  크기: {file_size_mb:.1f} MB")

with col_right:
    st.subheader("레퍼런스 저장 옵션")

    ref_title = st.text_input(
        "레퍼런스 제목",
        placeholder="추출 후 저장할 이름 (예: 경쟁사A 광고 대본)",
    )

    if db_available and companies:
        company_options = {c["name"]: c for c in companies}
        selected_company_name = st.selectbox(
            "연결할 업체 (선택사항)",
            ["(연결 안 함)"] + list(company_options.keys()),
        )
        selected_company = (
            company_options.get(selected_company_name)
            if selected_company_name != "(연결 안 함)"
            else None
        )
    else:
        selected_company = None
        if db_available:
            st.info("저장된 업체가 없습니다. 대본 생성 페이지에서 업체를 먼저 저장하세요.")

# ── 추출 버튼 ─────────────────────────────────────────────────────────────────
st.divider()
extract_col, _ = st.columns([1, 3])
with extract_col:
    extract_btn = st.button("스크립트 추출", type="primary", use_container_width=True, disabled=not media_file)

if extract_btn and media_file:
    st.subheader("추출된 스크립트")
    try:
        with st.spinner("Gemini가 파일을 분석하는 중... (파일 크기에 따라 수십 초 소요)"):
            extracted = transcribe_media(media_file)
    except Exception as e:
        st.error(f"추출 오류: {e}")
        st.stop()

    st.text_area("결과", value=extracted, height=400)
    st.session_state["extracted_script"] = extracted

    # 결과 액션
    dl_col, save_col = st.columns(2)
    with dl_col:
        st.download_button(
            "txt 다운로드",
            data=extracted.encode("utf-8"),
            file_name="추출_스크립트.txt",
            mime="text/plain",
        )

    with save_col:
        if db_available:
            if st.button("레퍼런스로 저장", type="primary", key="save_extracted"):
                if not ref_title:
                    st.error("레퍼런스 제목을 입력해주세요.")
                else:
                    try:
                        db.save_reference(
                            title=ref_title,
                            content=extracted,
                            source="extracted",
                            company_id=selected_company["id"] if selected_company else None,
                        )
                        st.success(
                            f"'{ref_title}' 이름으로 레퍼런스에 저장되었습니다.\n"
                            "대본 생성 페이지에서 바로 사용할 수 있습니다."
                        )
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
        else:
            st.info("DB 연결이 필요합니다.")

# ── 저장된 레퍼런스 목록 ───────────────────────────────────────────────────────
if db_available:
    st.divider()
    st.subheader("저장된 레퍼런스 목록")
    try:
        all_refs = db.list_references()
        if all_refs:
            for ref in all_refs:
                source_label = {"extracted": "📹 추출", "upload": "📄 업로드", "generated": "✨ 생성"}.get(
                    ref.get("source", ""), "기타"
                )
                with st.expander(f"{source_label}  |  {ref['title']}"):
                    st.text_area("내용", value=ref["content"], height=150, disabled=True, key=f"ref_{ref['id']}")
                    if st.button("삭제", key=f"del_{ref['id']}", type="secondary"):
                        db.delete_reference(ref["id"])
                        st.success("삭제되었습니다.")
                        st.rerun()
        else:
            st.info("저장된 레퍼런스가 없습니다.")
    except Exception as e:
        st.error(f"목록 조회 실패: {e}")
