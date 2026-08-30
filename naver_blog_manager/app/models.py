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
    OTHER = "other"  # 등록되지 않은 타 업체/타인 글


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
