/**
 * API client pour RedirectionTracer
 * Ce fichier contient les fonctions pour interagir avec l'API backend
 */

// Fonction pour vérifier le statut d'une tâche
async function checkTaskStatus(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}/status`);
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Erreur lors de la vérification du statut:', error);
        throw error;
    }
}

// Fonction pour récupérer les résultats d'une tâche
async function getTaskResults(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}/results`);
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Erreur lors de la récupération des résultats:', error);
        throw error;
    }
}

// Fonction pour soumettre un fichier CSV
async function uploadCSV(formData) {
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Erreur lors de l\'upload:', error);
        throw error;
    }
}

// Fonction pour suivre la progression d'une tâche avec des callbacks
function trackTaskProgress(taskId, onProgress, onComplete, onError) {
    let pollInterval;
    
    const checkProgress = async () => {
        try {
            const status = await checkTaskStatus(taskId);
            
            // Appeler le callback de progression
            if (onProgress) {
                onProgress(status);
            }
            
            // Si la tâche est terminée
            if (status.status === 'completed') {
                clearInterval(pollInterval);
                
                // Récupérer les résultats
                const results = await getTaskResults(taskId);
                
                // Appeler le callback de complétion
                if (onComplete) {
                    onComplete(results);
                }
            } 
            // Si la tâche a échoué
            else if (status.status === 'failed') {
                clearInterval(pollInterval);
                
                // Appeler le callback d'erreur
                if (onError) {
                    onError(new Error(status.message || 'La tâche a échoué'));
                }
            }
        } catch (error) {
            clearInterval(pollInterval);
            
            // Appeler le callback d'erreur
            if (onError) {
                onError(error);
            }
        }
    };
    
    // Vérifier la progression toutes les 1 seconde
    pollInterval = setInterval(checkProgress, 1000);
    
    // Faire une première vérification immédiatement
    checkProgress();
    
    // Retourner une fonction pour arrêter le suivi
    return () => {
        clearInterval(pollInterval);
    };
}
