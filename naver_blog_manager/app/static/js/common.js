// 공통 유틸: fetch 래퍼 + 토스트 알림
async function apiFetch(url, options = {}) {
  const opts = Object.assign({ headers: { "Content-Type": "application/json" } }, options);
  const res = await fetch(url, opts);
  let data = null;
  try {
    data = await res.json();
  } catch (e) {
    data = null;
  }
  if (!res.ok) {
    const message = (data && data.detail) || `요청 실패 (${res.status})`;
    throw new Error(message);
  }
  return data;
}

let toastTimer = null;
function showToast(message, isError = false) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = message;
  el.style.background = isError ? "#e11d48" : "#1c2430";
  el.hidden = false;
  if (toastTimer) clearTimeout(toastTimer);
  // 오류 메시지는 원인 파악을 위해 읽을 시간이 필요하므로 훨씬 오래 띄워둔다.
  toastTimer = setTimeout(
    () => {
      el.hidden = true;
    },
    isError ? 12000 : 3200
  );
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatDateTime(iso) {
  if (!iso) return "확인 전";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "확인 전";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(
    d.getMinutes()
  )}`;
}

// 모든 페이지 공통: 상단 "로그아웃" 링크 (네이버 로그인 화면으로 되돌아간다)
document.addEventListener("DOMContentLoaded", () => {
  const logoutLink = document.getElementById("naver-logout-link");
  if (!logoutLink) return;
  logoutLink.addEventListener("click", async (e) => {
    e.preventDefault();
    if (!confirm("네이버 로그아웃 할까요? 다음에 쓰려면 다시 로그인해야 합니다.")) return;
    try {
      await apiFetch("/api/naver-auth/logout", { method: "POST" });
      window.location.href = "/login";
    } catch (err) {
      showToast(err.message, true);
    }
  });
});
