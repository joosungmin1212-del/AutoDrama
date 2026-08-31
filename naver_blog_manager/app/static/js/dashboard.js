const OWNERSHIP_LABEL = {
  ours_staff: "직원",
  ours_experience: "체험단",
  ours_company: "공식블로그",
  pending_experience: "체험단 의심(확인필요)",
  other: "타업체",
  empty: "미노출",
};

// 계정(등록된 블로그)별로 서로 다른 색을 주기 위한 팔레트 - "직원" 등 우리 소유 슬롯이
// 전부 초록색 하나로만 표시되면, TOP7 안에 우리 계정이 여러 개(예: 성민본계정,
// 성민부계정) 섞여 있어도 어떤 자리가 어느 계정인지 구별이 안 되는 문제가 실제로
// 있었다. owner_blog_id(등록된 블로그의 고유 id)를 기준으로 항상 같은 계정은 항상 같은
// 색이 나오도록 해시로 팔레트에서 고른다 - 대시보드 전체에서 일관되게 유지된다.
const ACCOUNT_COLOR_PALETTE = [
  "#16a34a", // green
  "#2563eb", // blue
  "#7c3aed", // violet
  "#db2777", // pink
  "#ea580c", // orange
  "#0891b2", // cyan
  "#65a30d", // lime
  "#c026d3", // fuchsia
  "#dc2626", // red
  "#0d9488", // teal
];

function accountColorFor(key) {
  if (key === null || key === undefined || key === "") return null;
  const str = String(key);
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) >>> 0;
  }
  return ACCOUNT_COLOR_PALETTE[hash % ACCOUNT_COLOR_PALETTE.length];
}

// "우리 소유"(직원/체험단/공식블로그) 슬롯에만 계정별 색을 입힌다 - 타업체/미노출/체험단
// 의심(미확정) 자리는 여전히 역할 기반 회색/점선/노란색을 그대로 쓴다.
function accountColorForSlot(s) {
  if (!s || !String(s.ownership || "").startsWith("ours_")) return null;
  return accountColorFor(s.owner_blog_id ?? s.owner_name);
}

// ownership이 아직 "other"라도 owner_role로 등록된 계정이면(체험단/경쟁업체) 그냥 모르는
// "타업체"와는 다르게 라벨을 구별해준다. 단, 등록해뒀다고 해서 이 글까지 자동으로 확정된
// 건 아니다 - 같은 체험단 계정이 다른 키워드에선 완전히 다른 업체 글을 쓸 수 있어서,
// 신원(누구 계정인지)과 이 글의 판정은 따로 본다.
function ownershipLabel(s) {
  if (s.ownership === "other" && s.owner_role === "competitor") return "확인된 타업체";
  if (s.ownership === "other" && s.owner_role === "experience") return "등록된 체험단(이 글 확인 필요)";
  return OWNERSHIP_LABEL[s.ownership] || s.ownership;
}

function accountColorCss(s) {
  const color = accountColorForSlot(s);
  return color ? `background:${color}; border-color:${color}; color:#fff;` : "";
}

function rankDotStyle(s) {
  const css = accountColorCss(s);
  return css ? ` style="${css}"` : "";
}

let dashboardData = { stats: null, keywords: [] };
let currentFilter = "all";
let searchText = "";
let draggedKeywordId = null;

async function loadDashboard() {
  try {
    dashboardData = await apiFetch("/api/dashboard/summary");
  } catch (e) {
    showToast(e.message, true);
    return;
  }
  renderStats(dashboardData.stats);
  renderFilterTabs(dashboardData.keywords, dashboardData.stats);
  renderKeywordList();
}

function renderStats(stats) {
  document.getElementById("stat-monitored").textContent = stats.monitored_keywords;
  document.getElementById(
    "stat-monitored-sub"
  ).textContent = `개 등록 관리 중 · 이탈 알림 ${stats.open_alert_count}건`;

  const btn = document.getElementById("content-match-btn");
  btn.textContent = `🕵️ 체험단 확인 필요 (${stats.pending_content_match_count})`;
  btn.classList.toggle("filter-tab--alert", stats.pending_content_match_count > 0);

  renderSummaryBanner(stats);
}

