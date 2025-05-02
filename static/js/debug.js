/**
 * Utilitaires de débogage pour RedirectionTracer
 */

// Activer les logs détaillés
const DEBUG = true;

// Logger personnalisé avec horodatage
const Logger = {
    log: function(message, data) {
        if (!DEBUG) return;
        
        const timestamp = new Date().toISOString();
        const formattedMessage = `[${timestamp}] ${message}`;
        
        if (data) {
            console.log(formattedMessage, data);
        } else {
            console.log(formattedMessage);
        }
        
        // Ajouter au log visuel si disponible
        this.appendToVisualLog(formattedMessage, data);
    },
    
    error: function(message, error) {
        const timestamp = new Date().toISOString();
        const formattedMessage = `[${timestamp}] ERROR: ${message}`;
        
        console.error(formattedMessage, error);
        
        // Ajouter au log visuel si disponible
        this.appendToVisualLog(formattedMessage, error, 'error');
    },
    
    warn: function(message, data) {
        if (!DEBUG) return;
        
        const timestamp = new Date().toISOString();
        const formattedMessage = `[${timestamp}] WARNING: ${message}`;
        
        console.warn(formattedMessage, data);
        
        // Ajouter au log visuel si disponible
        this.appendToVisualLog(formattedMessage, data, 'warning');
    },
    
    // Ajouter un log à l'interface visuelle
    appendToVisualLog: function(message, data, type = 'info') {
        const logContainer = document.getElementById('debug-log-container');
        if (!logContainer) return;
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        
        // Créer le contenu du log
        let logContent = message;
        if (data) {
            try {
                if (typeof data === 'object') {
                    logContent += ': ' + JSON.stringify(data);
                } else {
                    logContent += ': ' + data;
                }
            } catch (e) {
                logContent += ': [Objet non sérialisable]';
            }
        }
        
        logEntry.textContent = logContent;
        logContainer.appendChild(logEntry);
        
        // Faire défiler vers le bas
        logContainer.scrollTop = logContainer.scrollHeight;
    },
    
    // Créer le conteneur de logs visuels
    createVisualLogContainer: function() {
        if (!DEBUG) return;
        
        // Vérifier si le conteneur existe déjà
        if (document.getElementById('debug-log-container')) return;
        
        // Créer le conteneur de logs
        const logContainer = document.createElement('div');
        logContainer.id = 'debug-log-container';
        logContainer.className = 'debug-log-container';
        logContainer.style.cssText = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            width: 400px;
            height: 200px;
            background-color: rgba(0, 0, 0, 0.8);
            color: #fff;
            font-family: monospace;
            font-size: 12px;
            padding: 10px;
            border-radius: 5px;
            overflow-y: auto;
            z-index: 9999;
            display: none;
        `;
        
        // Créer l'en-tête
        const header = document.createElement('div');
        header.className = 'debug-log-header';
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            padding-bottom: 5px;
            border-bottom: 1px solid #555;
        `;
        
        const title = document.createElement('span');
        title.textContent = 'Debug Logs';
        
        const closeButton = document.createElement('button');
        closeButton.textContent = 'X';
        closeButton.style.cssText = `
            background: none;
            border: none;
            color: #fff;
            cursor: pointer;
        `;
        closeButton.onclick = function() {
            logContainer.style.display = 'none';
        };
        
        header.appendChild(title);
        header.appendChild(closeButton);
        logContainer.appendChild(header);
        
        // Ajouter au body
        document.body.appendChild(logContainer);
        
        // Ajouter un bouton pour afficher/masquer les logs
        const toggleButton = document.createElement('button');
        toggleButton.id = 'debug-log-toggle';
        toggleButton.textContent = 'Logs';
        toggleButton.style.cssText = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            background-color: #3b82f6;
            color: #fff;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 12px;
            cursor: pointer;
            z-index: 9998;
        `;
        toggleButton.onclick = function() {
            const container = document.getElementById('debug-log-container');
            if (container) {
                container.style.display = container.style.display === 'none' ? 'block' : 'none';
            }
        };
        
        document.body.appendChild(toggleButton);
    }
};

// Initialiser le logger visuel au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    Logger.createVisualLogContainer();
    Logger.log('Debug logger initialisé');
});

// Intercepter les appels API pour les logger
const originalFetch = window.fetch;
window.fetch = function(url, options) {
    Logger.log(`Requête API: ${url}`, options);
    
    return originalFetch.apply(this, arguments)
        .then(response => {
            // Cloner la réponse pour pouvoir la lire
            const clonedResponse = response.clone();
            
            // Tenter de lire la réponse comme JSON
            clonedResponse.json().then(data => {
                Logger.log(`Réponse API: ${url}`, data);
            }).catch(() => {
                // Si ce n'est pas du JSON, logger juste le statut
                Logger.log(`Réponse API: ${url} - Statut: ${response.status}`);
            });
            
            return response;
        })
        .catch(error => {
            Logger.error(`Erreur API: ${url}`, error);
            throw error;
        });
};

// Exporter le logger
window.Logger = Logger;
