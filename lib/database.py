import os
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


def _get_secret(key: str) -> str:
    # .env 우선, 없으면 Streamlit Cloud secrets 사용
    env_val = os.getenv(key, "")
    if env_val:
        return env_val
    try:
        import streamlit as st
        return st.secrets.get(key, "")
    except Exception:
        return ""


def _get_client() -> Client:
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.")
    return create_client(url, key)


# ── 업체(companies) ─────────────────────────────────────────────────────────

def list_companies() -> list[dict]:
    client = _get_client()
    result = client.table("companies").select("*").order("name").execute()
    return result.data or []


def get_company(company_id: str) -> Optional[dict]:
    client = _get_client()
    result = (
        client.table("companies").select("*").eq("id", company_id).single().execute()
    )
    return result.data


def save_company(name: str, product_info: str, brand_direction: str, target: str) -> dict:
    client = _get_client()
    result = (
        client.table("companies")
        .insert(
            {
                "name": name,
                "product_info": product_info,
                "brand_direction": brand_direction,
                "target": target,
            }
        )
        .execute()
    )
    return result.data[0]


def update_company(
    company_id: str,
    name: str,
    product_info: str,
    brand_direction: str,
    target: str,
) -> dict:
    client = _get_client()
    result = (
        client.table("companies")
        .update(
            {
                "name": name,
                "product_info": product_info,
                "brand_direction": brand_direction,
                "target": target,
            }
        )
        .eq("id", company_id)
        .execute()
    )
    return result.data[0]


def delete_company(company_id: str) -> None:
    client = _get_client()
    client.table("companies").delete().eq("id", company_id).execute()


# ── 레퍼런스(references) ─────────────────────────────────────────────────────

def list_references(company_id: Optional[str] = None) -> list[dict]:
    client = _get_client()
    query = client.table("script_refs").select("*").order("created_at", desc=True)
    if company_id:
        query = query.eq("company_id", company_id)
    result = query.execute()
    return result.data or []


def save_reference(
    title: str,
    content: str,
    source: str,
    company_id: Optional[str] = None,
) -> dict:
    client = _get_client()
    payload: dict = {"title": title, "content": content, "source": source}
    if company_id:
        payload["company_id"] = company_id
    result = client.table("script_refs").insert(payload).execute()
    return result.data[0]


def delete_reference(reference_id: str) -> None:
    client = _get_client()
    client.table("script_refs").delete().eq("id", reference_id).execute()


# ── 생성 로그(generated_logs) ────────────────────────────────────────────────

def save_log(company: str, appeal: str, script: str) -> dict:
    client = _get_client()
    result = (
        client.table("generated_logs")
        .insert({"company": company, "appeal": appeal, "script": script})
        .execute()
    )
    return result.data[0]


def list_logs(limit: int = 30) -> list[dict]:
    client = _get_client()
    result = (
        client.table("generated_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def delete_log(log_id: str) -> None:
    client = _get_client()
    client.table("generated_logs").delete().eq("id", log_id).execute()
