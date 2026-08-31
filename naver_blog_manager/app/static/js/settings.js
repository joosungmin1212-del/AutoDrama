let defaultPrompt = "";

async function loadSettings() {
  try {
    const s = await apiFetch("/api/settings");
    const form = document.getElementById("ai-settings-form");
    form.openai_model.value = s.openai_model || "gpt-4o-mini";
    form.rank_check_interval_hours.value = s.rank_check_interval_hours || 24;
    form.custom_prompt.value = s.custom_prompt || "";
    defaultPrompt = s.default_prompt || "";

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

document.getElementById("ai-settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await apiFetch("/api/settings/ai", {
      method: "PUT",
      body: JSON.stringify({
        openai_api_key: fd.get("openai_api_key") || "",
        openai_model: fd.get("openai_model") || "gpt-4o-mini",
        rank_check_interval_hours: Number(fd.get("rank_check_interval_hours") || 24),
        custom_prompt: fd.get("custom_prompt") || "",
      }),
    });
    e.target.openai_api_key.value = "";
    showToast("설정을 저장했습니다.");
    await loadSettings();
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("prompt-reset-btn").addEventListener("click", () => {
  document.getElementById("prompt-textarea").value = defaultPrompt;
});

loadSettings();
