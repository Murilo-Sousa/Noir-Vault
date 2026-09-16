const socket = io();

socket.on('connect', () => {
  console.log('✅ Conectado ao servidor Socket.IO!');
});

socket.on("open_modal", () => {
  openModal()
});

socket.on("adicionar_roupa", () => {
  adicionarCarrinho()
  openModalRoupa()
})

socket.on("adicionar_wishlist", () => {
  adicionarWishlist()
  openModalRoupa()
})

socket.on("change_page", (data) => {
  window.location.href = data.url
})

document.querySelectorAll('.acc-item').forEach(item => {
  const btn = item.querySelector('.acc-header');
  const content = item.querySelector('.acc-content');

  btn.addEventListener('click', () => {
    if (item.classList.contains('active')) {
      item.classList.remove('active');
      content.style.maxHeight = null;
    } else {
      document.querySelectorAll('.acc-item').forEach(i => {
        i.classList.remove('active');
        i.querySelector('.acc-content').style.maxHeight = null;
      });
      item.classList.add('active');
      content.style.maxHeight = content.scrollHeight + "px";
    }
  });
});

const produto = JSON.parse(localStorage.getItem("produtoSelecionado"));

function carregarProduto() {
  if (!produto) {
    window.location.href = '/';
    return;
  }
  const fotoPrincipal = document.querySelector('.foto1')
  const foto2 = document.querySelector('.foto2')
  const foto3 = document.querySelector('.foto3')
  const foto4 = document.querySelector('.foto4')
  const containerNome = document.querySelector('.brand')
  const subtitle = document.querySelector('.subtitle')
  const price = document.querySelector('.price')
  const parcelas = document.querySelector('.installments')
  const opcao1 = document.querySelector('.option1')
  const opcao2 = document.querySelector('.option2')
  const opcao3 = document.querySelector('.option3')
  const opcao4 = document.querySelector('.option4')

  if (produto.tipo != 'Bota') {
    if (opcao1) opcao1.textContent = 'PP'
    if (opcao2) opcao2.textContent = 'P'
    if (opcao3) opcao3.textContent = 'M'
    if (opcao4) opcao4.textContent = 'G'
  }

  const fotos = (produto.fotos && produto.fotos.length > 0) ? produto.fotos : ['placeholder.png'];
  if (fotoPrincipal) fotoPrincipal.src = '/static/assets/' + (fotos[0] || 'placeholder.png')
  if (foto2) foto2.src = '/static/assets/' + (fotos[1] || fotos[0] || 'placeholder.png')
  if (foto3) foto3.src = '/static/assets/' + (fotos[2] || fotos[0] || 'placeholder.png')
  if (foto4) foto4.src = '/static/assets/' + (fotos[3] || fotos[0] || 'placeholder.png')
  if (containerNome) containerNome.textContent = produto.nome || ''
  if (subtitle) subtitle.textContent = produto.nome || ''
  if (price) price.textContent = 'R$' + (produto.preco || 0)
  let valorParcela = (produto.preco || 0) / 12
  if (parcelas) parcelas.textContent = `12 x R$${valorParcela.toFixed(2)}`
  console.log(produto)
}

function buscarUser(func) {
  socket.emit('buscarUser', { rota: func, 'produto': produto.produto_id })
}

function adicionarCarrinho() {
  const tamanhoContainer = document.querySelector('.tamanho')
  socket.emit('adicionarCarrinho', { 'produto': produto, 'tamanho': tamanhoContainer.value } )
}

function adicionarWishlist() {
  socket.emit('adicionarWishlist', { 'produto': produto })
}

function openModalRoupa() {
  const cardRoupa = document.querySelector('.main-photo')
  const div = document.querySelector('.modal-roupa')

  cardRoupa.style.position = 'static'
  div.style.display = 'flex'
}

function closeModalRoupa() {
  const div = document.querySelector('.modal-roupa')

  div.style.display = 'none'
}

function loginCheck(url) {
  socket.emit('login_check', { 'url': url })
}

function openModal() {
  let div = document.querySelector(".modal");
  let fundo = document.querySelector(".overlay");
  let header = document.querySelector(".menu-container");
  let foto = document.querySelector(".main-photo")
  let imagens = document.querySelectorAll(".product-thumb")

  imagens.forEach((img) => {
    img.style.position = "static";
  })

  header.style.position = "static";
  header.style.isolation = "initial";
  header.style.zIndex = "initial"
  foto.style.position = "static"

  div.classList.add("visible");
  fundo.classList.add("visible");
}

function closeModal() {
  let div = document.querySelector(".modal");
  let fundo = document.querySelector(".overlay");
  let header = document.querySelector(".menu-container");

  header.style.position = "sticky";
  header.style.isolation = "isolate";

  div.classList.remove("visible");
  fundo.classList.remove("visible");
}

document.addEventListener("DOMContentLoaded", (e) => {
  carregarProduto()
})