let currentDraftId = null;
let currentHashtags = [];

// URL의 ?keyword= 로 들어오면 (대시보드의 "글 작성" 버튼) 자동으로 채워준다.
const params = new URLSearchParams(window.location.search);
if (params.get("keyword")) {
  document.getElementById("keyword-input").value = params.get("keyword");
  document.getElementById("title-input").focus();
}

// 글쓰기 계정(직원으로 등록한 블로그)이 2개 이상이면 "보낼 계정"을 고를 수 있게 한다 -
// 1개뿐이면(대부분의 경우) 기존처럼 신경 쓸 필요 없이 자동으로 그 계정(=마지막으로
// 로그인/전송한 계정)으로 보낸다. "공식 블로그"라는 별도 역할은 더 이상 없다 - 이미
// 직원으로 등록해둔 블로그 자체가 계정 후보다.
async function loadSendAccountOptions() {
  try {
    const [accounts, settings] = await Promise.all([
      apiFetch("/api/naver-auth/accounts"),
      apiFetch("/api/settings"),
    ]);
    const field = document.getElementById("send-account-field");
    const select = document.getElementById("send-account-select");
    if (accounts.length > 1) {
      select.innerHTML = accounts
        .map((a) => `<option value="${a.blog_pk}">${escapeHtml(a.name)} (${escapeHtml(a.blog_id)})</option>`)
        .join("");
      // 마지막으로 쓴 계정을 기본 선택값으로 - 매번 다시 고를 필요 없게.
      const activeAccount = accounts.find(
        (a) => a.blog_id.toLowerCase() === (settings.active_writer_blog_id || "").toLowerCase()
      );
      if (activeAccount) select.value = String(activeAccount.blog_pk);
      field.hidden = false;
    } else {
      field.hidden = true;
    }
  } catch (e) {
    // 조용히 무시 - 계정 선택 없이도(1개 등록 기준) 보내기는 그대로 동작한다.
  }
}
loadSendAccountOptions();

document.getElementById("generate-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("generate-btn");
  const fd = new FormData(e.target);
  const title = fd.get("title");
  if (!title || !title.trim()) {
    showToast("제목을 입력해주세요.", true);
    return;
  }

  btn.disabled = true;
  btn.textContent = "생성 중... (최대 30초)";
  document.getElementById("send-btn").disabled = true;

  try {
    const res = await apiFetch("/api/writer/generate", {
      method: "POST",
      body: JSON.stringify({
        title,
        keyword: fd.get("keyword") || null,
        extra_request: fd.get("extra_request") || "",
      }),
    });
    currentDraftId = res.draft_id;
    currentHashtags = res.hashtags || [];
    document.getElementById("content-box").value = res.content;
    renderSeoCheck(res.seo_check, res.template_label);
    renderHashtags(currentHashtags);
    document.getElementById("send-btn").disabled = false;
    showToast("초안을 생성했습니다. 내용을 확인해주세요.");
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = "AI 초안 생성";
  }
});

function renderSeoCheck(check, templateLabel) {
  const box = document.getElementById("seo-check-box");
  box.style.display = "flex";
  const templateBadge = templateLabel
    ? `<div class="seo-check-item ok">📖 스토리 템플릿: ${escapeHtml(templateLabel)}</div>`
    : "";
  box.innerHTML = `
    <div class="seo-check-item ${check.length_ok ? "ok" : "warn"}">
      ${check.length_ok ? "✅" : "⚠"} 글자 수 ${check.length}자 (권장 1700~2500자)
    </div>
    <div class="seo-check-item ${check.keyword_count_ok ? "ok" : "warn"}">
      ${check.keyword_count_ok ? "✅" : "⚠"} 키워드 반복 ${check.keyword_count}회 (권장 5~10회)
    </div>
    <div class="seo-check-item ${check.subheading_count >= 3 ? "ok" : "warn"}">
      ${check.subheading_count >= 3 ? "✅" : "⚠"} 소제목 ${check.subheading_count}개 (권장 3~5개)
    </div>
    ${templateBadge}
  `;
}

function renderHashtags(tags) {
  const box = document.getElementById("hashtag-box");
  box.innerHTML = tags.map((t) => `<span class="hashtag-pill">${escapeHtml(t)}</span>`).join("");
}

document.getElementById("copy-btn").addEventListener("click", async () => {
  const content = document.getElementById("content-box").value;
  const text = content + (currentHashtags.length ? "\n\n" + currentHashtags.join(" ") : "");
  try {
    await navigator.clipboard.writeText(text);
    showToast("클립보드에 복사했습니다. 네이버 에디터에 붙여넣어주세요.");
  } catch (e) {
    showToast("복사에 실패했습니다. 직접 드래그해서 복사해주세요.", true);
  }
});

document.getElementById("send-btn").addEventListener("click", async () => {
  if (!currentDraftId) return;
  const btn = document.getElementById("send-btn");
  btn.disabled = true;
  btn.textContent = "네이버 창을 여는 중...";
  const accountField = document.getElementById("send-account-field");
  const writerBlogId =
    !accountField.hidden && document.getElementById("send-account-select").value
      ? Number(document.getElementById("send-account-select").value)
      : null;

  try {
    const res = await apiFetch("/api/writer/send-to-naver", {
      method: "POST",
      // 미리보기에서 고친 내용을 그대로 보낸다 (서버에 저장된 원본 초안이 아니라).
      body: JSON.stringify({
        draft_id: currentDraftId,
        content: document.getElementById("content-box").value,
        writer_blog_id: writerBlogId,
      }),
    });
    showToast(res.message);
    if (typeof updateActiveWriterBadge === "function") updateActiveWriterBadge();
  } catch (e) {
    showToast(e.message + " (복사하기 버튼으로 직접 붙여넣어도 됩니다)", true);
  } finally {
    btn.disabled = false;
    btn.textContent = "네이버로 보내기";
  }
});
