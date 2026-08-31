const ROLE_LABEL = {
  company: "공식 블로그",
  staff: "직원",
  experience: "체험단/서포터즈",
  competitor: "경쟁업체",
};

async function loadBlogs() {
  const tbody = document.getElementById("blog-table-body");
  let blogs;
  try {
    blogs = await apiFetch("/api/blogs");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6">불러오기 실패: ${escapeHtml(e.message)}</td></tr>`;
    return;
  }

  if (blogs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--text-faint)">등록된 블로그가 없습니다.</td></tr>`;
    return;
  }

  tbody.innerHTML = blogs
    .map(
      (b) => `
    <tr>
      <td>${escapeHtml(b.name)}</td>
      <td><span class="role-pill role-pill--${b.role}">${ROLE_LABEL[b.role] || b.role}</span></td>
      <td><a href="${escapeHtml(b.blog_url)}" target="_blank" rel="noopener">${escapeHtml(b.blog_url)}</a></td>
      <td>${escapeHtml(b.blog_id)}</td>
      <td>${escapeHtml(b.memo || "")}</td>
      <td><button class="icon-btn icon-btn--danger" data-id="${b.id}" data-name="${escapeHtml(b.name)}">🗑</button></td>
    </tr>`
    )
    .join("");

  tbody.querySelectorAll("button[data-id]").forEach((btn) => {
    btn.addEventListener("click", () => deleteBlog(Number(btn.dataset.id), btn.dataset.name));
  });
}

async function deleteBlog(id, name) {
  if (!confirm(`"${name}" 블로그 등록을 삭제할까요?`)) return;
  try {
    await apiFetch(`/api/blogs/${id}`, { method: "DELETE" });
    showToast("삭제했습니다.");
    await loadBlogs();
    await loadNaverAccounts();
  } catch (e) {
    showToast(e.message, true);
  }
}

document.getElementById("add-blog-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await apiFetch("/api/blogs", {
      method: "POST",
      body: JSON.stringify({
        name: fd.get("name"),
        blog_url: fd.get("blog_url"),
        role: fd.get("role"),
        memo: fd.get("memo") || "",
      }),
    });
    e.target.reset();
    showToast("블로그를 등록했습니다.");
    await loadBlogs();
    await loadNaverAccounts();
  } catch (e2) {
    showToast(e2.message, true);
  }
});

// ---------- 네이버 계정(공식 블로그별 로그인) ----------
// 공식 블로그를 1개만 등록해 쓰는 대부분의 경우엔 이 카드 자체를 숨긴다 - 기존
// 사용자에게는 화면이 그대로 보이도록. 2개 이상일 때만 계정 전환이 의미가 있어 보여준다.
async function loadNaverAccounts() {
  const card = document.getElementById("naver-accounts-card");
  const tbody = document.getElementById("naver-account-table-body");
  let accounts;
  try {
    accounts = await apiFetch("/api/naver-auth/accounts");
  } catch (e) {
    card.style.display = "none";
    return;
  }

  if (accounts.length < 2) {
    card.style.display = "none";
    return;
  }
  card.style.display = "";

  tbody.innerHTML = accounts
    .map(
      (a) => `
    <tr>
      <td>${escapeHtml(a.name)}</td>
      <td>${escapeHtml(a.blog_id)}</td>
      <td>${a.logged_in ? "✅ 로그인됨" : "⬜ 로그인 필요"}</td>
      <td>
        <button class="btn btn-outline" data-naver-login="${escapeHtml(a.blog_id)}" style="padding:5px 12px;">
          ${a.logged_in ? "다시 로그인" : "이 계정으로 로그인"}
        </button>
        ${
          a.logged_in
            ? `<button class="btn btn-outline" data-naver-logout="${escapeHtml(
                a.blog_id
              )}" style="padding:5px 12px;">로그아웃</button>`
            : ""
        }
      </td>
    </tr>`
    )
    .join("");

  tbody.querySelectorAll("[data-naver-login]").forEach((btn) => {
    btn.addEventListener("click", () => naverAccountLogin(btn.dataset.naverLogin, btn));
  });
  tbody.querySelectorAll("[data-naver-logout]").forEach((btn) => {
    btn.addEventListener("click", () => naverAccountLogout(btn.dataset.naverLogout));
  });
}

async function naverAccountLogin(blogId, btn) {
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = "브라우저 창에서 로그인해주세요...";
  try {
    await apiFetch(`/api/naver-auth/login?blog_id=${encodeURIComponent(blogId)}`, { method: "POST" });
    showToast("로그인되었습니다.");
    await loadNaverAccounts();
  } catch (e) {
    showToast(e.message, true);
    btn.disabled = false;
    btn.textContent = original;
  }
}

async function naverAccountLogout(blogId) {
  try {
    await apiFetch(`/api/naver-auth/logout?blog_id=${encodeURIComponent(blogId)}`, { method: "POST" });
    showToast("로그아웃했습니다.");
    await loadNaverAccounts();
  } catch (e) {
    showToast(e.message, true);
  }
}

loadBlogs();
loadNaverAccounts();
