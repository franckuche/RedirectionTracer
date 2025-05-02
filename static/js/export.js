/**
 * Script pour gérer l'export des résultats en CSV
 * Prend en compte les filtres actifs
 */

document.addEventListener('DOMContentLoaded', function() {
    // Récupérer le bouton d'export
    const exportBtn = document.querySelector('.export-btn');
    
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            // Récupérer l'ID de la tâche
            const taskId = document.getElementById('task-id').value;
            
            // Récupérer les filtres actifs
            const activeStatusFilter = document.querySelector('.filter-btn[data-group="status"].active');
            const activeCodeFilter = document.querySelector('.filter-btn[data-group="code"].active');
            
            // Récupérer la valeur de recherche
            const searchInput = document.getElementById('url-search');
            const searchValue = searchInput ? searchInput.value.trim() : '';
            
            // Construire l'URL pour l'export
            let exportUrl = `/api/task/${taskId}/export?format=csv`;
            
            // Ajouter les filtres actifs à l'URL
            if (activeStatusFilter && activeStatusFilter.dataset.value !== 'all') {
                exportUrl += `&status=${activeStatusFilter.dataset.value}`;
            }
            
            if (activeCodeFilter && activeCodeFilter.dataset.value !== 'all') {
                exportUrl += `&http_code=${activeCodeFilter.dataset.value}`;
            }
            
            // Ajouter la recherche si elle existe
            if (searchValue) {
                exportUrl += `&search=${encodeURIComponent(searchValue)}`;
            }
            
            // Rediriger vers l'URL d'export
            window.location.href = exportUrl;
        });
    }
});