// ---------- 지금 확인해야 할 것 요약 배너 ----------
function renderSummaryBanner(stats) {
  const el = document.getElementById("summary-banner");
  // 업데이트 직후 브라우저에 옛 HTML이 캐시돼 있는 등, 이 요소가 아직 없는 화면일 수도
  // 있다 - 여기서 조용히 넘어가야 다른 렌더링(키워드 목록 등)까지 멈추지 않는다.
  if (!el) return;
  const chips = [];

  if (stats.open_alert_count > 0) {
    chips.push(
      `<button class="summary-banner__chip summary-banner__chip--danger" id="summary-goto-alert">⚠ 이탈 알림 ${stats.open_alert_count}건</button>`
    );
  }
  if (stats.pending_content_match_count > 0) {
    chips.push(
      `<button class="summary-banner__chip summary-banner__chip--warn" id="summary-open-content-match">🕵️ 체험단 확인 필요 ${stats.pending_content_match_count}건</button>`
    );
  }

  if (chips.length === 0) {
    el.className = "summary-banner summary-banner--ok";
    el.innerHTML = "✅ 지금 확인이 필요한 알림이 없습니다.";
    return;
  }

  el.className = "summary-banner summary-banner--alert";
  el.innerHTML = `<span class="summary-banner__label">지금 확인해야 할 것</span>${chips.join("")}`;

  const alertChip = document.getElementById("summary-goto-alert");
  if (alertChip) {
    alertChip.addEventListener("click", () => {
      currentFilter = "alert";
      renderFilterTabs(dashboardData.keywords, dashboardData.stats);
      renderKeywordList();
      document.getElementById("kw-list").scrollIntoView({ behavior: "smooth" });
    });
  }
  const contentMatchChip = document.getElementById("summary-open-content-match");
  if (contentMatchChip) {
    contentMatchChip.addEventListener("click", () => {
      document.getElementById("content-match-modal").hidden = false;
      loadContentMatchModal();
    });
  }
}

function pct(n, total) {
  if (!total) return 0;
  return Math.round((n / total) * 100);
}

function renderFilterTabs(keywords, stats) {
  const container = document.getElementById("filter-tabs");
  const categories = [...new Set(keywords.map((k) => k.category).filter(Boolean))];

  let html = `<button class="filter-tab ${currentFilter === "all" ? "active" : ""}" data-filter="all">전체</button>`;
  for (const cat of categories) {
    html += `<button class="filter-tab ${currentFilter === cat ? "active" : ""}" data-filter="${escapeHtml(
      cat
    )}">${escapeHtml(cat)}</button>`;
  }
  html += `<button class="filter-tab filter-tab--alert ${
    currentFilter === "alert" ? "active" : ""
  }" data-filter="alert">이탈 알림 (${stats.open_alert_count})</button>`;

  container.innerHTML = html;
  container.querySelectorAll(".filter-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentFilter = btn.dataset.filter;
      renderFilterTabs(dashboardData.keywords, dashboardData.stats);
      renderKeywordList();
    });
  });

  updateReorderHint();
}

function isReorderEnabled() {
  return currentFilter === "all" && !searchText.trim();
}

function updateReorderHint() {
  const hint = document.getElementById("reorder-hint");
  hint.hidden = !isReorderEnabled();
}

function renderKeywordList() {
  const listEl = document.getElementById("kw-list");
  let keywords = dashboardData.keywords;

  if (currentFilter === "alert") {
    keywords = keywords.filter((k) => k.has_open_alert);
  } else if (currentFilter !== "all") {
    keywords = keywords.filter((k) => k.category === currentFilter);
  }
  if (searchText.trim()) {
    const q = searchText.trim().toLowerCase();
    keywords = keywords.filter((k) => k.keyword.toLowerCase().includes(q));
  }

  updateReorderHint();

  if (keywords.length === 0) {
    listEl.innerHTML = `<div class="empty-state">등록된 키워드가 없습니다. 우측 상단 "+ 키워드 추가"로 시작해보세요.</div>`;
    return;
  }

  const draggable = isReorderEnabled();
  listEl.innerHTML = keywords.map((k) => renderKeywordCard(k, draggable)).join("");

  listEl.querySelectorAll("[data-action='refresh']").forEach((btn) => {
    btn.addEventListener("click", () => refreshKeyword(Number(btn.dataset.id), btn));
  });
  listEl.querySelectorAll("[data-action='delete']").forEach((btn) => {
    btn.addEventListener("click", () => deleteKeyword(Number(btn.dataset.id), btn.dataset.keyword));
  });
  listEl.querySelectorAll("[data-action='write']").forEach((btn) => {
    btn.addEventListener("click", () => {
      window.location.href = `/writer?keyword=${encodeURIComponent(btn.dataset.keyword)}`;
    });
  });
  listEl.querySelectorAll("[data-action='view-detail']").forEach((el) => {
    el.addEventListener("click", () => openKeywordDetail(Number(el.dataset.id)));
  });
  listEl.querySelectorAll("[data-action='edit']").forEach((btn) => {
    btn.addEventListener("click", () => openEditKeywordModal(Number(btn.dataset.id)));
  });

  if (draggable) {
    setupDragAndDrop(listEl);
  }
}

