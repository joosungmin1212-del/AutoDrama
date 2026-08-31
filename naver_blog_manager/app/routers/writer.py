import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import naver_browser, openai_writer, secure_storage

router = APIRouter(prefix="/api/writer", tags=["writer"])


def _get_or_create_setting(db: Session) -> models.Setting:
    setting = db.get(models.Setting, 1)
    if not setting:
        setting = models.Setting(id=1)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.post("/generate", response_model=schemas.WriterGenerateOut)
def generate(payload: schemas.WriterGenerateIn, db: Session = Depends(get_db)):
    setting = _get_or_create_setting(db)
    profile = openai_writer.BusinessProfile(
        business_name=setting.business_name,
        address=setting.address,
        phone=setting.phone,
        strengths=setting.strengths,
    )
    try:
        generated = openai_writer.generate_post(
            api_key=secure_storage.unprotect(setting.openai_api_key),
            model=setting.openai_model,
            title=payload.title,
            keyword=payload.keyword,
            extra_request=payload.extra_request,
            profile=profile,
            system_prompt=setting.custom_prompt or None,
        )
    except openai_writer.WriterError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"OpenAI 호출 중 오류가 발생했습니다: {exc}")

    seo_check = openai_writer.compute_seo_check(
        generated.content, payload.keyword or payload.title
    )

    keyword_obj = None
    if payload.keyword:
        keyword_obj = (
            db.query(models.Keyword).filter(models.Keyword.keyword == payload.keyword).first()
        )

    draft = models.Draft(
        title=payload.title,
        keyword_id=keyword_obj.id if keyword_obj else None,
        content=generated.content,
        hashtags=",".join(generated.hashtags),
        seo_meta=json.dumps(seo_check, ensure_ascii=False),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    return schemas.WriterGenerateOut(
        draft_id=draft.id,
        title=draft.title,
        content=draft.content,
        hashtags=generated.hashtags,
        seo_check=schemas.SeoCheck(**seo_check),
    )


@router.post("/send-to-naver", response_model=schemas.WriterSendOut)
async def send_to_naver(payload: schemas.WriterSendIn, db: Session = Depends(get_db)):
    draft = db.get(models.Draft, payload.draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="초안을 찾을 수 없습니다.")

    company_blog = (
        db.query(models.RegisteredBlog)
        .filter(models.RegisteredBlog.role == models.BlogRole.COMPANY.value)
        .first()
    )
    if not company_blog or not company_blog.blog_id:
        raise HTTPException(
            status_code=400,
            detail="공식 블로그가 등록되어 있지 않습니다. 블로그 관리 화면에서 먼저 등록해주세요.",
        )

    body_with_tags = draft.content
    if draft.hashtags:
        tags = " ".join(h.strip() for h in draft.hashtags.split(",") if h.strip())
        body_with_tags = f"{body_with_tags}\n\n{tags}"

    try:
        await naver_browser.open_write_draft(company_blog.blog_id, draft.title, body_with_tags)
    except naver_browser.NaverAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"네이버 전송 중 오류가 발생했습니다: {exc}")

    draft.sent_to_naver_at = datetime.utcnow()
    db.commit()

    return schemas.WriterSendOut(
        success=True,
        message="네이버 블로그 글쓰기 화면에 초안을 채워넣었습니다. 브라우저 창에서 검토 후 직접 발행해주세요.",
    )
