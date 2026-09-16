const socket = io();

socket.on('connect', () => {
  console.log('✅ Conectado ao servidor Socket.IO!');
  socket.emit("carregar_produtos");
});

function removerItem(produtoId) {
    socket.emit('removerProduto', { 'produtoId': produtoId })
    window.location.href = '/carrinho'
}