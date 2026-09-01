from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import openai_writer, scheduler as scheduler_service, secure_storage, writer_account

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create(db: Session) -> models.Setting:
    setting = db.get(models.Setting, 1)
    if not setting:
        setting = models.Setting(id=1)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def _to_out(db: Session, setting: models.Setting) -> schemas.SettingOut:
    auto_names: list[str] = []
    if setting.business_name.strip():
        auto_names.append(setting.business_name.strip())
    staff_blogs = (
        db.query(models.RegisteredBlog)
        .filter(
            models.RegisteredBlog.role.in_(
                [models.BlogRole.STAFF.value, models.BlogRole.COMPANY.value]
            )
        )
        .all()
    )
    auto_names.extend(b.name.strip() for b in staff_blogs if b.name.strip())

    # 여기서는 writer_account.resolve_writer_blog()를 쓰지 않는다 - 그 함수는 "실제로
    # 이번에 어디로 보낼지"를 정하는 용도라 매칭되는 계정이 없으면 아무 계정이나(첫
    # 번째로 등록된 것) 대신 골라주는데, 그걸 "지금 활성 계정"인 것처럼 화면에 보여주면
    # 실제 저장된 값과 다른 걸 보여주는 셈이 된다(로그인은 했는데 아직 그 blog_id로
    # 등록된 블로그가 없는 순간처럼). 여기서는 그냥 저장된 값을 있는 그대로 보여주고,
    # 이름만 찾을 수 있으면 붙여준다.
    writer_accounts = writer_account.list_writer_accounts(db)
    active_blog_id = setting.active_writer_blog_id
    active_name = ""
    if active_blog_id:
        matched = next(
            (a for a in writer_accounts if a.blog_id.lower() == active_blog_id.lower()), None
        )
        active_name = matched.name if matched else ""

    return schemas.SettingOut(
        business_name=setting.business_name,
        address=setting.address,
        phone=setting.phone,
        strengths=setting.strengths,
        openai_model=setting.openai_model,
        rank_check_interval_hours=setting.rank_check_interval_hours,
        # 커스텀 프롬프트가 없으면 기본 프롬프트를 그대로 "현재 적용 중인 값"으로 보여준다
        # (사용자가 처음 프롬프트 화면을 열었을 때 빈 칸이 아니라 실제 기본값이 보이도록).
        custom_prompt=setting.custom_prompt or openai_writer.SYSTEM_PROMPT,
        default_prompt=openai_writer.SYSTEM_PROMPT,
        openai_api_key_set=bool(setting.openai_api_key),
        custom_watch_keywords=setting.custom_watch_keywords,
        auto_watch_names=auto_names,
        active_writer_blog_id=active_blog_id,
        active_writer_name=active_name,
    )


@router.get("", response_model=schemas.SettingOut)
def get_settings(db: Session = Depends(get_db)):
    return _to_out(db, _get_or_create(db))


@router.put("/profile", response_model=schemas.SettingOut)
def update_profile(payload: schemas.SettingProfileIn, db: Session = Depends(get_db)):
    """업체 프로필만 갱신한다 (대시보드의 접이식 카드용) - AI 설정은 건드리지 않는다."""
    setting = _get_or_create(db)
    setting.business_name = payload.business_name
    setting.address = payload.address
    setting.phone = payload.phone
    setting.strengths = payload.strengths
    setting.custom_watch_keywords = payload.custom_watch_keywords
    db.commit()
    db.refresh(setting)
    return _to_out(db, setting)


@router.put("/active-writer", response_model=schemas.SettingOut)
def set_active_writer(payload: schemas.ActiveWriterIn, db: Session = Depends(get_db)):
    """로그인 직후 등록한 계정을 바로 "지금 쓸 글쓰기 계정"으로 지정한다."""
    setting = _get_or_create(db)
    setting.active_writer_blog_id = payload.blog_id.strip()
    db.commit()
    db.refresh(setting)
    return _to_out(db, setting)


@router.put("/ai", response_model=schemas.SettingOut)
def update_ai(payload: schemas.SettingAiIn, db: Session = Depends(get_db)):
    """AI 관련 설정만 갱신한다 (설정 화면용) - 업체 프로필은 건드리지 않는다."""
    setting = _get_or_create(db)
    if payload.openai_api_key:  # 화면에 마스킹되어 오므로, 빈 값이면 기존 키를 그대로 유지
        setting.openai_api_key = secure_storage.protect(payload.openai_api_key)
    setting.openai_model = payload.openai_model
    interval_changed = setting.rank_check_interval_hours != payload.rank_check_interval_hours
    setting.rank_check_interval_hours = payload.rank_check_interval_hours
    setting.custom_prompt = payload.custom_prompt
    db.commit()
    db.refresh(setting)

    if interval_changed:
        # 재시작 없이 바로 반영되도록 실행 중인 스케줄러 주기도 함께 바꾼다
        # (예전에는 이 값이 저장만 되고 실제로는 안 쓰여서 항상 24시간 고정이었다).
        scheduler_service.reschedule(setting.rank_check_interval_hours)

    return _to_out(db, setting)
