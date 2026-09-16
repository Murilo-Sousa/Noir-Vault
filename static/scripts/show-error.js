document.addEventListener("DOMContentLoaded", function () {
  telaErro = document.querySelector(".tela-de-erro");
  telaErro.classList.add("slide-down");
  setTimeout(() => telaErro.classList.remove("slide-down"), 3000); // desaparece depois de 3s
});
