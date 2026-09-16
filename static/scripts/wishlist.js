const socket = io();

socket.on('connect', () => {
  console.log('✅ Conectado ao servidor Socket.IO!');
  socket.emit("carregar_produtos");
});

const wrap = document.querySelector('.carousel-wrap');
const carousel = document.querySelector('.carousel');
const slider = document.getElementById('track');

function updateSliderRange() {
  const visibleWidth = wrap.clientWidth;
  const totalWidth = carousel.scrollWidth;
  const maxTranslate = Math.max(0, totalWidth - visibleWidth);

  slider.max = Math.round(maxTranslate);
  slider.value = Math.min(Number(slider.value || 0), slider.max);

  carousel.style.transform = `translateX(-${slider.value}px)`;
}

document.addEventListener("click", (e) => {
    const wrapper = e.target.closest(".card");
    if (!wrapper) return;

    const produto = JSON.parse(wrapper.dataset.produto);

    // Salvar no LocalStorage
    localStorage.setItem("produtoSelecionado", JSON.stringify(produto));

    window.location.href = '/visualizar'
});

slider.addEventListener('input', () => {
  carousel.style.transform = `translateX(-${slider.value}px)`;
});

function removerWishlist(produto_id) {
  socket.emit("removerWishlist", { 'id': produto_id })
  window.location.href = '/wishlist'
}

window.addEventListener('resize', updateSliderRange);
window.addEventListener('load', updateSliderRange);