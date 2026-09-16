// Mostrar o banner de cookies após um pequeno delay
document.addEventListener("DOMContentLoaded", function () {
  const banner = document.getElementById("cookieBanner");
  const cookiesAccepted = localStorage.getItem("cookiesAccepted");
  if (cookiesAccepted === "true" && banner) {
    banner.style.display = "none";
  } else if (banner) {
    setTimeout(function () {
      banner.classList.add("show");
    }, 4000);
  }

  const acceptBtn = document.getElementById("acceptCookies");
  if (acceptBtn) {
    acceptBtn.addEventListener("click", function () {
      if (banner) {
        banner.classList.remove("show");
        setTimeout(function () {
          banner.style.display = "none";
        }, 800);
      }
      localStorage.setItem("cookiesAccepted", "true");
    });
  }
});