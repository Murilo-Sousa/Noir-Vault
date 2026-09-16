
document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('fade-in');

    document.querySelectorAll('a[href]').forEach(link => {
        link.addEventListener('click', (event) => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('/') || href.endsWith('.html')) { // Only handle internal links
                event.preventDefault();
                document.body.classList.remove('fade-in');
                document.body.classList.add('fade-out'); // Add a fade-out class if desired
                setTimeout(() => {
                    window.location.href = href;
                }, 500); // Match this duration to your CSS transition duration
            }
        });
    });
});

