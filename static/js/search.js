// Fonctionnalité de recherche par URL ou mot-clé

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('url-search');
    const searchButton = document.getElementById('search-button');
    const clearButton = document.getElementById('search-clear');
    const resultsTableBody = document.getElementById('results-table-body');
    
    // Fonction pour effectuer la recherche
    function performSearch() {
        const searchTerm = searchInput.value.trim().toLowerCase();
        
        // Si le champ de recherche est vide, réinitialiser l'affichage
        if (searchTerm === '') {
            clearSearch();
            return;
        }
        
        // Afficher le bouton de suppression
        clearButton.style.display = 'block';
        
        // Récupérer toutes les lignes du tableau
        const rows = resultsTableBody.querySelectorAll('tr');
        let hasResults = false;
        
        // Parcourir chaque ligne pour vérifier si elle contient le terme de recherche
        rows.forEach(row => {
            // Récupérer les cellules contenant les URLs
            const sourceCell = row.querySelector('td:nth-child(2)');
            const targetCell = row.querySelector('td:nth-child(3)');
            const finalCell = row.querySelector('td:nth-child(4)');
            
            if (!sourceCell || !targetCell || !finalCell) return;
            
            const sourceText = sourceCell.textContent.toLowerCase();
            const targetText = targetCell.textContent.toLowerCase();
            const finalText = finalCell.textContent.toLowerCase();
            
            // Vérifier si l'une des cellules contient le terme de recherche
            const isMatch = sourceText.includes(searchTerm) || 
                           targetText.includes(searchTerm) || 
                           finalText.includes(searchTerm);
            
            // Afficher ou masquer la ligne en fonction du résultat
            if (isMatch) {
                row.style.display = '';
                hasResults = true;
                
                // Surligner les correspondances
                highlightMatches(sourceCell, searchTerm);
                highlightMatches(targetCell, searchTerm);
                highlightMatches(finalCell, searchTerm);
            } else {
                row.style.display = 'none';
            }
        });
        
        // Afficher un message si aucun résultat n'est trouvé
        if (!hasResults && rows.length > 0) {
            // Vérifier si le message "Aucun résultat" existe déjà
            let noResultsRow = resultsTableBody.querySelector('.no-search-results');
            
            if (!noResultsRow) {
                // Créer une nouvelle ligne pour le message
                noResultsRow = document.createElement('tr');
                noResultsRow.className = 'no-search-results';
                noResultsRow.innerHTML = `
                    <td colspan="6" class="text-center">
                        <div style="padding: 2rem 0;">
                            <p style="font-size: 1rem; color: var(--text-tertiary);">Aucun résultat ne correspond à votre recherche</p>
                        </div>
                    </td>
                `;
                resultsTableBody.appendChild(noResultsRow);
            } else {
                noResultsRow.style.display = '';
            }
        } else {
            // Masquer le message "Aucun résultat" s'il existe
            const noResultsRow = resultsTableBody.querySelector('.no-search-results');
            if (noResultsRow) {
                noResultsRow.style.display = 'none';
            }
        }
    }
    
    // Fonction pour surligner les correspondances dans une cellule
    function highlightMatches(cell, searchTerm) {
        // Récupérer le contenu de la cellule
        const originalContent = cell.textContent;
        
        // Créer une expression régulière pour trouver toutes les occurrences du terme de recherche (insensible à la casse)
        const regex = new RegExp(searchTerm, 'gi');
        
        // Remplacer toutes les occurrences par la même chaîne entourée d'une balise span
        const highlightedContent = originalContent.replace(regex, match => `<span class="highlight-match">${match}</span>`);
        
        // Mettre à jour le contenu de la cellule si des correspondances ont été trouvées
        if (highlightedContent !== originalContent) {
            // Préserver la structure des tooltips
            const tooltipText = cell.querySelector('.tooltip-text');
            const tooltipContent = tooltipText ? tooltipText.textContent : '';
            
            // Mettre à jour le contenu de la cellule
            cell.innerHTML = `
                <span class="url-text">${highlightedContent}</span>
                ${tooltipText ? `<span class="tooltip-text">${tooltipContent}</span>` : ''}
            `;
        }
    }
    
    // Fonction pour effacer la recherche et réinitialiser l'affichage
    function clearSearch() {
        searchInput.value = '';
        clearButton.style.display = 'none';
        
        // Afficher toutes les lignes
        const rows = resultsTableBody.querySelectorAll('tr');
        rows.forEach(row => {
            if (!row.classList.contains('no-search-results')) {
                row.style.display = '';
            }
        });
        
        // Masquer le message "Aucun résultat"
        const noResultsRow = resultsTableBody.querySelector('.no-search-results');
        if (noResultsRow) {
            noResultsRow.style.display = 'none';
        }
        
        // Supprimer les surlignages
        const highlightedElements = resultsTableBody.querySelectorAll('.highlight-match');
        highlightedElements.forEach(el => {
            const parent = el.parentNode;
            parent.textContent = parent.textContent; // Astuce pour supprimer le HTML et garder le texte
        });
    }
    
    // Événement de clic sur le bouton de recherche
    searchButton.addEventListener('click', performSearch);
    
    // Événement de clic sur le bouton de suppression
    clearButton.addEventListener('click', clearSearch);
    
    // Événement de saisie dans le champ de recherche (recherche en temps réel)
    searchInput.addEventListener('input', function() {
        // Afficher ou masquer le bouton de suppression
        clearButton.style.display = this.value.trim() !== '' ? 'block' : 'none';
        
        // Effectuer la recherche après un court délai pour éviter trop de calculs
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(performSearch, 300);
    });
    
    // Événement de touche Entrée dans le champ de recherche
    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            performSearch();
        } else if (event.key === 'Escape') {
            clearSearch();
        }
    });
});
