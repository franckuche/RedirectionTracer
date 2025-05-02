/**
 * Script pour la page de résultats
 * Utilise l'API pour récupérer et afficher les résultats d'analyse
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser Alpine.js avec les données
    window.initializeAlpine = function(taskId) {
        return {
            taskId: taskId,
            loading: true,
            error: null,
            stats: null,
            details: [],
            statusFilters: ['all'],
            searchQuery: '',
            showDetails: null,
            httpStatusFilters: ['all'],
            
            // Initialiser les données
            async init() {
                try {
                    // Récupérer les résultats
                    const results = await getTaskResults(this.taskId);
                    
                    // Mettre à jour les données
                    this.stats = results.stats;
                    this.details = results.details.map((detail, index) => ({
                        ...detail,
                        index
                    }));
                    
                    this.loading = false;
                } catch (error) {
                    this.error = error.message;
                    this.loading = false;
                    console.error('Erreur lors du chargement des résultats:', error);
                }
            },
            
            // Propriété calculée pour les détails filtrés
            get filteredDetails() {
                return this.details.filter(detail => {
                    // Filtre par statut
                    const statusFilter = 
                        this.statusFilters.includes('all') || 
                        (this.statusFilters.includes('correct') && detail.status === 'CORRECT') || 
                        (this.statusFilters.includes('incorrect') && detail.status === 'INCORRECT') || 
                        (this.statusFilters.includes('error') && detail.status === 'ERREUR') || 
                        (this.statusFilters.includes('multi') && detail.redirections_count > 1);
                    
                    // Filtre par code HTTP
                    const httpFilter = 
                        this.httpStatusFilters.includes('all') || 
                        (this.httpStatusFilters.includes('2xx') && detail.http_status >= 200 && detail.http_status < 300) ||
                        (this.httpStatusFilters.includes('3xx') && detail.http_status >= 300 && detail.http_status < 400) ||
                        (this.httpStatusFilters.includes('4xx') && detail.http_status >= 400 && detail.http_status < 500) ||
                        (this.httpStatusFilters.includes('5xx') && detail.http_status >= 500);
                    
                    // Filtre par recherche
                    const searchFilter = 
                        !this.searchQuery || 
                        (detail.source && detail.source.toLowerCase().includes(this.searchQuery.toLowerCase())) || 
                        (detail.target && detail.target.toLowerCase().includes(this.searchQuery.toLowerCase())) || 
                        (detail.final && detail.final.toLowerCase().includes(this.searchQuery.toLowerCase()));
                    
                    return statusFilter && httpFilter && searchFilter;
                });
            },
            
            // Méthode pour basculer un filtre de statut
            toggleStatusFilter(filter) {
                if (filter === 'all') {
                    // Si 'all' est sélectionné, on désactive tous les autres filtres
                    this.statusFilters = ['all'];
                } else {
                    // Si 'all' est déjà dans le tableau, on le retire
                    if (this.statusFilters.includes('all')) {
                        this.statusFilters = this.statusFilters.filter(f => f !== 'all');
                    }
                    
                    // Si le filtre est déjà dans le tableau, on le retire, sinon on l'ajoute
                    if (this.statusFilters.includes(filter)) {
                        this.statusFilters = this.statusFilters.filter(f => f !== filter);
                        // Si aucun filtre n'est sélectionné, on remet 'all'
                        if (this.statusFilters.length === 0) {
                            this.statusFilters = ['all'];
                        }
                    } else {
                        this.statusFilters.push(filter);
                    }
                }
            },
            
            // Méthode pour basculer un filtre de code HTTP
            toggleHttpStatusFilter(filter) {
                if (filter === 'all') {
                    // Si 'all' est sélectionné, on désactive tous les autres filtres
                    this.httpStatusFilters = ['all'];
                } else {
                    // Si 'all' est déjà dans le tableau, on le retire
                    if (this.httpStatusFilters.includes('all')) {
                        this.httpStatusFilters = this.httpStatusFilters.filter(f => f !== 'all');
                    }
                    
                    // Si le filtre est déjà dans le tableau, on le retire, sinon on l'ajoute
                    if (this.httpStatusFilters.includes(filter)) {
                        this.httpStatusFilters = this.httpStatusFilters.filter(f => f !== filter);
                        // Si aucun filtre n'est sélectionné, on remet 'all'
                        if (this.httpStatusFilters.length === 0) {
                            this.httpStatusFilters = ['all'];
                        }
                    } else {
                        this.httpStatusFilters.push(filter);
                    }
                }
            },
            
            // Méthode pour exporter les résultats en CSV
            exportCSV() {
                // En-têtes
                let csvContent = "data:text/csv;charset=utf-8,";
                csvContent += "Ligne,URL Source,URL Target,URL Finale,Redirections,Statut,Code HTTP,Conclusion\n";
                
                // Utiliser les détails filtrés
                this.filteredDetails.forEach(detail => {
                    const values = [
                        detail.line,
                        `"${(detail.source || '').replace(/"/g, '""')}"`, 
                        `"${(detail.target || '').replace(/"/g, '""')}"`, 
                        `"${(detail.final || '').replace(/"/g, '""')}"`,
                        detail.redirections_count,
                        `"${(detail.status || '').replace(/"/g, '""')}"`,
                        detail.http_status || 0,
                        `"${(detail.conclusion || '').replace(/"/g, '""')}"` 
                    ];
                    csvContent += values.join(',') + '\n';
                });
                
                // Créer un lien de téléchargement
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.setAttribute('href', url);
                link.setAttribute('download', 'resultats_redirections.csv');
                link.style.visibility = 'hidden';
                
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            },
            
            // Initialiser le graphique
            initChart() {
                if (!this.stats) return;
                
                const ctx = document.getElementById('resultsChart').getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Redirections correctes', 'Redirections incorrectes', 'Erreurs', 'Redirections multiples'],
                        datasets: [{
                            label: '',
                            data: [
                                this.stats.correct_count,
                                this.stats.incorrect_count,
                                this.stats.error_count,
                                this.stats.multi_redirect_count
                            ],
                            backgroundColor: [
                                '#10b981', // success
                                '#ef4444', // danger
                                '#64748b', // secondary
                                '#f59e0b'  // warning
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    precision: 0
                                }
                            }
                        }
                    }
                });
            }
        };
    };
});
