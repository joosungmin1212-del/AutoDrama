"""API 요청/응답 Pydantic 스키마."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Settings ----------
class SettingIn(BaseModel):
    business_name: str = ""
    address: str = ""
    phone: str = ""
    strengths: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    rank_check_interval_hours: int = 24


class SettingOut(SettingIn):
    # 프론트에 그대로 키를 노출하면 위험하니 마스킹된 값만 내려준다.
    openai_api_key_set: bool = False

    model_config = ConfigDict(from_attributes=True)


# ---------- Registered Blog ----------
class RegisteredBlogIn(BaseModel):
    name: str
    blog_url: str
    role: str = Field(pattern="^(company|staff|experience)$", default="staff")
    memo: str = ""


class RegisteredBlogOut(BaseModel):
    id: int
    name: str
    blog_url: str
    blog_id: str
    role: str
    memo: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Keyword ----------
class KeywordIn(BaseModel):
    keyword: str
    category: str = ""
    memo: str = ""


class KeywordOut(BaseModel):
    id: int
    keyword: str
    category: str
    active: bool
    memo: str
    sort_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KeywordReorderIn(BaseModel):
    order: list[int]  # 위에서부터 원하는 순서대로 나열한 키워드 id 목록


# ---------- Rank ----------
class RankResultOut(BaseModel):
    position: int
    content_type: str
    url: str
    blog_id: str
    title: str
    ownership: str
    matched_blog_name: str | None = None


class RankCheckOut(BaseModel):
    checked_at: datetime | None = None
    results: list[RankResultOut] = []


class AlertOut(BaseModel):
    id: int
    keyword_id: int
    keyword: str
    matched_blog_name: str | None
    previous_position: int | None
    detected_at: datetime
    resolved: bool

    model_config = ConfigDict(from_attributes=True)


class StaffPresenceOut(BaseModel):
    id: int
    name: str
    present: bool


class KeywordSummaryOut(BaseModel):
    """대시보드 카드 1개에 필요한 모든 정보."""

    id: int
    keyword: str
    category: str
    memo: str
    active: bool
    sort_order: int
    last_checked_at: datetime | None
    our_count: int  # TOP7 중 우리(회사+직원+체험단, 확정된 것만) 글 개수
    total_slots: int  # 항상 7 (TOP_N)
    slots: list[dict]  # [{position, ownership, owner_name, owner_blog_id, title, url}] 1~7
    has_open_alert: bool
    staff_presence: list[StaffPresenceOut]  # 직원별로 이 키워드 TOP7에 있는지 여부
    experience_confirmed_count: int  # 확정된 체험단 글 개수
    experience_pending_count: int  # 아직 확인 안 한 "체험단 의심" 개수

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    monitored_keywords: int
    our_total: int
    our_slots_total: int  # monitored_keywords * 7
    staff_exposure_count: int
    experience_exposure_count: int
    staff_breakdown: dict[str, int]  # {직원이름: 개수}
    experience_breakdown: dict[str, int]
    open_alert_count: int
    pending_content_match_count: int  # 전체 키워드에서 아직 확인 안 한 체험단 후보 개수


class DashboardResponse(BaseModel):
    stats: DashboardStats
    keywords: list[KeywordSummaryOut]


# ---------- Content Match (체험단 자동 감지) ----------
class ContentMatchOut(BaseModel):
    id: int
    post_key: str
    url: str
    title: str
    matched_text: str
    decision: str
    created_at: datetime
    decided_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ContentMatchDecisionIn(BaseModel):
    decision: str = Field(pattern="^(confirmed|rejected)$")


# ---------- Writer ----------
class WriterGenerateIn(BaseModel):
    title: str
    keyword: str | None = None
    extra_request: str = ""


class SeoCheck(BaseModel):
    length: int
    keyword_count: int
    length_ok: bool
    keyword_count_ok: bool
    subheading_count: int


class WriterGenerateOut(BaseModel):
    draft_id: int
    title: str
    content: str
    hashtags: list[str]
    seo_check: SeoCheck


class WriterSendIn(BaseModel):
    draft_id: int


class WriterSendOut(BaseModel):
    success: bool
    message: str


# ---------- Naver Auth ----------
class NaverAuthStatus(BaseModel):
    logged_in: bool
    checked_at: datetime | None = None
    message: str = ""