function renderEmployeeChecklist(k) {
  const badges = k.staff_presence.map((s) => {
    // 이 계정이 실제로 TOP7에 있으면(present), 오른쪽 순위뱃지와 같은 색을 여기 태그에도
    // 입혀서 "이 태그 = 저 색깔 동그라미"라는 게 바로 보이게 한다 (구별용 범례 역할).
    const color = s.present ? accountColorFor(s.id) : null;
    const style = color ? ` style="background:${color}22; color:${color}; border-color:${color};"` : "";
    return `<span class="emp-badge ${s.present ? "emp-badge--yes" : "emp-badge--no"}"${style}>${escapeHtml(
      s.name
    )} ${s.present ? "✓" : "✗"}</span>`;
  });

  if (k.experience_confirmed_count > 0) {
    badges.push(`<span class="emp-badge emp-badge--experience">체험단 ${k.experience_confirmed_count}</span>`);
  }
  if (k.experience_pending_count > 0) {
    badges.push(
      `<span class="emp-badge emp-badge--pending" data-action="open-content-match" title="클릭해서 확인하기">체험단 의심 ${k.experience_pending_count} ?</span>`
    );
  }

  return `<div class="emp-checklist">${badges.join("")}</div>`;
}

function renderKeywordCard(k, draggable) {
  const pctVal = pct(k.our_count, k.total_slots);
  const alertClass = k.has_open_alert ? "kw-card--alert" : "";
  const dots = k.slots
    .map((s) => {
      const label = s.title ? `${ownershipLabel(s)}${s.owner_name ? " · " + s.owner_name : ""}\n${s.title}` : "미노출";
      return `<span class="rank-dot rank-dot--${s.ownership}"${rankDotStyle(s)} title="${escapeHtml(label)}">${s.position}</span>`;
    })
    .join("");

  return `
  <div class="kw-card ${alertClass}" data-id="${k.id}" ${draggable ? 'draggable="true"' : ""}>
    ${draggable ? '<span class="drag-handle" title="드래그해서 순서 바꾸기">⠿</span>' : ""}
    <div class="kw-ratio-box">${k.our_count}/${k.total_slots}</div>
    <div class="kw-card__main">
      <div class="kw-card__title-row">
        <span class="kw-title kw-title--clickable" data-action="view-detail" data-id="${k.id}" title="클릭해서 TOP7 글 목록 보기">${escapeHtml(k.keyword)} 🔍</span>
        ${k.category ? `<span class="badge badge-category">${escapeHtml(k.category)}</span>` : ""}
        ${k.has_open_alert ? `<span class="badge badge-alert">⚠ 이탈 발생</span>` : ""}
      </div>
      <div class="kw-card__meta">최근 확인: ${formatDateTime(k.last_checked_at)}</div>
      ${k.memo ? `<div class="kw-card__memo">${escapeHtml(k.memo)}</div>` : ""}
      ${renderEmployeeChecklist(k)}
    </div>
    <div class="kw-card__right">
      <div>
        <div class="rank-dots" data-action="view-detail" data-id="${k.id}" title="클릭해서 TOP7 글 목록 보기">${dots}</div>
        <div class="kw-ratio-text">TOP7 점유: ${k.our_count}/${k.total_slots} (${pctVal}%)</div>
      </div>
      <button class="icon-btn" data-action="refresh" data-id="${k.id}" title="순위 갱신">↻</button>
      <button class="btn-write" data-action="write" data-keyword="${escapeHtml(k.keyword)}">✎ 글 작성</button>
      <button class="icon-btn" data-action="edit" data-id="${k.id}" title="키워드/카테고리/메모 수정">🖊</button>
      <button class="icon-btn icon-btn--danger" data-action="delete" data-id="${k.id}" data-keyword="${escapeHtml(
        k.keyword
      )}" title="삭제">🗑</button>
    </div>
  </div>`;
}

