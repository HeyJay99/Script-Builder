import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from lib.prompt import SYSTEM_PROMPT, build_user_message, read_reference_file
from lib.gemini import generate_script_stream
from lib import database as db

st.set_page_config(page_title="대본 생성", page_icon="📝", layout="wide")
st.title("📝 숏폼 광고 대본 생성")

# ── 업체 선택 사이드바 ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("업체 관리")

    try:
        companies = db.list_companies()
        db_available = True
    except Exception as e:
        st.warning(f"DB 연결 실패: {e}\n로컬 모드로 실행됩니다.")
        companies = []
        db_available = False

    company_options = {c["name"]: c for c in companies}
    selected_name = st.selectbox(
        "저장된 업체 선택",
        ["(직접 입력)"] + list(company_options.keys()),
        key="company_select",
    )

    selected_company = company_options.get(selected_name) if selected_name != "(직접 입력)" else None

    st.divider()

    # 업체 저장 / 수정
    with st.expander("업체 저장 / 수정", expanded=False):
        save_name = st.text_input("업체명", value=selected_company["name"] if selected_company else "")
        if st.button("현재 입력 내용으로 저장", disabled=not db_available):
            if not save_name:
                st.error("업체명을 입력하세요.")
            else:
                payload = {
                    "name": save_name,
                    "product_info": st.session_state.get("product_info", ""),
                    "brand_direction": st.session_state.get("brand_direction", ""),
                    "target": st.session_state.get("target", ""),
                }
                try:
                    if selected_company and save_name == selected_company["name"]:
                        db.update_company(selected_company["id"], **payload)
                        st.success("업체 정보가 수정되었습니다.")
                    else:
                        db.save_company(**payload)
                        st.success(f"'{save_name}' 업체가 저장되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 실패: {e}")

    # 업체 삭제
    if selected_company and db_available:
        with st.expander("업체 삭제", expanded=False):
            if st.button("이 업체 삭제", type="secondary"):
                db.delete_company(selected_company["id"])
                st.success("삭제되었습니다.")
                st.rerun()

# ── 메인 입력 폼 ──────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("입력 정보")

    product_info = st.text_area(
        "제품 정보",
        value=selected_company["product_info"] if selected_company else "",
        height=130,
        placeholder="제품명, 가격, 구성, 특징, 상세페이지 내용 등",
        key="product_info",
    )
    brand_direction = st.text_area(
        "브랜드 / 콘텐츠 방향",
        value=selected_company["brand_direction"] if selected_company else "",
        height=100,
        placeholder="브랜드 톤, 반드시 살릴 메시지",
        key="brand_direction",
    )
    target = st.text_area(
        "고객 타겟",
        value=selected_company["target"] if selected_company else "",
        height=100,
        placeholder="타겟의 고민, 상황, 욕망",
        key="target",
    )
    key_appeal = st.text_input(
        "주요 소구",
        placeholder="예) 건조, 모공, 탄력 (이번 영상에서 사용할 소구)",
    )

