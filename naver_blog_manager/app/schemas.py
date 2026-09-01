"""API 요청/응답 Pydantic 스키마."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Settings ----------
class SettingProfileIn(BaseModel):
    """업체 프로필만 수정 (대시보드의 접이식 카드에서 저장)."""

    business_name: str = ""
    address: str = ""
    phone: str = ""
    strengths: str = ""
    custom_watch_keywords: str = ""  # 체험단 자동 확인용 추가 감시 키워드 (쉼표/줄바꿈 구분)


class SettingAiIn(BaseModel):
    """AI/글쓰기 관련 설정만 수정 (설정 화면에서 저장)."""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    rank_check_interval_hours: int = Field(default=24, ge=1)
    custom_prompt: str = ""  # 비워두면 기본 프롬프트 유지


class SettingOut(BaseModel):
    business_name: str = ""
    address: str = ""
    phone: str = ""
    strengths: str = ""
    openai_model: str = "gpt-4o-mini"
    rank_check_interval_hours: int = 24
    custom_prompt: str = ""  # 현재 적용 중인 프롬프트 (커스텀 없으면 기본값이 그대로 옴)
    default_prompt: str = ""  # "기본값으로 되돌리기" 버튼용 - 항상 원래 기본 프롬프트
    # 프론트에 API 키 원문을 그대로 내려주면 위험하니, 설정 여부만 알려준다.
    openai_api_key_set: bool = False
    custom_watch_keywords: str = ""  # 원문 그대로(설정 화면 textarea에 채워넣기용)
    # 업체명 + 등록된 직원/공식블로그 이름 - 사용자가 직접 입력 안 해도 이미 자동으로
    # 감시되고 있는 이름들을 "확인"할 수 있게 보여주기 위한 목록 (읽기 전용, 여기서 수정 불가).
    auto_watch_names: list[str] = []


# ---------- Registered Blog ----------
class RegisteredBlogIn(BaseModel):
    name: str
    blog_url: str
    role: str = Field(pattern="^(company|staff|experience|competitor)$", default="staff")
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
    blog_id: str = ""  # 등록 안 된 블로그(체험단)의 이탈이면 이름 대신 이 값으로 표시
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
    # 계정(블로그ID) 기준 노출 개수 - [{blog_id, name, count}], 많이 나온 순.
    # "모니터링 키워드" 카드 옆에 "우리 계정들이 지금 TOP7에 합쳐서 몇 개 있는지" 보여주는 데 씀.
    account_breakdown: list[dict] = []
    open_alert_count: int
    pending_content_match_count: int  # 전체 키워드에서 아직 확인 안 한 체험단 후보 개수


class DashboardResponse(BaseModel):
    stats: DashboardStats
    keywords: list[KeywordSummaryOut]
    # 최근 N일간 "그 날의 마지막 순위체크" 기준 전체 키워드 합산 TOP7 점유 추이.
    # [{date: "2026-08-20", our_total: 5}, ...] 날짜 오름차순.
    trend: list[dict] = []


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


class ContentMatchManualIn(BaseModel):
    """대시보드에서 TOP7 글 하나를 직접 확정/거절할 때 (제목에 이름이 없어 자동 감지가 놓친 경우)."""

    url: str
    title: str = ""
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
    # 미리보기에서 사용자가 고친 내용을 그대로 네이버로 보내기 위함 - 이게 없으면 화면에서
    # 아무리 수정해도 서버에 저장된(=AI가 처음 생성한) 원본 초안이 그대로 전송돼버린다.
    content: str = ""
    # 공식 블로그(계정)를 여러 개 등록해둔 경우 어디로 보낼지 지정 (RegisteredBlog.id).
    # 안 주면(0/None) 기존처럼 등록된 공식 블로그 중 하나를 그대로 쓴다(1개만 있을 때 기존 동작 유지).
    company_blog_id: int | None = None


class WriterSendOut(BaseModel):
    success: bool
    message: str


# ---------- Naver Auth ----------
class NaverAuthStatus(BaseModel):
    logged_in: bool
    checked_at: datetime | None = None
    message: str = ""


class NaverAccountOut(BaseModel):
    """공식 블로그(계정)별 네이버 로그인 상태 - 계정 전환 UI(블로그 관리 화면)용."""

    blog_pk: int  # RegisteredBlog.id
    name: str
    blog_id: str
    logged_in: bool
    # 이 계정 전용 세션이 따로 있는지(true) 아니면 기본 세션을 자동으로 쓰고 있는지(false).
    has_dedicated_session: bool