// ---------- 드래그앤드롭 순서 조절 ----------
function setupDragAndDrop(listEl) {
  const cards = [...listEl.querySelectorAll(".kw-card[draggable='true']")];

  cards.forEach((card) => {
    card.addEventListener("dragstart", () => {
      draggedKeywordId = card.dataset.id;
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
      cards.forEach((c) => c.classList.remove("drag-over"));
    });
    card.addEventListener("dragover", (e) => {
      e.preventDefault();
      if (card.dataset.id === draggedKeywordId) return;
      cards.forEach((c) => c.classList.remove("drag-over"));
      card.classList.add("drag-over");
    });
    card.addEventListener("drop", async (e) => {
      e.preventDefault();
      card.classList.remove("drag-over");
      const draggedEl = listEl.querySelector(`.kw-card[data-id="${draggedKeywordId}"]`);
      if (!draggedEl || draggedEl === card) return;

      const cardsNow = [...listEl.querySelectorAll(".kw-card")];
      const fromIndex = cardsNow.indexOf(draggedEl);
      const toIndex = cardsNow.indexOf(card);
      if (fromIndex < toIndex) {
        card.after(draggedEl);
      } else {
        card.before(draggedEl);
      }

      const newOrder = [...listEl.querySelectorAll(".kw-card")].map((c) => Number(c.dataset.id));
      try {
        await apiFetch("/api/keywords/reorder", {
          method: "POST",
          body: JSON.stringify({ order: newOrder }),
        });
      } catch (err) {
        showToast(err.message, true);
        await loadDashboard();
      }
    });
  });
}

async function refreshKeyword(id, btn) {
  btn.textContent = "…";
  btn.disabled = true;
  try {
    await apiFetch(`/api/keywords/${id}/refresh`, { method: "POST" });
    showToast("순위를 갱신했습니다.");
  } catch (e) {
    showToast(e.message, true);
  } finally {
    await loadDashboard();
  }
}

async function deleteKeyword(id, keyword) {
  if (!confirm(`"${keyword}" 키워드를 삭제할까요? 조회 이력도 함께 삭제됩니다.`)) return;
  try {
    await apiFetch(`/api/keywords/${id}`, { method: "DELETE" });
    showToast("키워드를 삭제했습니다.");
    await loadDashboard();
  } catch (e) {
    showToast(e.message, true);
  }
}

// 키워드 추가 모달은 "수정"에도 그대로 재사용한다 (editingKeywordId가 있으면 PUT, 없으면 POST).
let editingKeywordId = null;

function openEditKeywordModal(keywordId) {
  const k = dashboardData.keywords.find((kw) => kw.id === keywordId);
  if (!k) return;
  editingKeywordId = keywordId;

  const form = document.getElementById("add-keyword-form");
  form.keyword.value = k.keyword;
  form.category.value = k.category || "";
  form.memo.value = k.memo || "";

  document.getElementById("add-keyword-title").textContent = "키워드 수정";
  document.getElementById("add-keyword-submit").textContent = "저장";
  document.getElementById("add-keyword-modal").hidden = false;
}

function setupAddKeywordModal() {
  const modal = document.getElementById("add-keyword-modal");
  const openBtn = document.getElementById("add-keyword-btn");
  const cancelBtn = document.getElementById("add-keyword-cancel");
  const form = document.getElementById("add-keyword-form");

  function resetToAddMode() {
    editingKeywordId = null;
    form.reset();
    document.getElementById("add-keyword-title").textContent = "키워드 추가";
    document.getElementById("add-keyword-submit").textContent = "추가";
  }

  openBtn.addEventListener("click", () => {
    resetToAddMode();
    modal.hidden = false;
  });
  cancelBtn.addEventListener("click", () => {
    modal.hidden = true;
    resetToAddMode();
  });
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.hidden = true;
      resetToAddMode();
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const payload = {
      keyword: fd.get("keyword"),
      category: fd.get("category") || "",
      memo: fd.get("memo") || "",
    };
    try {
      if (editingKeywordId !== null) {
        await apiFetch(`/api/keywords/${editingKeywordId}`, { method: "PUT", body: JSON.stringify(payload) });
        showToast("키워드를 수정했습니다.");
      } else {
        await apiFetch("/api/keywords", { method: "POST", body: JSON.stringify(payload) });
        showToast("키워드를 추가했습니다.");
      }
      modal.hidden = true;
      resetToAddMode();
      await loadDashboard();
      await loadOnboarding();
    } catch (e) {
      showToast(e.message, true);
    }
  });
}

