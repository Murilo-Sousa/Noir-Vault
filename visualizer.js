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
    opcao1.textContent = 'PP'
    opcao2.textContent = 'P'
    opcao3.textContent = 'M'
    opcao4.textContent = 'G'
  }

  fotoPrincipal.src = '/static/assets/' + produto.fotos[0]
  foto2.src = '/static/assets/' + produto.fotos[1]
  foto3.src = '/static/assets/' + produto.fotos[2]
  foto4.src = '/static/assets/' + produto.fotos[3]
  containerNome.textContent = produto.nome
  subtitle.textContent = produto.nome
  price.textContent = 'R$' + produto.preco
  let valorParcela = produto.preco / 12
  parcelas.textContent = `12 x R$${valorParcela.toFixed(2)}`
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