const socket = io();

socket.on('connect', () => {
  console.log('✅ Conectado ao servidor Socket.IO!');
});


const toggleSidebar = document.getElementById("toggleSidebar");
const sidebar = document.getElementById("sidebar");
const body = document.body;
const links = document.querySelectorAll('a')
const line = document.querySelector('hr')

toggleSidebar.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    body.classList.toggle("sidebar-open");
    links.forEach(item => {
        item.classList.toggle('visible')
    })
    line.classList.toggle('visible')
});

// Foto do perfil
const input = document.getElementById("photoInput");
const profileImage = document.getElementById("profileImage");
const avatarDefault = document.getElementById("avatarDefault");

// Função para carregar a imagem salva ao iniciar a página
function loadSavedProfileImage() {
    const savedImage = localStorage.getItem('profileImage');
    
    if (savedImage) {
        profileImage.src = savedImage;
        profileImage.classList.remove("hidden");
        avatarDefault.style.display = "none";
    }
}

// Função para salvar a imagem no localStorage
function saveProfileImage(imageData) {
    localStorage.setItem('profileImage', imageData);
}

// Função para remover a imagem salva
function removeProfileImage() {
    localStorage.removeItem('profileImage');
}

// Event listener para quando uma nova imagem é selecionada
input.addEventListener("change", function () {
    const file = this.files[0];

    if (file) {
        const reader = new FileReader();

        reader.onload = function (e) {
            const imageData = e.target.result;
            
            // Atualizar a imagem na página
            profileImage.src = imageData;
            profileImage.classList.remove("hidden");
            avatarDefault.style.display = "none";
            
            // Salvar no localStorage
            saveProfileImage(imageData);
            socket.emit('salvarFoto', { 'url': imageData })
        };

        reader.readAsDataURL(file);
    }
});

// Função para remover a foto de perfil (opcional)
function removeProfilePhoto() {
    profileImage.classList.add("hidden");
    avatarDefault.style.display = "block";
    removeProfileImage();
    input.value = ''; // Limpar o input file
}

// Carregar a imagem salva quando a página carregar
document.addEventListener('DOMContentLoaded', loadSavedProfileImage);