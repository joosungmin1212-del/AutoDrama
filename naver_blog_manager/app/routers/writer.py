import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import naver_browser, openai_writer, secure_storage, writer_account

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
    # 같은 키워드로 매번 똑같은 템플릿(뻔한 스토리)이 나오지 않도록, 지난번에 이 키워드로
    # 생성했을 때 쓴 템플릿을 먼저 찾아 "이번엔 다른 걸로" 힌트를 넘긴다.
    keyword_obj = None
    if payload.keyword:
        keyword_obj = (
            db.query(models.Keyword).filter(models.Keyword.keyword == payload.keyword).first()
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
            avoid_template=keyword_obj.last_used_template if keyword_obj else None,
        )
    except openai_writer.WriterError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"OpenAI 호출 중 오류가 발생했습니다: {exc}")

    seo_check = openai_writer.compute_seo_check(
        generated.content, payload.keyword or payload.title
    )

    draft = models.Draft(
        title=payload.title,
        keyword_id=keyword_obj.id if keyword_obj else None,
        content=generated.content,
        hashtags=",".join(generated.hashtags),
        seo_meta=json.dumps(seo_check, ensure_ascii=False),
    )
    db.add(draft)
    if keyword_obj and generated.template_used:
        keyword_obj.last_used_template = generated.template_used
    db.commit()
    db.refresh(draft)

    return schemas.WriterGenerateOut(
        draft_id=draft.id,
        title=draft.title,
        content=draft.content,
        hashtags=generated.hashtags,
        seo_check=schemas.SeoCheck(**seo_check),
        template_used=generated.template_used,
        template_label=openai_writer.TEMPLATE_LABELS.get(generated.template_used, ""),
    )


@router.post("/send-to-naver", response_model=schemas.WriterSendOut)
async def send_to_naver(payload: schemas.WriterSendIn, db: Session = Depends(get_db)):
    draft = db.get(models.Draft, payload.draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="초안을 찾을 수 없습니다.")

    # 미리보기 화면에서 사용자가 내용을 고쳤을 수 있으므로, 그 최종본을 우선 사용한다
    # (안 보내면 서버에 저장된 원본 초안이 그대로 나가버려 수정한 게 반영되지 않는다).
    final_content = payload.content.strip() if payload.content.strip() else draft.content
    if not final_content:
        raise HTTPException(status_code=400, detail="보낼 내용이 비어 있습니다.")
    draft.content = final_content

    setting = _get_or_create_setting(db)
    target_blog = writer_account.resolve_writer_blog(db, setting, payload.writer_blog_id)
    if not target_blog or not target_blog.blog_id:
        raise HTTPException(
            status_code=400,
            detail="글쓰기 계정이 없습니다. 설정 화면 또는 블로그 관리에서 먼저 네이버 로그인을 해주세요.",
        )

    body_with_tags = final_content
    if draft.hashtags:
        tags = " ".join(h.strip() for h in draft.hashtags.split(",") if h.strip())
        body_with_tags = f"{body_with_tags}\n\n{tags}"

    try:
        await naver_browser.open_write_draft(target_blog.blog_id, draft.title, body_with_tags)
    except naver_browser.NaverAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"네이버 전송 중 오류가 발생했습니다: {exc}")

    draft.sent_to_naver_at = datetime.utcnow()
    # 이번에 실제로 쓴 계정을 "마지막 사용 계정"으로 기억해둔다 - 다음번엔 따로 고르지
    # 않아도 이 계정이 기본으로 선택된다("로그인했던 계정이 글쓰기 계정" 요구사항).
    setting.active_writer_blog_id = target_blog.blog_id
    db.commit()

    return schemas.WriterSendOut(
        success=True,
        message="네이버 블로그 글쓰기 화면에 초안을 채워넣었습니다. 브라우저 창에서 검토 후 직접 발행해주세요.",
    )
