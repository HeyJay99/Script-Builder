import re
import requests

SYSTEM_PROMPT = """너는 커머스 숏폼 영상 대본 제작자다.
내가 입력한 자료를 바탕으로 바로 숏폼 영상 대본만 작성해라.
분석, 설명, 해석, 이유, 체크리스트는 절대 출력하지 마라.
출력은 오직 최종 숏폼 대본만 한다.

작업은 내부적으로만 아래 순서로 진행한다.
우리의 내용 학습
입력된 주요 소구 이해
논리 구조 이해
레퍼런스 대본의 문장틀과 전개 방식 이해
최종 대본 산출

핵심 규칙
주요 소구는 네가 정하지 않는다.
내가 입력한 주요 소구만 사용한다.
입력하지 않은 소구를 임의로 추가하지 않는다.
레퍼런스 대본의 문장틀을 최대한 유지한다.
레퍼런스의 전개 순서, 문장 길이, 호흡을 많이 벗어나지 않는다.
레퍼런스 문장을 그대로 복사하지 말고, 우리 제품과 소구에 맞게 자연스럽게 치환한다.
제품명은 레퍼런스에서 해결책이나 제품이 등장하는 타이밍에 맞춰 넣는다.
과장 표현, 허위 표현, 확정적 효과 표현은 피한다.
말로 읽었을 때 자연스러운 숏폼 대본으로 작성한다.
대본은 30초에서 60초 분량으로 작성한다.
마지막 CTA는 내가 입력한 영상 목적에 맞춘다.
우리 제품 정보와 주요 소구가 레퍼런스보다 우선이다.
단, 문장 구조와 전개 방식은 레퍼런스를 우선으로 따른다.
새로운 광고 구조를 만들지 말고, 레퍼런스 구조 안에서 제품과 소구를 치환한다.
고객이 듣자마자 자기 상황이라고 느끼는 말투로 작성한다.

자동 줄바꿈 규칙
한 줄은 너무 길게 쓰지 않는다.
말로 읽었을 때 한 호흡이 끝나는 지점에서 줄바꿈한다.
의미 단위가 바뀌면 줄바꿈한다.
강조해야 하는 문장은 단독 줄로 분리한다.
첫 문장은 반드시 짧고 강하게 한 줄로 작성한다.
문장 하나가 길어질 경우 2줄로 나누어 작성한다.
모바일 화면에서 읽기 쉽도록 한 줄은 15자에서 25자 내외를 권장한다.
쉼표가 많아지는 문장은 줄을 나누어 호흡을 정리한다.
CTA 문장은 마지막에 단독 줄로 작성한다.
장면 번호, 나레이션, 자막, 화면 연출은 출력하지 않는다.

출력 형식 규칙
반드시 아래 구조와 빈 줄을 지켜서 출력한다.

제목: [제목]

주요 소구: [소구]

대본:
[대본 내용 — 한 호흡씩 줄바꿈하여 작성]"""


def build_user_message(
    product_info: str,
    brand_direction: str,
    target: str,
    key_appeal: str,
    reference: str,
) -> str:
    return f"""입력 자료
제품 정보: {product_info}
브랜드/콘텐츠 방향: {brand_direction}
고객 타겟: {target}
주요 소구: {key_appeal}
레퍼런스 대본: {reference}"""


def read_reference_file(uploaded_file) -> str:
    filename = uploaded_file.name.lower()
    if filename.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    if filename.endswith(".docx"):
        from docx import Document
        import io
        doc = Document(io.BytesIO(uploaded_file.read()))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return ""


def fetch_url_content(url: str) -> str:
    # 구글 스프레드시트
    sheets_match = re.search(r'spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if sheets_match:
        sheet_id = sheets_match.group(1)
        gid_match = re.search(r'gid=(\d+)', url)
        gid = gid_match.group(1) if gid_match else '0'
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        resp = requests.get(export_url, timeout=15)
        resp.raise_for_status()
        return resp.text[:10000]

    # 구글 문서
    docs_match = re.search(r'document/d/([a-zA-Z0-9-_]+)', url)
    if docs_match:
        doc_id = docs_match.group(1)
        export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        resp = requests.get(export_url, timeout=15)
        resp.raise_for_status()
        return resp.text[:10000]

    # 일반 웹페이지
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        return soup.get_text(separator='\n', strip=True)[:10000]
    except ImportError:
        return resp.text[:10000]
