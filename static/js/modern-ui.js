// Fonctionnalités UI modernes pour RedirectionTracer
document.addEventListener('DOMContentLoaded', function() {
    // Gestion du mode sombre
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const body = document.body;
    
    // Vérifier si le mode sombre est enregistré dans localStorage
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    
    // Appliquer le mode sombre si nécessaire
    if (isDarkMode) {
        body.classList.add('dark-mode');
        if (darkModeToggle) {
            darkModeToggle.innerHTML = '<i data-feather="sun"></i>';
        }
    }
    
    // Gestionnaire d'événement pour le bouton de mode sombre
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-mode');
            const isDark = body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDark);
            
            // Changer l'icône
            darkModeToggle.innerHTML = isDark 
                ? '<i data-feather="sun"></i>' 
                : '<i data-feather="moon"></i>';
                
            // Réinitialiser les icônes Feather
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        });
    }
    
    // Initialiser les icônes Feather
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Gestion des filtres
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterType = this.dataset.filter;
            const filterValue = this.dataset.value;
            
            // Mettre à jour la classe active pour les boutons du même groupe
            const filterGroup = this.dataset.group;
            document.querySelectorAll(`.filter-btn[data-group="${filterGroup}"]`).forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            // Animer le bouton
            this.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                this.classList.remove('animate__animated', 'animate__pulse');
            }, 500);
            
            // Déclencher l'événement HTMX pour filtrer les résultats
            if (filterType && filterValue) {
                const taskId = document.getElementById('task-id').value;
                // Utiliser l'URL correcte qui correspond à la route dans routes.py
                let url = `/api/task/${taskId}/filter?${filterType}=${filterValue}`;
                
                console.log('DEBUG - Filtrage avec URL:', url);
                
                // Afficher l'indicateur de chargement
                const resultsTableBody = document.getElementById('results-table-body');
                if (resultsTableBody) {
                    resultsTableBody.innerHTML = '<tr><td colspan="6" class="text-center"><div style="padding: 2rem 0;"><div class="loading-spinner"></div><p>Filtrage des résultats...</p></div></td></tr>';
                }
                
                // Utiliser fetch pour obtenir les résultats filtrés
                fetch(url)
                    .then(response => {
                        console.log('DEBUG - Réponse du serveur:', response.status);
                        return response.text();
                    })
                    .then(html => {
                        console.log('DEBUG - HTML reçu:', html.substring(0, 100) + '...');
                        if (resultsTableBody) {
                            resultsTableBody.innerHTML = html;
                            // Réinitialiser les icônes Feather après le chargement du contenu
                            if (typeof feather !== 'undefined') {
                                feather.replace();
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Erreur lors du filtrage:', error);
                        if (resultsTableBody) {
                            resultsTableBody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="error-message">Erreur lors du filtrage des résultats.</div></td></tr>';
                        }
                    });
            }
        });
    });
    
    // Gestionnaire pour l'exportation des résultats
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.dataset.format;
            const filtered = this.dataset.filtered === 'true';
            const taskId = document.getElementById('task-id').value;
            
            let url = `/export/${taskId}/${format}`;
            if (filtered) {
                const statusFilter = document.querySelector('.filter-btn[data-group="status"].active').dataset.value;
                const codeFilter = document.querySelector('.filter-btn[data-group="code"].active')?.dataset.value || 'all';
                url += `/${statusFilter}/${codeFilter}`;
            }
            
            // Rediriger vers l'URL d'exportation
            window.location.href = url;
        });
    });
    
    // Animations au chargement
    document.querySelectorAll('.stats-card').forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('animate__animated', 'animate__fadeInUp');
            setTimeout(() => {
                card.classList.remove('animate__animated', 'animate__fadeInUp');
            }, 800);
        }, index * 150);
    });
    
    // Initialisation du graphique si Chart.js est disponible
    if (typeof Chart !== 'undefined' && document.getElementById('results-chart')) {
        const ctx = document.getElementById('results-chart').getContext('2d');
        
        // Récupérer les données des statistiques
        const correctCount = parseInt(document.getElementById('correct-count').textContent);
        const incorrectCount = parseInt(document.getElementById('incorrect-count').textContent);
        const errorCount = parseInt(document.getElementById('error-count').textContent);
        const multipleCount = parseInt(document.getElementById('multiple-count').textContent);
        
        // Créer le graphique en donut
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Correctes', 'Incorrectes', 'Erreurs', 'Multiples'],
                datasets: [{
                    data: [correctCount, incorrectCount, errorCount, multipleCount],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.7)',  // Vert
                        'rgba(249, 115, 22, 0.7)',  // Orange
                        'rgba(239, 68, 68, 0.7)',   // Rouge
                        'rgba(139, 92, 246, 0.7)'   // Violet
                    ],
                    borderColor: [
                        'rgba(16, 185, 129, 1)',
                        'rgba(249, 115, 22, 1)',
                        'rgba(239, 68, 68, 1)',
                        'rgba(139, 92, 246, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: {
                                family: 'DM Sans',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.8)',
                        titleFont: {
                            family: 'DM Sans',
                            size: 14
                        },
                        bodyFont: {
                            family: 'DM Sans',
                            size: 13
                        },
                        padding: 12,
                        cornerRadius: 8
                    }
                }
            }
        });
    }
});
