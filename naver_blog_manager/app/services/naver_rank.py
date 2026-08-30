"""네이버 VIEW(통합검색 내 블로그+카페) 순위 조회.

주의:
  네이버 검색결과 페이지의 실제 HTML 클래스명은 자주(예고 없이) 바뀐다.
  그래서 특정 class 선택자에 의존하는 대신, "본문 영역(main_pack) 안에서 등장하는
  blog.naver.com / cafe.naver.com 링크를 등장 순서대로" 뽑는 방식을 기본 전략으로 쓴다.
  이 방식은 마크업이 바뀌어도 비교적 안정적으로 동작하지만, 만약 결과가 비거나
  이상하면 이 파일의 MAIN_CONTAINER_SELECTORS / EXCLUDE_SELECTORS 만 실제 페이지를
  보고 조정하면 된다.
"""
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from urllib.parse import quote, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from .. import config
from . import matcher

VIEW_SEARCH_URL = "https://search.naver.com/search.naver?query={query}&where=view"

# 검색 결과 본문을 담는 컨테이너로 알려진 id/class 후보 (우선순위 순)
MAIN_CONTAINER_SELECTORS = ["#main_pack", "div.api_subject_bx", "body"]
# 광고/파워링크 등 결과에서 제외할 영역
EXCLUDE_SELECTORS = ["[class*='power_link']", "[class*='ad_']", "[id*='power_link']"]


@dataclass
class RankItem:
    position: int
    content_type: str  # "blog" | "cafe"
    url: str
    blog_id: str
    title: str
    ownership: str = "other"
    matched_blog: object | None = None


def _normalize_key(url: str) -> str:
    """같은 글로 향하는 썸네일 링크/제목 링크를 하나로 묶기 위한 정규화 키."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{parsed.netloc}{path}"


def _is_excluded(tag: Tag) -> bool:
    for parent in tag.parents:
        if not isinstance(parent, Tag):
            continue
        classes = " ".join(parent.get("class", []))
        el_id = parent.get("id", "")
        if "power_link" in classes or "power_link" in el_id or "ad_" in classes:
            return True
    return False


def parse_view_html(html: str, top_n: int = config.TOP_N) -> list[RankItem]:
    """검색결과 HTML에서 상위 top_n개의 블로그/카페 글을 뽑아 RankItem 리스트로 반환."""
    soup = BeautifulSoup(html, "html.parser")

    container = None
    for sel in MAIN_CONTAINER_SELECTORS:
        found = soup.select_one(sel)
        if found is not None:
            container = found
            break
    if container is None:
        container = soup

    seen_keys: set[str] = set()
    items: list[RankItem] = []

    for a in container.find_all("a", href=True):
        href = a["href"]
        if "blog.naver.com" not in href and "cafe.naver.com" not in href:
            continue
        if _is_excluded(a):
            continue

        key = _normalize_key(href)
        if key in seen_keys:
            continue

        title = a.get_text(strip=True)
        if not title:
            # 썸네일 이미지 링크 등 텍스트 없는 앵커는 건너뛰고, 텍스트 있는 링크를 우선한다
            continue

        seen_keys.add(key)
        content_type = "cafe" if "cafe.naver.com" in href else "blog"
        blog_id = matcher.extract_identifier(href)

        items.append(
            RankItem(
                position=len(items) + 1,
                content_type=content_type,
                url=href,
                blog_id=blog_id,
                title=title,
            )
        )
        if len(items) >= top_n:
            break

    return items


async def fetch_view_html(keyword: str, timeout_ms: int = 15000) -> str:
    """Playwright(headless)로 VIEW 통합검색 결과 HTML을 가져온다."""
    # 지연 import: playwright가 설치되지 않은 환경(예: 유닛테스트만 도는 CI)에서도
    # 이 모듈의 parse_view_html 등은 문제없이 import/테스트 가능하게 하기 위함.
    from playwright.async_api import async_playwright

    url = VIEW_SEARCH_URL.format(query=quote(keyword))
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(user_agent=config.NAVER_USER_AGENT)
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            html = await page.content()
        finally:
            await browser.close()
    return html


async def check_keyword_rank(
    keyword: str, registered_blogs: list, top_n: int = config.TOP_N
) -> list[RankItem]:
    """키워드 하나를 조회해서 소유자까지 매칭된 RankItem 리스트를 반환."""
    html = await fetch_view_html(keyword)
    items = parse_view_html(html, top_n=top_n)
    for item in items:
        ownership, matched = matcher.match_ownership(item.blog_id, registered_blogs)
        item.ownership = ownership
        item.matched_blog = matched
    return items


async def check_keywords_with_delay(
    keywords: list[str], registered_blogs: list, top_n: int = config.TOP_N
) -> dict[str, list[RankItem]]:
    """여러 키워드를 순차 조회하되, 요청 사이에 랜덤 딜레이를 둬서 과도한 크롤링을 피한다."""
    results: dict[str, list[RankItem]] = {}
    for idx, kw in enumerate(keywords):
        if idx > 0:
            delay = random.uniform(config.MIN_REQUEST_DELAY_SEC, config.MAX_REQUEST_DELAY_SEC)
            await asyncio.sleep(delay)
        results[kw] = await check_keyword_rank(kw, registered_blogs, top_n=top_n)
    return results


def detect_dropouts(
    previous_items: list[RankItem], current_items: list[RankItem]
) -> list[RankItem]:
    """이전 조회에서는 TOP_N 안에 있던 '우리' 글인데, 이번 조회에는 없는 항목을 반환.

    반환된 RankItem은 previous_items에서 가져온 것으로, position은 '마지막으로 확인된 순위'다.
    """
    current_keys = {(item.blog_id, item.content_type) for item in current_items if item.blog_id}
    dropped = []
    for prev in previous_items:
        if prev.ownership == "other" or not prev.blog_id:
            continue
        key = (prev.blog_id, prev.content_type)
        if key not in current_keys:
            dropped.append(prev)
    return dropped
