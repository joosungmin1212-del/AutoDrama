"""SQLAlchemy ORM 모델.

- RegisteredBlog: 우리 업체 공식 블로그 / 직원 블로그 / 체험단(서포터즈) 블로그를 한 테이블에서 role로 구분해 등록.
- Keyword: 사용자가 모니터링할 검색 키워드.
- RankCheck/RankResult: 키워드별 순위 조회 1회 실행 기록과, 그때 확인된 TOP7 각 항목.
- Alert: 이전 조회에는 있었는데 이번 조회에서 사라진 "우리 글"을 감지했을 때 생성되는 이탈 알림.
- Draft: AI가 생성한 블로그 글 초안.
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class BlogRole(str, enum.Enum):
    COMPANY = "company"  # 우리 업체 공식 블로그
    STAFF = "staff"  # 직원 개인 블로그
    EXPERIENCE = "experience"  # 체험단 / 서포터즈


class ContentType(str, enum.Enum):
    BLOG = "blog"
    CAFE = "cafe"


class Ownership(str, enum.Enum):
    OURS_COMPANY = "ours_company"
    OURS_STAFF = "ours_staff"
    OURS_EXPERIENCE = "ours_experience"
    PENDING_EXPERIENCE = "pending_experience"  # 체험단 의심 - 아직 사람이 확인 안 함
    OTHER = "other"  # 등록되지 않은 타 업체/타인 글


class ContentMatchDecision(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Setting(Base):
    """싱글턴 설정 레코드 (id=1 고정)."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    business_name: Mapped[str] = mapped_column(String(200), default="")
    address: Mapped[str] = mapped_column(String(300), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    strengths: Mapped[str] = mapped_column(Text, default="")  # 업체 강점/차별점 (프롬프트에 반영)
    openai_api_key: Mapped[str] = mapped_column(String(300), default="")
    openai_model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    rank_check_interval_hours: Mapped[int] = mapped_column(Integer, default=24)
    custom_prompt: Mapped[str] = mapped_column(Text, default="")  # 비어있으면 기본 프롬프트 사용
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RegisteredBlog(Base):
    __tablename__ = "registered_blogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))  # 직원 이름 / 체험단 닉네임 / "공식블로그"
    blog_url: Mapped[str] = mapped_column(String(500))
    blog_id: Mapped[str] = mapped_column(String(200), default="")  # blog_url에서 추출된 식별자
    role: Mapped[str] = mapped_column(String(20), default=BlogRole.STAFF.value)
    memo: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    rank_results: Mapped[list["RankResult"]] = relationship(back_populates="matched_blog")


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column(String(200), unique=True)
    category: Mapped[str] = mapped_column(String(50), default="")  # 메인/타겟질환/세부키워드 등 자유 라벨
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    memo: Mapped[str] = mapped_column(String(300), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)  # 대시보드 드래그앤드롭 순서
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    rank_checks: Mapped[list["RankCheck"]] = relationship(
        back_populates="keyword", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="keyword", cascade="all, delete-orphan"
    )


class RankCheck(Base):
    __tablename__ = "rank_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"))
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source: Mapped[str] = mapped_column(String(20), default="view")

    keyword: Mapped["Keyword"] = relationship(back_populates="rank_checks")
    results: Mapped[list["RankResult"]] = relationship(
        back_populates="rank_check", cascade="all, delete-orphan", order_by="RankResult.position"
    )


class RankResult(Base):
    __tablename__ = "rank_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rank_check_id: Mapped[int] = mapped_column(ForeignKey("rank_checks.id"))
    position: Mapped[int] = mapped_column(Integer)  # 1~7
    content_type: Mapped[str] = mapped_column(String(10), default=ContentType.BLOG.value)
    url: Mapped[str] = mapped_column(String(500), default="")
    blog_id: Mapped[str] = mapped_column(String(200), default="")
    title: Mapped[str] = mapped_column(String(500), default="")
    matched_blog_id_fk: Mapped[int | None] = mapped_column(
        ForeignKey("registered_blogs.id"), nullable=True
    )
    ownership: Mapped[str] = mapped_column(String(20), default=Ownership.OTHER.value)

    rank_check: Mapped["RankCheck"] = relationship(back_populates="results")
    matched_blog: Mapped["RegisteredBlog | None"] = relationship(back_populates="rank_results")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"))
    matched_blog_id_fk: Mapped[int | None] = mapped_column(
        ForeignKey("registered_blogs.id"), nullable=True
    )
    # 등록된 블로그가 아닌(체험단 자동/수동 확정) 글이 이탈한 경우엔 matched_blog_id_fk가
    # 없으므로, "어떤 블로그가 이탈했는지"를 다시 매칭하기 위해 blog_id 자체도 남겨둔다.
    # 나중에 같은 blog_id가 TOP7에 다시 나타나면 이 값으로 이 알림을 자동으로 해소한다.
    blog_id: Mapped[str] = mapped_column(String(200), default="")
    previous_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    keyword: Mapped["Keyword"] = relationship(back_populates="alerts")
    matched_blog: Mapped["RegisteredBlog | None"] = relationship()


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[str] = mapped_column(Text, default="")  # 콤마 구분
    seo_meta: Mapped[str] = mapped_column(Text, default="{}")  # JSON 문자열
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_to_naver_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    keyword: Mapped["Keyword | None"] = relationship()


class ContentMatch(Base):
    """등록되지 않은 블로그(주로 체험단)가 쓴 글인데, 제목에 우리 업체명/직원 이름이 나와서
    "우리 글일 수 있다"고 자동으로 걸린 후보. 사람이 한 번 맞음/아니오로 확정하면 그 뒤로는
    같은 글(post_key)이 다시 나와도 자동으로 같은 판정을 적용한다 - 순위가 오르내리거나
    한동안 TOP7에서 사라졌다 돌아와도 이 판정은 계속 유효하다.
    """

    __tablename__ = "content_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_key: Mapped[str] = mapped_column(String(300), unique=True)  # 예: "blog:blogid:logno"
    url: Mapped[str] = mapped_column(String(500), default="")
    title: Mapped[str] = mapped_column(String(500), default="")
    matched_text: Mapped[str] = mapped_column(String(200), default="")  # 어떤 이름/키워드에 걸렸는지
    decision: Mapped[str] = mapped_column(String(12), default=ContentMatchDecision.PENDING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
