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

# 네이버가 자동화 접근을 의심해 보안문자/차단 페이지를 돌려줄 때 흔히 등장하는 문구들.
# 이런 페이지에서는 "결과 0개"가 곧 "우리 글이 다 내려갔다"는 뜻이 아니므로 반드시 구분해야 한다.
_BLOCK_INDICATORS = [
    "자동입력 방지",
    "비정상적인 접근",
    "captcha",
    "보안문자",
    "이용에 불편을 드려",
    "잠시 후 다시 시도",
]


class NaverBlockError(RuntimeError):
    """네이버가 차단/보안문자 페이지를 돌려준 것으로 의심될 때 발생시킨다.

    이 경우 조회 결과를 DB에 저장하면 안 된다 - 잘못된 "0/7" 스냅샷이 남아서
    실제로는 내려가지 않은 글이 "이탈 발생"으로 잘못 표시될 수 있기 때문이다.
    """


def detect_block(html: str) -> bool:
    lowered = html.lower()
    return any(indicator.lower() in lowered for indicator in _BLOCK_INDICATORS)


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


async def _load_search_page(page, keyword: str, timeout_ms: int) -> str:
    """이미 열려있는 Playwright Page로 검색 결과 HTML을 가져온다 (브라우저 재사용용 저수준 함수)."""
    url = VIEW_SEARCH_URL.format(query=quote(keyword))
    # 주의: wait_until="networkidle"는 쓰지 않는다. 네이버 검색결과 페이지는 광고/로깅용
    # 백그라운드 요청이 끊임없이 발생해서 "네트워크가 완전히 조용해지는 시점"이 거의
    # 오지 않는다 - 그래서 매번 타임아웃으로 실패하고, 그러면 이 조회는 아예 저장되지
    # 않아 대시보드에 "확인 전"만 계속 남는다. 대신 DOM이 준비되면 바로 진행하고,
    # 본문 컨테이너가 나타날 때까지 짧게만 추가로 기다린다(안 나타나도 계속 진행).
    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    try:
        await page.wait_for_selector(", ".join(MAIN_CONTAINER_SELECTORS[:-1]), timeout=5000)
    except Exception:  # noqa: BLE001
        pass
    return await page.content()


async def fetch_view_html(keyword: str, page=None, timeout_ms: int = 20000) -> str:
    """VIEW 통합검색 결과 HTML을 가져온다.

    page를 넘기면 그 Page(=이미 떠 있는 브라우저)를 그대로 재사용한다. 키워드가 많을 때
    (예: "전체 순위 갱신") 매번 새 브라우저를 켰다 끄는 오버헤드를 없애기 위함이다.
    page를 안 넘기면 (예: 카드 하나만 순위 갱신) 이 함수가 알아서 브라우저를 켰다 끈다.
    """
    if page is not None:
        return await _load_search_page(page, keyword, timeout_ms)

    # 지연 import: playwright가 설치되지 않은 환경(예: 유닛테스트만 도는 CI)에서도
    # 이 모듈의 parse_view_html 등은 문제없이 import/테스트 가능하게 하기 위함.
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            new_page = await browser.new_page(user_agent=config.NAVER_USER_AGENT)
            return await _load_search_page(new_page, keyword, timeout_ms)
        finally:
            await browser.close()


async def check_keyword_rank(
    keyword: str, registered_blogs: list, top_n: int = config.TOP_N, page=None
) -> list[RankItem]:
    """키워드 하나를 조회해서 소유자까지 매칭된 RankItem 리스트를 반환.

    네이버가 차단/보안문자 페이지를 돌려준 것으로 의심되면 NaverBlockError를 발생시키고,
    이 경우 호출자는 (잘못된 0개 결과를 저장하는 대신) 저장을 건너뛰고 나중에 다시
    시도해야 한다. page를 넘기면 그 브라우저 Page를 재사용한다 (여러 키워드를 한 번에
    조회할 때 rank_service.py에서 브라우저 하나로 돌려쓰기 위함).
    """
    html = await fetch_view_html(keyword, page=page)
    if detect_block(html):
        raise NaverBlockError(
            f"'{keyword}' 조회 결과가 비정상적입니다 (네이버 차단/보안문자 페이지로 의심됨). "
            "잠시 후 다시 시도해주세요."
        )
    items = parse_view_html(html, top_n=top_n)
    for item in items:
        ownership, matched = matcher.match_ownership(item.blog_id, registered_blogs)
        item.ownership = ownership
        item.matched_blog = matched
    return items


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