// ---------- 체험단 확인 모달 ----------
async function loadContentMatchModal() {
  const listEl = document.getElementById("content-match-list");
  listEl.innerHTML = `<div class="empty-state">불러오는 중...</div>`;
  let matches;
  try {
    matches = await apiFetch("/api/content-matches?status=pending");
  } catch (e) {
    listEl.innerHTML = `<div class="empty-state">${escapeHtml(e.message)}</div>`;
    return;
  }

  if (matches.length === 0) {
    listEl.innerHTML = `<div class="empty-state">확인할 게 없습니다. 새로 걸리면 여기 나타납니다.</div>`;
    return;
  }

  listEl.innerHTML = matches
    .map(
      (m) => `
    <div class="content-match-item" data-id="${m.id}">
      <div class="content-match-item__title">${escapeHtml(m.title)}</div>
      <div class="content-match-item__meta">
        "${escapeHtml(m.matched_text)}" 이(가) 제목에 보여서 후보로 잡혔어요 ·
        <a href="${escapeHtml(m.url)}" target="_blank" rel="noopener">글 보러가기 ↗</a>
      </div>
      <div class="content-match-item__actions">
        <button class="btn btn-primary" data-decide="confirmed" data-id="${m.id}" style="padding:6px 14px;">✓ 우리 글 맞음</button>
        <button class="btn btn-outline" data-decide="rejected" data-id="${m.id}" style="padding:6px 14px;">아니오</button>
      </div>
    </div>`
    )
    .join("");

  listEl.querySelectorAll("[data-decide]").forEach((btn) => {
    btn.addEventListener("click", () => decideContentMatch(Number(btn.dataset.id), btn.dataset.decide));
  });
}

