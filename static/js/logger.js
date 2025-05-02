/**
 * Utilitaire de logging frontend pour RedirectionTracer
 * Permet d'envoyer les logs du frontend vers le backend pour centraliser les logs
 */

// Classe Logger pour gérer les logs frontend
class FrontendLogger {
    constructor(options = {}) {
        this.options = {
            endpoint: '/api/logs',
            appName: 'RedirectionTracer',
            batchSize: 10,
            batchTimeMs: 2000,
            consoleOutput: true,
            ...options
        };
        
        this.logQueue = [];
        this.timer = null;
        this.isSending = false;
        
        // Démarrer le timer pour l'envoi périodique des logs
        this._startTimer();
        
        // Intercepter les erreurs non gérées
        this._setupErrorHandling();
        
        console.log(`[${this.options.appName}] Logger initialisé`);
    }
    
    /**
     * Envoie un log de niveau INFO
     * @param {string} message - Message à logger
     * @param {Object} context - Contexte additionnel (optionnel)
     */
    info(message, context = null) {
        this._log('info', message, context);
    }
    
    /**
     * Envoie un log de niveau WARNING
     * @param {string} message - Message à logger
     * @param {Object} context - Contexte additionnel (optionnel)
     */
    warn(message, context = null) {
        this._log('warning', message, context);
    }
    
    /**
     * Envoie un log de niveau ERROR
     * @param {string} message - Message à logger
     * @param {Object} context - Contexte additionnel (optionnel)
     */
    error(message, context = null) {
        this._log('error', message, context);
    }
    
    /**
     * Envoie un log de niveau DEBUG
     * @param {string} message - Message à logger
     * @param {Object} context - Contexte additionnel (optionnel)
     */
    debug(message, context = null) {
        this._log('debug', message, context);
    }
    
    /**
     * Fonction interne pour gérer tous les logs
     * @private
     */
    _log(level, message, context) {
        const logEntry = {
            level,
            message,
            context,
            timestamp: new Date().toISOString()
        };
        
        // Afficher dans la console si activé
        if (this.options.consoleOutput) {
            const consoleMethod = level === 'error' ? 'error' : 
                                 level === 'warning' ? 'warn' : 
                                 level === 'debug' ? 'debug' : 'log';
            
            console[consoleMethod](`[${this.options.appName}] ${message}`, context || '');
        }
        
        // Ajouter à la file d'attente
        this.logQueue.push(logEntry);
        
        // Envoyer immédiatement si c'est une erreur ou si la file est pleine
        if (level === 'error' || this.logQueue.length >= this.options.batchSize) {
            this._sendLogs();
        }
    }
    
    /**
     * Envoie les logs au serveur
     * @private
     */
    async _sendLogs() {
        if (this.isSending || this.logQueue.length === 0) return;
        
        this.isSending = true;
        const logsToSend = [...this.logQueue];
        this.logQueue = [];
        
        try {
            // Envoyer les logs un par un pour éviter les problèmes de taille
            for (const log of logsToSend) {
                await fetch(this.options.endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(log)
                });
            }
        } catch (error) {
            // En cas d'erreur, remettre les logs dans la file et afficher l'erreur
            console.error(`[${this.options.appName}] Erreur lors de l'envoi des logs:`, error);
            this.logQueue = [...logsToSend, ...this.logQueue];
        } finally {
            this.isSending = false;
        }
    }
    
    /**
     * Démarre le timer pour l'envoi périodique des logs
     * @private
     */
    _startTimer() {
        this.timer = setInterval(() => {
            if (this.logQueue.length > 0) {
                this._sendLogs();
            }
        }, this.options.batchTimeMs);
    }
    
    /**
     * Configure la capture des erreurs non gérées
     * @private
     */
    _setupErrorHandling() {
        window.addEventListener('error', (event) => {
            this.error(`Erreur non gérée: ${event.message}`, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error ? event.error.stack : null
            });
            
            // Ne pas bloquer l'erreur
            return false;
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.error(`Promesse rejetée non gérée`, {
                reason: event.reason ? event.reason.toString() : 'Raison inconnue',
                stack: event.reason && event.reason.stack ? event.reason.stack : null
            });
        });
    }
    
    /**
     * Nettoie les ressources du logger
     */
    destroy() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        
        // Envoyer les logs restants
        if (this.logQueue.length > 0) {
            this._sendLogs();
        }
    }
}

// Créer une instance globale du logger
const logger = new FrontendLogger();

// Exporter le logger pour une utilisation dans d'autres fichiers
window.logger = logger;
