document.getElementById("naver-login-btn").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  const msg = document.getElementById("login-status-msg");
  btn.disabled = true;
  btn.textContent = "브라우저 창에서 로그인해주세요...";
  msg.textContent = "";

  try {
    await apiFetch("/api/naver-auth/login", { method: "POST" });
    msg.textContent = "로그인 성공! 이동합니다...";
    window.location.href = "/";
  } catch (err) {
    msg.textContent = err.message;
    btn.disabled = false;
    btn.textContent = "네이버 로그인하기";
  }
});