async function decideContentMatch(id, decision) {
  try {
    await apiFetch(`/api/content-matches/${id}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    });
    showToast(decision === "confirmed" ? "체험단 글로 확정했습니다." : "우리 글이 아닌 것으로 처리했습니다.");
    await loadContentMatchModal();
    await loadDashboard();
  } catch (e) {
    showToast(e.message, true);
  }
}

function setupContentMatchModal() {
  const modal = document.getElementById("content-match-modal");
  const openBtn = document.getElementById("content-match-btn");
  const closeBtn = document.getElementById("content-match-close");

  openBtn.addEventListener("click", () => {
    modal.hidden = false;
    loadContentMatchModal();
  });
  closeBtn.addEventListener("click", () => (modal.hidden = true));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.hidden = true;
  });

  // 키워드 카드의 "체험단 의심 N ?" 배지를 눌러도 같은 모달이 뜨도록
  document.getElementById("kw-list").addEventListener("click", (e) => {
    if (e.target.closest("[data-action='open-content-match']")) {
      modal.hidden = false;
      loadContentMatchModal();
    }
  });
}

// ---------- 키워드 TOP7 상세보기 (자동 감지가 놓친 체험단 글을 직접 확정할 수 있음) ----------
// 자동 감지는 "제목에 업체명/직원 이름이 있는지"만 보기 때문에, 체험단이 우리 이름을
// 안 쓰고 쓴 글은 "타업체"로 남아있게 된다. 여기서는 TOP7 글 하나하나를 보여주고,
// 자동으로 안 걸린 글도 사람이 직접 "우리 체험단 맞음/아님"으로 정할 수 있게 한다.
let currentDetailKeywordId = null;

function openKeywordDetail(keywordId) {
  const k = dashboardData.keywords.find((kw) => kw.id === keywordId);
  if (!k) return;
  currentDetailKeywordId = keywordId;
  document.getElementById("keyword-detail-title").textContent = `"${k.keyword}" TOP7 글 목록`;
  document.getElementById("keyword-detail-modal").hidden = false;
  renderKeywordDetailList(k);
  loadKeywordDetailAlerts(keywordId);
}

async function loadKeywordDetailAlerts(keywordId) {
  const box = document.getElementById("keyword-detail-alerts");
  box.innerHTML = "";
  let alertsList;
  try {
    alertsList = await apiFetch(`/api/alerts?status=open&keyword_id=${keywordId}`);
  } catch (e) {
    return; // 알림 조회 실패는 조용히 무시 - TOP7 목록은 그대로 보여준다
  }
  if (alertsList.length === 0) return;

  box.innerHTML = `
    <div class="alert-box">
      <div class="alert-box__title">⚠ 이탈 알림 ${alertsList.length}건</div>
      ${alertsList
        .map(
          (a) => `
        <div class="alert-box__row">
          <span>${escapeHtml(a.matched_blog_name || a.blog_id || "알 수 없음")} - 이전 ${
            a.previous_position
          }위에 있었는데 지금은 안 보여요 (${formatDateTime(a.detected_at)} 감지)</span>
          <button class="btn btn-outline" data-resolve-alert="${a.id}" style="padding:4px 10px; font-size:12px;">확인 완료</button>
        </div>`
        )
        .join("")}
    </div>`;

  box.querySelectorAll("[data-resolve-alert]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await apiFetch(`/api/alerts/${btn.dataset.resolveAlert}/resolve`, { method: "POST" });
        await loadDashboard();
        loadKeywordDetailAlerts(keywordId);
      } catch (e) {
        showToast(e.message, true);
      }
    });
  });
}

function renderKeywordDetailList(k) {
  const listEl = document.getElementById("keyword-detail-list");

  listEl.innerHTML = k.slots
    .map((s) => {
      if (!s.title) {
        return `<div class="content-match-item content-match-item--empty">
          <div class="content-match-item__meta">${s.position}위 · 미노출</div>
        </div>`;
      }

      const label = ownershipLabel(s);
      // 경쟁업체는 계정 자체가 자기 홍보용이라 우리 얘기가 나올 일이 사실상 없어서
      // 확정 버튼을 안 보여준다. 체험단은 다르다 - 같은 계정이 다른 키워드에선 완전히
      // 다른 업체 글을 쓰기도 해서, 이 글 자체는 항상 사람이 판정을 뒤집을 수 있어야
      // 한다 (직원 블로그만 예외 - 늘 우리 것).
      const isKnownCompetitor = s.ownership === "other" && s.owner_role === "competitor";
      const canOverride = s.ownership !== "ours_staff" && !isKnownCompetitor;
      // 아직 아무 역할로도 등록 안 된 블로그(신원 미확인)에서만 "경쟁업체로 등록"을
      // 보여준다 - 이미 체험단/공식/직원으로 등록돼 있으면 중복 등록할 이유가 없다.
      const canRegisterCompetitor =
        !s.owner_role && (s.ownership === "other" || s.ownership === "pending_experience");
      const actions = canOverride
        ? `<div class="content-match-item__actions">
            <button class="btn btn-primary" data-kd-decide="confirmed" data-url="${escapeHtml(
              s.url
            )}" data-title="${escapeHtml(s.title)}" style="padding:6px 14px;">✓ 우리 체험단 맞음</button>
            <button class="btn btn-outline" data-kd-decide="rejected" data-url="${escapeHtml(
              s.url
            )}" data-title="${escapeHtml(s.title)}" style="padding:6px 14px;">타업체/아니오</button>
            ${
              canRegisterCompetitor
                ? `<button class="btn btn-outline" data-kd-register-competitor="1" data-blog-id="${escapeHtml(
                    s.blog_id || ""
                  )}" data-content-type="${escapeHtml(
                    s.content_type || "blog"
                  )}" style="padding:6px 14px;">🚫 경쟁업체로 등록</button>`
                : ""
            }
          </div>`
        : "";

      return `
      <div class="content-match-item">
        <div class="content-match-item__title">${s.position}위 · ${escapeHtml(s.title)}</div>
        <div class="content-match-item__meta">
          <span class="rank-dot rank-dot--${s.ownership}" style="display:inline-flex; margin-right:6px; ${accountColorCss(
        s
      )}">${
        s.position
      }</span>${escapeHtml(label)}${s.owner_name ? " · " + escapeHtml(s.owner_name) : ""} ·
          <a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">글 보러가기 ↗</a>
        </div>
        ${actions}
      </div>`;
    })
    .join("");

  listEl.querySelectorAll("[data-kd-decide]").forEach((btn) => {
    btn.addEventListener("click", () =>
      decideKeywordDetailMatch(btn.dataset.url, btn.dataset.title, btn.dataset.kdDecide)
    );
  });
  listEl.querySelectorAll("[data-kd-register-competitor]").forEach((btn) => {
    btn.addEventListener("click", () =>
      registerCompetitorFromDetail(btn.dataset.blogId, btn.dataset.contentType)
    );
  });
}

async function registerCompetitorFromDetail(blogId, contentType) {
  if (!blogId) {
    showToast("이 글의 블로그 계정을 인식하지 못해 등록할 수 없습니다.", true);
    return;
  }
  const name = window.prompt(
    "이 블로그를 경쟁업체로 등록합니다. 앞으로 이 계정의 모든 글은 자동으로 \"확인된 타업체\"로 표시됩니다.\n\n경쟁업체 이름(상호명/트레이너 이름 등)을 입력해주세요:",
    ""
  );
  if (name === null) return; // 취소
  if (!name.trim()) {
    showToast("이름을 입력해야 등록할 수 있습니다.", true);
    return;
  }

  const blogUrl =
    contentType === "cafe" ? `https://cafe.naver.com/${blogId}` : `https://blog.naver.com/${blogId}`;

  try {
    await apiFetch("/api/blogs", {
      method: "POST",
      body: JSON.stringify({ name: name.trim(), blog_url: blogUrl, role: "competitor", memo: "" }),
    });
    showToast(`"${name.trim()}"을(를) 경쟁업체로 등록했습니다.`);
    await loadDashboard();
    const modal = document.getElementById("keyword-detail-modal");
    if (!modal.hidden && currentDetailKeywordId !== null) {
      const k = dashboardData.keywords.find((kw) => kw.id === currentDetailKeywordId);
      if (k) renderKeywordDetailList(k);
    }
  } catch (e) {
    showToast(e.message, true);
  }
}

