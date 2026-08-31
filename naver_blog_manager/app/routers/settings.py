from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import openai_writer, secure_storage

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create(db: Session) -> models.Setting:
    setting = db.get(models.Setting, 1)
    if not setting:
        setting = models.Setting(id=1)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def _to_out(setting: models.Setting) -> schemas.SettingOut:
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
    )


@router.get("", response_model=schemas.SettingOut)
def get_settings(db: Session = Depends(get_db)):
    return _to_out(_get_or_create(db))


@router.put("/profile", response_model=schemas.SettingOut)
def update_profile(payload: schemas.SettingProfileIn, db: Session = Depends(get_db)):
    """업체 프로필만 갱신한다 (대시보드의 접이식 카드용) - AI 설정은 건드리지 않는다."""
    setting = _get_or_create(db)
    setting.business_name = payload.business_name
    setting.address = payload.address
    setting.phone = payload.phone
    setting.strengths = payload.strengths
    db.commit()
    db.refresh(setting)
    return _to_out(setting)


@router.put("/ai", response_model=schemas.SettingOut)
def update_ai(payload: schemas.SettingAiIn, db: Session = Depends(get_db)):
    """AI 관련 설정만 갱신한다 (설정 화면용) - 업체 프로필은 건드리지 않는다."""
    setting = _get_or_create(db)
    if payload.openai_api_key:  # 화면에 마스킹되어 오므로, 빈 값이면 기존 키를 그대로 유지
        setting.openai_api_key = secure_storage.protect(payload.openai_api_key)
    setting.openai_model = payload.openai_model
    setting.rank_check_interval_hours = payload.rank_check_interval_hours
    setting.custom_prompt = payload.custom_prompt
    db.commit()
    db.refresh(setting)
    return _to_out(setting)