with col_right:
    st.subheader("레퍼런스 대본")

    # 레퍼런스 탭: 저장된 것 선택 / 파일 업로드 / 직접 입력
    ref_tab1, ref_tab2, ref_tab3 = st.tabs(["저장된 레퍼런스", "파일 업로드", "직접 입력"])

    reference_text = ""

    with ref_tab1:
        ref_company_id = selected_company["id"] if selected_company else None
        try:
            refs = db.list_references(ref_company_id) if db_available else []
        except Exception:
            refs = []

        if refs:
            ref_options = {r["title"]: r for r in refs}
            chosen_ref_title = st.selectbox("레퍼런스 선택", list(ref_options.keys()))
            chosen_ref = ref_options[chosen_ref_title]
            ref_preview = st.text_area(
                "미리보기",
                value=chosen_ref["content"],
                height=200,
                disabled=True,
            )
            if st.button("이 레퍼런스 사용", key="use_saved_ref"):
                st.session_state["active_reference"] = chosen_ref["content"]
                st.session_state["active_ref_source"] = "saved"

            # 삭제
            if st.button("삭제", key="del_ref", type="secondary"):
                db.delete_reference(chosen_ref["id"])
                st.success("삭제되었습니다.")
                st.rerun()
        else:
            st.info("저장된 레퍼런스가 없습니다.")

    with ref_tab2:
        uploaded = st.file_uploader(
            "레퍼런스 파일 업로드",
            type=["txt", "docx"],
            help=".txt 또는 .docx 파일",
        )
        if uploaded:
            try:
                file_text = read_reference_file(uploaded)
                st.text_area("파일 내용 미리보기", value=file_text, height=180, disabled=True)
                if st.button("이 파일 내용 사용", key="use_file_ref"):
                    st.session_state["active_reference"] = file_text
                    st.session_state["active_ref_source"] = "file"
            except Exception as e:
                st.error(f"파일 읽기 실패: {e}")

    with ref_tab3:
        direct_text = st.text_area("직접 입력", height=200, placeholder="레퍼런스 대본 내용을 붙여넣으세요.")
        if st.button("직접 입력 내용 사용", key="use_direct_ref"):
            st.session_state["active_reference"] = direct_text
            st.session_state["active_ref_source"] = "direct"

    # 현재 선택된 레퍼런스 표시
    active_ref = st.session_state.get("active_reference", "")
    if active_ref:
        st.success(f"레퍼런스 적용됨 ({st.session_state.get('active_ref_source', '')})")
        reference_text = active_ref

# ── 생성 버튼 ─────────────────────────────────────────────────────────────────
st.divider()
generate_col, _ = st.columns([1, 3])
with generate_col:
    generate_btn = st.button("대본 생성", type="primary", use_container_width=True)

if generate_btn:
    missing = []
    if not product_info.strip():
        missing.append("제품 정보")
    if not key_appeal.strip():
        missing.append("주요 소구")
    if not reference_text.strip():
        missing.append("레퍼런스 대본")

    if missing:
        st.error(f"필수 입력 항목이 빠져있습니다: {', '.join(missing)}")
    else:
        user_msg = build_user_message(
            product_info, brand_direction, target, key_appeal, reference_text
        )
        st.subheader("생성된 대본")
        result_placeholder = st.empty()
        full_text = ""

        try:
            with st.spinner("Gemini가 대본을 작성하는 중..."):
                for chunk in generate_script_stream(SYSTEM_PROMPT, user_msg):
                    full_text += chunk
                    result_placeholder.markdown(full_text)
        except Exception as e:
            st.error(f"생성 오류: {e}")
            st.stop()

        # 결과 액션
        st.session_state["last_script"] = full_text
        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            st.download_button(
                "txt 다운로드",
                data=full_text.encode("utf-8"),
                file_name="대본.txt",
                mime="text/plain",
            )

        with action_col2:
            # Streamlit에서 클립보드 복사는 JS 사용
            st.button(
                "클립보드 복사",
                on_click=lambda: st.write(
                    f"<script>navigator.clipboard.writeText({repr(full_text)})</script>",
                    unsafe_allow_html=True,
                ),
                key="copy_btn",
            )

        with action_col3:
            if db_available:
                if st.button("레퍼런스로 저장", key="save_as_ref"):
                    st.session_state["show_ref_save_form"] = True

        if st.session_state.get("show_ref_save_form") and db_available:
            with st.form("save_ref_form"):
                ref_title = st.text_input("레퍼런스 제목", value=f"{selected_name} 생성 대본")
                submitted = st.form_submit_button("저장")
                if submitted and ref_title:
                    db.save_reference(
                        title=ref_title,
                        content=full_text,
                        source="generated",
                        company_id=selected_company["id"] if selected_company else None,
                    )
                    st.success("레퍼런스로 저장되었습니다.")
                    st.session_state["show_ref_save_form"] = False