async function decideKeywordDetailMatch(url, title, decision) {
  try {
    await apiFetch("/api/content-matches/manual", {
      method: "POST",
      body: JSON.stringify({ url, title, decision }),
    });
    showToast(decision === "confirmed" ? "체험단 글로 확정했습니다." : "우리 글이 아닌 것으로 처리했습니다.");
    await loadDashboard();
    const modal = document.getElementById("keyword-detail-modal");
    if (!modal.hidden && currentDetailKeywordId !== null) {
      const k = dashboardData.keywords.find((kw) => kw.id === currentDetailKeywordId);
      if (k) renderKeywordDetailList(k);
    }
  } catch (e) {
    showToast(e.message, true);
  }
}

function setupKeywordDetailModal() {
  const modal = document.getElementById("keyword-detail-modal");
  const closeBtn = document.getElementById("keyword-detail-close");
  closeBtn.addEventListener("click", () => (modal.hidden = true));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.hidden = true;
  });
}

document.getElementById("search-input").addEventListener("input", (e) => {
  searchText = e.target.value;
  renderKeywordList();
});

// ---------- 전체 순위 갱신 진행률 ----------
let refreshPollTimer = null;

function stopRefreshPolling() {
  if (refreshPollTimer) {
    clearInterval(refreshPollTimer);
    refreshPollTimer = null;
  }
  const progress = document.getElementById("refresh-progress");
  if (progress) progress.hidden = true;
  const btn = document.getElementById("refresh-all-btn");
  if (!btn) return;
  btn.disabled = false;
  btn.innerHTML = "↻ 전체 순위 갱신";
}

async function pollRefreshStatus() {
  let status;
  try {
    status = await apiFetch("/api/keywords/refresh-all/status");
  } catch (e) {
    stopRefreshPolling();
    return;
  }

  const progress = document.getElementById("refresh-progress");
  const fill = document.getElementById("refresh-progress-fill");
  const text = document.getElementById("refresh-progress-text");
  if (progress && fill && text) {
    progress.hidden = false;
    const fillPct = status.total ? Math.round((status.done / status.total) * 100) : 0;
    fill.style.width = `${fillPct}%`;
    text.textContent = status.running
      ? `${status.done}/${status.total} 처리 중${status.current_keyword ? " · " + status.current_keyword : ""}`
      : `${status.done}/${status.total} 완료`;
  }

  if (!status.running) {
    stopRefreshPolling();
    const failCount = status.errors.length;
    const successCount = status.total - failCount;
    showToast(
      failCount > 0
        ? `${status.total}개 중 ${successCount}개 갱신 완료, ${failCount}개는 실패했습니다: ${status.errors
            .map((e) => e.keyword)
            .join(", ")}`
        : `${status.total}개 키워드 순위를 갱신했습니다.`,
      failCount > 0
    );
    await loadDashboard();
  }
}

document.getElementById("refresh-all-btn").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  btn.disabled = true;
  btn.textContent = "시작하는 중...";
  try {
    const res = await apiFetch("/api/keywords/refresh-all", { method: "POST" });
    if (!res.total) {
      showToast("갱신할 키워드가 없습니다.");
      btn.disabled = false;
      btn.innerHTML = "↻ 전체 순위 갱신";
      return;
    }
    btn.textContent = "갱신 중...";
    if (refreshPollTimer) clearInterval(refreshPollTimer);
    refreshPollTimer = setInterval(pollRefreshStatus, 1200);
    await pollRefreshStatus();
  } catch (e2) {
    showToast(e2.message, true);
    btn.disabled = false;
    btn.innerHTML = "↻ 전체 순위 갱신";
  }
});

