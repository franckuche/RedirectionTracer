/**
 * Script personnalisé pour appliquer les styles de la sidebar
 * Ce script s'exécute après le chargement de la page et force l'application des styles
 */
document.addEventListener('DOMContentLoaded', function() {
    // Fonction pour appliquer les styles de la sidebar
    function applySidebarStyles() {
        // Supprimer les titres de section
        document.querySelectorAll('.sidebar-section-title, h3.text-xs.font-semibold.text-gray-500.uppercase.tracking-wider').forEach(title => {
            title.style.display = 'none';
        });

        // Styliser le bouton de déconnexion
        const logoutButtons = document.querySelectorAll('#sidebar-logout-btn, #logout-btn, button[id*="logout"]');
        logoutButtons.forEach(button => {
            button.classList.add('bg-red-500', 'hover:bg-red-600', 'text-white', 'rounded-xl', 'py-2', 'px-4', 'font-medium', 'w-3/4', 'mx-auto', 'block', 'transition');
            button.style.backgroundColor = '#ef4444';
            button.style.color = 'white';
            button.style.borderRadius = '12px';
            button.style.padding = '8px 16px';
            button.style.fontWeight = '500';
            button.style.width = '75%';
            button.style.textAlign = 'center';
            button.style.margin = '1rem auto';
            button.style.display = 'block';
            button.style.border = 'none';
            button.style.cursor = 'pointer';
        });

        // Styliser la sidebar
        const sidebar = document.querySelector('#sidebar, aside.fixed');
        if (sidebar) {
            sidebar.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
            sidebar.style.backdropFilter = 'blur(10px)';
            sidebar.style.WebkitBackdropFilter = 'blur(10px)';
            sidebar.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.1)';
            sidebar.style.border = 'none';
        }

        // Centrer les boutons d'authentification
        const authSections = document.querySelectorAll('#auth-section, div[id*="auth"]');
        authSections.forEach(section => {
            section.style.display = 'flex';
            section.style.flexDirection = 'column';
            section.style.alignItems = 'center';
            section.style.marginTop = 'auto';
            section.style.padding = '1rem';
        });

        // Styliser les liens de la sidebar
        const sidebarLinks = document.querySelectorAll('.sidebar-link, aside a');
        sidebarLinks.forEach(link => {
            link.style.borderRadius = '12px';
            link.style.transition = 'all 0.2s ease';
            link.style.marginBottom = '4px';
        });
    }

    // Appliquer les styles immédiatement
    applySidebarStyles();

    // Observer les changements dans le DOM pour réappliquer les styles si nécessaire
    // Cela est utile si le contenu de la sidebar est modifié dynamiquement par d'autres scripts
    const observer = new MutationObserver(function(mutations) {
        applySidebarStyles();
    });

    // Observer le document entier pour les changements
    observer.observe(document.body, { 
        childList: true,
        subtree: true
    });

    // Réappliquer les styles toutes les 500ms pendant 5 secondes
    // Cela garantit que nos styles sont appliqués même si d'autres scripts les écrasent
    let count = 0;
    const interval = setInterval(function() {
        applySidebarStyles();
        count++;
        if (count >= 10) {
            clearInterval(interval);
        }
    }, 500);
});
