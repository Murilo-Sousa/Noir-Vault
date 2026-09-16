const socket = io();

socket.on('connect', () => {
  console.log('✅ Conectado ao servidor Socket.IO!');
  socket.emit("carregar_produtos");
});

socket.on("open_modal", () => {
  openModal()
});

socket.on("change_page", (data) => {
  window.location.href = data.url
})

socket.on("renderizar_produtos", data => {
  const container = document.querySelector('.roupas-container');
  container.innerHTML = ""; // limpa antes de renderizar

  console.log("PRODUTOS:", data.produtos);

  data.produtos.forEach(produto => {

    // garante que existam fotos
    let imagemPrincipal = "/static/assets/placeholder.png";
    if (produto.fotos && produto.fotos.length >= 1) {
      imagemPrincipal = `/static/assets/${produto.fotos[0]}`;
      imagemSecundaria = `/static/assets/${produto.fotos[1]}`
    }

    const card = `
            <div class="clothe" data-produto='${JSON.stringify(produto)}'>
                <h1>${produto.nome}</h1>
                <div class="decoration"></div>

                <div class="card">
                    <img src="${imagemPrincipal}" alt="${produto.nome}" class="img img-1">
                    <img src="${imagemSecundaria}" alt="${produto.nome}" class="img img-2">
                </div>

                <i class="fa-solid fa-heart" id="icon-roupa"></i>
            </div>
        `;

    container.insertAdjacentHTML("beforeend", card);
  });
});

document.addEventListener("click", (e) => {
    const wrapper = e.target.closest(".clothe");
    if (!wrapper) return;

    const produto = JSON.parse(wrapper.dataset.produto);

    // Salvar no LocalStorage
    localStorage.setItem("produtoSelecionado", JSON.stringify(produto));

    window.location.href = '/visualizar'
});



function loginCheck(url) {
  socket.emit('login_check', { 'url': url })
}

function openModal() {
  let div = document.querySelector(".modal");
  let fundo = document.querySelector(".overlay");
  let header = document.querySelector(".menu-container");
  let img = document.querySelector(".hero-image");
  let container = document.querySelector(".hero");
  let title = document.querySelector(".titleHero");
  let subtitles = document.querySelectorAll(".filter");
  let roupas = document.querySelectorAll(".img")

  subtitles.forEach((subtitle) => {
    subtitle.style.position = "static";
  });

  roupas.forEach((roupa) => {
    roupa.style.position = "static";
  })

  title.style.zIndex = "initial";
  title.style.mixBlendMode = "initial";
  container.style.position = "static";
  header.style.position = "static";
  header.style.isolation = "initial";
  img.style.position = "static";
  img.style.zIndex = "initial";

  div.classList.add("visible");
  fundo.classList.add("visible");
}

function closeModal() {
  let div = document.querySelector(".modal");
  let fundo = document.querySelector(".overlay");
  let header = document.querySelector(".menu-container");
  let img = document.querySelector(".hero-image");
  let container = document.querySelector(".hero");
  let title = document.querySelector(".titleHero");
  let subtitles = document.querySelectorAll(".filter");

  subtitles.forEach((subtitle) => {
    subtitle.style.position = "relative";
  });

  title.style.zIndex = "1";
  title.style.mixBlendMode = "darken";
  container.style.position = "relative";
  header.style.position = "sticky";
  header.style.isolation = "isolate";
  img.style.position = "absolute";
  img.style.zIndex = "2";

  div.classList.remove("visible");
  fundo.classList.remove("visible");
}

const erro = document.getElementById("erro-msg")?.dataset.erro === "true";

if (erro) {
  openModal()
}
