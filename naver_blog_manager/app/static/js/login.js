document.getElementById("naver-login-btn").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  const msg = document.getElementById("login-status-msg");
  btn.disabled = true;
  btn.textContent = "브라우저 창에서 로그인해주세요...";
  msg.textContent = "";

  try {
    await apiFetch("/api/naver-auth/login", { method: "POST" });

    // 로그인은 됐는데, "네이버로 보내기"가 실제로 쓸 "공식 블로그"가 하나도 등록 안
    // 돼있으면 - 방금 로그인한 그 계정을 바로 이어서 등록하게 한다. "로그인했으니
    // 당연히 이 계정으로 글을 쓰겠지"라는 기대가 실제로 그렇게 동작하도록, 로그인과
    // 등록을 분리된 화면(블로그 관리)으로 미루지 않고 같은 흐름에서 끝낸다.
    const blogs = await apiFetch("/api/blogs");
    const hasCompanyBlog = blogs.some((b) => b.role === "company");
    if (hasCompanyBlog) {
      msg.textContent = "로그인 성공! 이동합니다...";
      window.location.href = "/";
      return;
    }

    btn.disabled = true;
    btn.textContent = "로그인 완료";
    document.getElementById("link-blog-box").hidden = false;
  } catch (err) {
    msg.textContent = err.message;
    btn.disabled = false;
    btn.textContent = "네이버 로그인하기";
  }
});

document.getElementById("link-blog-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const submitBtn = e.target.querySelector("button[type='submit']");
  submitBtn.disabled = true;
  try {
    await apiFetch("/api/blogs", {
      method: "POST",
      body: JSON.stringify({
        name: "공식 블로그",
        blog_url: fd.get("blog_url"),
        role: "company",
      }),
    });
    window.location.href = "/";
  } catch (err) {
    showToast(err.message, true);
    submitBtn.disabled = false;
  }
});

document.getElementById("skip-link-blog-btn").addEventListener("click", () => {
  window.location.href = "/";
});
