const ROLE_LABEL = { company: "공식 블로그", staff: "직원", experience: "체험단/서포터즈" };

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
  } catch (e2) {
    showToast(e2.message, true);
  }
});

loadBlogs();
