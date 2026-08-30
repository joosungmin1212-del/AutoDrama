const OWNERSHIP_LABEL = {
  ours_staff: "직원",
  ours_experience: "체험단",
  ours_company: "공식블로그",
  pending_experience: "체험단 의심(확인필요)",
  other: "타업체",
  empty: "미노출",
};

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

  document.getElementById(
    "stat-share"
  ).innerHTML = `${stats.our_total} / ${stats.our_slots_total} <small>(${pct(
    stats.our_total,
    stats.our_slots_total
  )}%)</small>`;
  document.getElementById("stat-share-bar").style.width = `${pct(stats.our_total, stats.our_slots_total)}%`;

  document.getElementById("stat-staff").textContent = stats.staff_exposure_count;
  document.getElementById("stat-staff-sub").textContent = breakdownText(stats.staff_breakdown, "개 포스팅 노출 중");

  document.getElementById("stat-experience").textContent = stats.experience_exposure_count;
  document.getElementById("stat-experience-sub").textContent = breakdownText(
    stats.experience_breakdown,
    "개 후기 노출 중"
  );

  const btn = document.getElementById("content-match-btn");
  btn.textContent = `🕵️ 체험단 확인 필요 (${stats.pending_content_match_count})`;
  btn.classList.toggle("filter-tab--alert", stats.pending_content_match_count > 0);
}

function pct(n, total) {
  if (!total) return 0;
  return Math.round((n / total) * 100);
}

function breakdownText(breakdown, suffix) {
  const entries = Object.entries(breakdown || {});
  if (entries.length === 0) return `${suffix}`;
  const detail = entries.map(([name, count]) => `${name} ${count}건`).join(" · ");
  return `${suffix} · ${detail}`;
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

  if (draggable) {
    setupDragAndDrop(listEl);
  }
}

function renderEmployeeChecklist(k) {
  const badges = k.staff_presence.map(
    (s) =>
      `<span class="emp-badge ${s.present ? "emp-badge--yes" : "emp-badge--no"}">${escapeHtml(s.name)} ${
        s.present ? "✓" : "✗"
      }</span>`
  );

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
      const label = s.title
        ? `${OWNERSHIP_LABEL[s.ownership] || ""}${s.owner_name ? " · " + s.owner_name : ""}\n${s.title}`
        : "미노출";
      return `<span class="rank-dot rank-dot--${s.ownership}" title="${escapeHtml(label)}">${s.position}</span>`;
    })
    .join("");

  return `
  <div class="kw-card ${alertClass}" data-id="${k.id}" ${draggable ? 'draggable="true"' : ""}>
    ${draggable ? '<span class="drag-handle" title="드래그해서 순서 바꾸기">⠿</span>' : ""}
    <div class="kw-ratio-box">${k.our_count}/${k.total_slots}</div>
    <div class="kw-card__main">
      <div class="kw-card__title-row">
        <span class="kw-title">${escapeHtml(k.keyword)}</span>
        ${k.category ? `<span class="badge badge-category">${escapeHtml(k.category)}</span>` : ""}
        ${k.has_open_alert ? `<span class="badge badge-alert">⚠ 이탈 발생</span>` : ""}
      </div>
      <div class="kw-card__meta">최근 확인: ${formatDateTime(k.last_checked_at)}</div>
      ${k.memo ? `<div class="kw-card__memo">${escapeHtml(k.memo)}</div>` : ""}
      ${renderEmployeeChecklist(k)}
    </div>
    <div class="kw-card__right">
      <div>
        <div class="rank-dots">${dots}</div>
        <div class="kw-ratio-text">TOP7 점유: ${k.our_count}/${k.total_slots} (${pctVal}%)</div>
      </div>
      <button class="icon-btn" data-action="refresh" data-id="${k.id}" title="순위 갱신">↻</button>
      <button class="btn-write" data-action="write" data-keyword="${escapeHtml(k.keyword)}">✎ 글 작성</button>
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

function setupAddKeywordModal() {
  const modal = document.getElementById("add-keyword-modal");
  const openBtn = document.getElementById("add-keyword-btn");
  const cancelBtn = document.getElementById("add-keyword-cancel");
  const form = document.getElementById("add-keyword-form");

  openBtn.addEventListener("click", () => (modal.hidden = false));
  cancelBtn.addEventListener("click", () => (modal.hidden = true));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.hidden = true;
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    try {
      await apiFetch("/api/keywords", {
        method: "POST",
        body: JSON.stringify({
          keyword: fd.get("keyword"),
          category: fd.get("category") || "",
          memo: fd.get("memo") || "",
        }),
      });
      form.reset();
      modal.hidden = true;
      showToast("키워드를 추가했습니다.");
      await loadDashboard();
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

document.getElementById("search-input").addEventListener("input", (e) => {
  searchText = e.target.value;
  renderKeywordList();
});

document.getElementById("refresh-all-btn").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  btn.disabled = true;
  btn.textContent = "갱신 중...";
  try {
    const res = await apiFetch("/api/keywords/refresh-all", { method: "POST" });
    showToast(`${res.checked}개 키워드 순위를 갱신했습니다.`);
  } catch (e2) {
    showToast(e2.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = "↻ 전체 순위 갱신";
    await loadDashboard();
  }
});

setupAddKeywordModal();
setupContentMatchModal();
loadDashboard();
