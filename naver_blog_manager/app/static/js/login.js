document.getElementById("naver-login-btn").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  const msg = document.getElementById("login-status-msg");
  btn.disabled = true;
  btn.textContent = "브라우저 창에서 로그인해주세요...";
  msg.textContent = "";

  try {
    await apiFetch("/api/naver-auth/login", { method: "POST" });

    // 로그인은 됐는데, "네이버로 보내기"가 실제로 쓸 계정이 하나도 등록 안 돼있으면 -
    // 방금 로그인한 그 계정을 바로 이어서 등록하게 한다. "로그인했으니 당연히 이
    // 계정으로 글을 쓰겠지"라는 기대가 실제로 그렇게 동작하도록, 로그인과 등록을
    // 분리된 화면(블로그 관리)으로 미루지 않고 같은 흐름에서 끝낸다. 별도의 "공식
    // 블로그" 역할은 없다 - 이미 계정이 하나라도 등록돼 있으면(직원으로) 그냥 넘어간다.
    const accounts = await apiFetch("/api/naver-auth/accounts");
    if (accounts.length > 0) {
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
    const created = await apiFetch("/api/blogs", {
      method: "POST",
      body: JSON.stringify({
        name: fd.get("name"),
        blog_url: fd.get("blog_url"),
        role: "staff",
      }),
    });
    // 방금 등록한 계정을 바로 "지금 쓸 글쓰기 계정"으로 지정한다.
    await apiFetch("/api/settings/active-writer", {
      method: "PUT",
      body: JSON.stringify({ blog_id: created.blog_id }),
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
