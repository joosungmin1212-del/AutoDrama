from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

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
    data = schemas.SettingOut.model_validate(setting)
    data.openai_api_key_set = bool(setting.openai_api_key)
    data.openai_api_key = ""  # 저장된 키 원문은 절대 프론트로 내려주지 않는다
    return data


@router.get("", response_model=schemas.SettingOut)
def get_settings(db: Session = Depends(get_db)):
    return _to_out(_get_or_create(db))


@router.put("", response_model=schemas.SettingOut)
def update_settings(payload: schemas.SettingIn, db: Session = Depends(get_db)):
    setting = _get_or_create(db)
    setting.business_name = payload.business_name
    setting.address = payload.address
    setting.phone = payload.phone
    setting.strengths = payload.strengths
    if payload.openai_api_key:  # 화면에 마스킹되어 오므로, 빈 값이면 기존 키를 그대로 유지
        setting.openai_api_key = payload.openai_api_key
    setting.openai_model = payload.openai_model
    setting.rank_check_interval_hours = payload.rank_check_interval_hours
    db.commit()
    db.refresh(setting)
    return _to_out(setting)