// 페이지를 새로고침했는데 마침 백그라운드에서 갱신이 진행 중이었다면 이어서 폴링을 재개한다.
async function resumeRefreshPollingIfRunning() {
  try {
    const status = await apiFetch("/api/keywords/refresh-all/status");
    if (status.running) {
      document.getElementById("refresh-all-btn").disabled = true;
      document.getElementById("refresh-all-btn").textContent = "갱신 중...";
      refreshPollTimer = setInterval(pollRefreshStatus, 1200);
      await pollRefreshStatus();
    }
  } catch (e) {
    // 무시 - 다음 수동 갱신 때 다시 시도됨
  }
}

// ---------- 업체 프로필 (접이식) ----------
async function loadProfile() {
  try {
    const s = await apiFetch("/api/settings");
    const form = document.getElementById("profile-form");
    form.business_name.value = s.business_name || "";
    form.address.value = s.address || "";
    form.phone.value = s.phone || "";
    form.strengths.value = s.strengths || "";
    form.custom_watch_keywords.value = s.custom_watch_keywords || "";

    const autoBox = document.getElementById("auto-watch-names");
    autoBox.textContent = s.auto_watch_names && s.auto_watch_names.length
      ? `현재 자동으로 감시 중: ${s.auto_watch_names.join(", ")}`
      : "현재 자동으로 감시 중인 이름 없음 (업체명/직원을 등록하면 자동으로 추가됩니다)";
  } catch (e) {
    showToast(e.message, true);
  }
}

document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await apiFetch("/api/settings/profile", {
      method: "PUT",
      body: JSON.stringify({
        business_name: fd.get("business_name") || "",
        address: fd.get("address") || "",
        phone: fd.get("phone") || "",
        strengths: fd.get("strengths") || "",
        custom_watch_keywords: fd.get("custom_watch_keywords") || "",
      }),
    });
    showToast("업체 프로필을 저장했습니다.");
    await loadOnboarding();
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- 초기 설정 체크리스트 ----------
async function loadOnboarding() {
  const card = document.getElementById("onboarding-card");
  if (!card) return;
  try {
    const [settings, blogs, dash] = await Promise.all([
      apiFetch("/api/settings"),
      apiFetch("/api/blogs"),
      apiFetch("/api/dashboard/summary"),
    ]);

    const steps = [
      {
        label: "업체 프로필 입력 (업체명)",
        done: !!settings.business_name,
        action: () => {
          document.getElementById("profile-details").open = true;
          document.getElementById("profile-details").scrollIntoView({ behavior: "smooth" });
        },
      },
      { label: "OpenAI API 키 설정", done: settings.openai_api_key_set, href: "/settings" },
      { label: "블로그 등록 (내 블로그 최소 1개)", done: blogs.length > 0, href: "/blogs" },
      {
        label: "키워드 추가",
        done: dash.keywords.length > 0,
        action: () => document.getElementById("add-keyword-btn").click(),
      },
    ];

    if (steps.every((s) => s.done)) {
      card.hidden = true;
      return;
    }

    card.hidden = false;
    const list = document.getElementById("onboarding-list");
    list.innerHTML = steps
      .map(
        (s, idx) => `
      <li class="onboarding-item ${s.done ? "onboarding-item--done" : ""}">
        <span>${s.done ? "✅" : "⬜"}</span>
        <span>${escapeHtml(s.label)}</span>
        ${
          !s.done
            ? s.href
              ? `<a class="onboarding-item__link" href="${s.href}">이동 →</a>`
              : `<button class="onboarding-item__link" data-onboarding-step="${idx}">바로가기 →</button>`
            : ""
        }
      </li>`
      )
      .join("");

    list.querySelectorAll("[data-onboarding-step]").forEach((btn) => {
      btn.addEventListener("click", () => steps[Number(btn.dataset.onboardingStep)].action());
    });
  } catch (e) {
    card.hidden = true;
  }
}

setupAddKeywordModal();
setupContentMatchModal();
setupKeywordDetailModal();
loadDashboard();
loadProfile();
loadOnboarding();
resumeRefreshPollingIfRunning();
