async function loadSettings() {
  try {
    const s = await apiFetch("/api/settings");
    const form = document.getElementById("settings-form");
    form.business_name.value = s.business_name || "";
    form.address.value = s.address || "";
    form.phone.value = s.phone || "";
    form.strengths.value = s.strengths || "";
    form.openai_model.value = s.openai_model || "gpt-4o-mini";
    form.rank_check_interval_hours.value = s.rank_check_interval_hours || 24;

    const keyStatus = document.getElementById("key-status");
    if (s.openai_api_key_set) {
      keyStatus.textContent = "설정됨";
      keyStatus.className = "status-pill ok";
    } else {
      keyStatus.textContent = "미설정";
      keyStatus.className = "status-pill off";
    }
  } catch (e) {
    showToast(e.message, true);
  }
}

document.getElementById("settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await apiFetch("/api/settings", {
      method: "PUT",
      body: JSON.stringify({
        business_name: fd.get("business_name") || "",
        address: fd.get("address") || "",
        phone: fd.get("phone") || "",
        strengths: fd.get("strengths") || "",
        openai_api_key: fd.get("openai_api_key") || "",
        openai_model: fd.get("openai_model") || "gpt-4o-mini",
        rank_check_interval_hours: Number(fd.get("rank_check_interval_hours") || 24),
      }),
    });
    e.target.openai_api_key.value = "";
    showToast("설정을 저장했습니다.");
    await loadSettings();
  } catch (err) {
    showToast(err.message, true);
  }
});

async function loadNaverStatus() {
  const badge = document.getElementById("naver-status");
  try {
    const s = await apiFetch("/api/naver-auth/status");
    if (s.logged_in) {
      badge.textContent = "연동됨";
      badge.className = "status-pill ok";
    } else {
      badge.textContent = "미연동";
      badge.className = "status-pill off";
    }
  } catch (e) {
    badge.textContent = "확인 실패";
    badge.className = "status-pill off";
  }
}

document.getElementById("naver-login-btn").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  btn.disabled = true;
  btn.textContent = "브라우저 창에서 로그인해주세요...";
  try {
    await apiFetch("/api/naver-auth/login", { method: "POST" });
    showToast("네이버 로그인에 성공했습니다.");
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = "네이버 로그인";
    await loadNaverStatus();
  }
});

document.getElementById("naver-logout-btn").addEventListener("click", async () => {
  try {
    await apiFetch("/api/naver-auth/logout", { method: "POST" });
    showToast("로그아웃했습니다.");
    await loadNaverStatus();
  } catch (err) {
    showToast(err.message, true);
  }
});

loadSettings();
loadNaverStatus();
