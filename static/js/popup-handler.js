// Gestion du popup de détails de redirection

function showRedirectionDetails(row) {
    // Récupérer les données de la ligne
    const lineNum = row.getAttribute('data-line-num');
    const source = row.getAttribute('data-source');
    const target = row.getAttribute('data-target');
    const final = row.getAttribute('data-final');
    const redirectionsCount = row.getAttribute('data-redirections-count');
    const httpStatus = row.getAttribute('data-http-status');
    const targetStatus = row.getAttribute('data-target-status');
    const status = row.getAttribute('data-status');
    const conclusion = row.getAttribute('data-conclusion');

    // Remplir le popup avec les données
    document.getElementById('popup-source-url').textContent = source;
    document.getElementById('popup-target-url').textContent = target;
    document.getElementById('popup-final-url').textContent = final;
    document.getElementById('popup-redirections-count').textContent = redirectionsCount;
    
    // Ajouter les codes HTTP avec la classe appropriée
    const httpStatusElement = document.getElementById('popup-http-status');
    httpStatusElement.textContent = 'HTTP ' + httpStatus;
    httpStatusElement.className = 'http-code';
    if (httpStatus >= 200 && httpStatus < 300) {
        httpStatusElement.classList.add('badge-success');
    } else if (httpStatus >= 300 && httpStatus < 400) {
        httpStatusElement.classList.add('badge-warning');
    } else {
        httpStatusElement.classList.add('badge-error');
    }

    const targetStatusElement = document.getElementById('popup-target-status');
    targetStatusElement.textContent = 'HTTP ' + targetStatus;
    targetStatusElement.className = 'http-code';
    if (targetStatus >= 200 && targetStatus < 300) {
        targetStatusElement.classList.add('badge-success');
    } else if (targetStatus >= 300 && targetStatus < 400) {
        targetStatusElement.classList.add('badge-warning');
    } else {
        targetStatusElement.classList.add('badge-error');
    }

    // Ajouter la conclusion avec la classe appropriée
    const conclusionElement = document.getElementById('popup-conclusion');
    conclusionElement.textContent = conclusion;
    conclusionElement.className = 'conclusion-text';
    if (status === 'CORRECT') {
        conclusionElement.classList.add('badge-success');
    } else if (status === 'INCORRECT') {
        conclusionElement.classList.add('badge-warning');
    } else {
        conclusionElement.classList.add('badge-error');
    }

    // Afficher le popup
    const popup = document.getElementById('redirection-details-popup');
    popup.style.display = 'flex';

    // Empêcher le défilement de la page
    document.body.style.overflow = 'hidden';
}

// Fermer le popup quand on clique sur le bouton de fermeture
document.addEventListener('DOMContentLoaded', function() {
    const closeButtons = document.querySelectorAll('.close-popup');
    closeButtons.forEach(button => {
        button.addEventListener('click', closePopup);
    });

    // Fermer le popup quand on clique en dehors
    const popup = document.getElementById('redirection-details-popup');
    popup.addEventListener('click', function(event) {
        if (event.target === popup) {
            closePopup();
        }
    });

    // Fermer le popup avec la touche Echap
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closePopup();
        }
    });
});

function closePopup() {
    const popup = document.getElementById('redirection-details-popup');
    popup.style.display = 'none';
    
    // Réactiver le défilement de la page
    document.body.style.overflow = 'auto';
}
