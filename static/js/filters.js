// Gestion des filtres pour les résultats de redirection

document.addEventListener('DOMContentLoaded', function() {
    // Récupérer tous les boutons de filtre
    const filterButtons = document.querySelectorAll('.filter-btn');
    const taskId = document.getElementById('task-id').value;
    
    // Ajouter un écouteur d'événement pour chaque bouton de filtre
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Récupérer les attributs de filtre
            const filterType = this.getAttribute('data-filter');
            const filterValue = this.getAttribute('data-value');
            const filterGroup = this.getAttribute('data-group');
            
            // Désactiver tous les boutons du même groupe
            document.querySelectorAll(`.filter-btn[data-group="${filterGroup}"]`).forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Activer le bouton cliqué
            this.classList.add('active');
            
            // Récupérer les filtres actifs
            const activeFilters = {};
            document.querySelectorAll('.filter-btn.active').forEach(activeBtn => {
                const type = activeBtn.getAttribute('data-filter');
                const value = activeBtn.getAttribute('data-value');
                if (value !== 'all') {
                    activeFilters[type] = value;
                }
            });
            
            // Appeler l'API pour filtrer les résultats
            applyFilters(activeFilters);
        });
    });
    
    // Fonction pour appliquer les filtres via AJAX
    function applyFilters(filters) {
        // Construire l'URL avec les paramètres de filtre
        let url = `/api/task/${taskId}/filter?`;
        for (const [key, value] of Object.entries(filters)) {
            url += `${key}=${value}&`;
        }
        
        // Supprimer le dernier '&'
        url = url.slice(0, -1);
        
        // Afficher un indicateur de chargement
        const resultsTableBody = document.getElementById('results-table-body');
        resultsTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">
                    <div style="padding: 2rem 0;">
                        <div class="loading-spinner"></div>
                        <p style="font-size: 1rem; color: var(--text-tertiary);">Filtrage en cours...</p>
                    </div>
                </td>
            </tr>
        `;
        
        // Effectuer la requête AJAX
        fetch(url)
            .then(response => response.text())
            .then(html => {
                resultsTableBody.innerHTML = html;
            })
            .catch(error => {
                console.error('Erreur lors du filtrage:', error);
                resultsTableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center">
                            <div style="padding: 2rem 0;">
                                <p style="font-size: 1rem; color: var(--text-error);">Erreur lors du filtrage. Veuillez réessayer.</p>
                            </div>
                        </td>
                    </tr>
                `;
            });
    }
    
    // Gestion des boutons d'export
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.getAttribute('data-format');
            const filtered = this.getAttribute('data-filtered') === 'true';
            
            // Récupérer les filtres actifs si nécessaire
            let activeFilters = {};
            if (filtered) {
                document.querySelectorAll('.filter-btn.active').forEach(activeBtn => {
                    const type = activeBtn.getAttribute('data-filter');
                    const value = activeBtn.getAttribute('data-value');
                    if (value !== 'all') {
                        activeFilters[type] = value;
                    }
                });
            }
            
            // Construire l'URL d'export
            let exportUrl = `/export/${taskId}?format=${format}`;
            if (filtered) {
                for (const [key, value] of Object.entries(activeFilters)) {
                    exportUrl += `&${key}=${value}`;
                }
            }
            
            // Rediriger vers l'URL d'export
            window.location.href = exportUrl;
        });
    });
});
