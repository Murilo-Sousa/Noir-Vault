// Lista de imagens disponíveis (adicione os nomes dos seus arquivos)
const images = [
    'onça.png',
    'dog.png',
    'shark.png'
    // Adicione aqui todos os nomes dos arquivos das suas imagens
];

function getRandomImage() {
    // Recupera o histórico de imagens usadas
    const usedImages = JSON.parse(localStorage.getItem('usedImages') || '[]');
    
    // Se todas as imagens já foram usadas, reinicia o ciclo
    if (usedImages.length >= images.length) {
        usedImages.length = 0;
    }
    
    // Filtra as imagens que ainda não foram usadas
    const availableImages = images.filter(img => !usedImages.includes(img));
    
    // Seleciona uma imagem aleatória das disponíveis
    const randomIndex = Math.floor(Math.random() * availableImages.length);
    const selectedImage = availableImages[randomIndex];
    
    // Adiciona a imagem selecionada ao histórico
    usedImages.push(selectedImage);
    localStorage.setItem('usedImages', JSON.stringify(usedImages));
    
    return '/static/assets/' + selectedImage;
}

function updateImage() {
    const imgElement = document.getElementById('random-image');
    const randomImageSrc = getRandomImage();
    
    // Atualiza a src da imagem
    imgElement.src = randomImageSrc;
    
    // Atualiza o alt para corresponder à imagem
    const imageName = randomImageSrc.split('/').pop().split('.')[0];
    imgElement.alt = imageName.charAt(0).toUpperCase() + imageName.slice(1);
}

// Executa quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    updateImage();
});