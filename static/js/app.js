// Application Vue.js pour RedirectionTracer

// Composant pour la barre de progression
const ProgressBar = {
  props: {
    progress: {
      type: Number,
      required: true
    },
    status: {
      type: String,
      default: ''
    }
  },
  template: `
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="progress-text">
        {{ progress }}% {{ status ? '- ' + status : '' }}
      </div>
    </div>
  `
};

// Composant pour les logs
const LogViewer = {
  props: {
    logs: {
      type: Array,
      default: () => []
    }
  },
  template: `
    <div class="log-viewer">
      <h4 class="log-title">Logs</h4>
      <div class="log-container">
        <div v-for="(log, index) in logs" :key="index" class="log-entry">
          {{ log }}
        </div>
        <div v-if="logs.length === 0" class="log-empty">
          Aucun log disponible
        </div>
      </div>
    </div>
  `
};

// Composant pour les résultats
const ResultsViewer = {
  props: {
    results: {
      type: Object,
      default: null
    }
  },
  template: `
    <div v-if="results" class="results-container">
      <h3 class="results-title">Résultats de l'analyse</h3>
      
      <div class="stats-container">
        <div class="stat-item">
          <div class="stat-value">{{ results.total_urls }}</div>
          <div class="stat-label">URLs analysées</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ results.correct_redirects }}</div>
          <div class="stat-label">Redirections correctes</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ results.incorrect_redirects }}</div>
          <div class="stat-label">Redirections incorrectes</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ results.errors }}</div>
          <div class="stat-label">Erreurs</div>
        </div>
      </div>
      
      <div class="results-table-container">
        <table class="results-table">
          <thead>
            <tr>
              <th>Ligne</th>
              <th>URL Source</th>
              <th>URL Cible</th>
              <th>URL Finale</th>
              <th>Statut</th>
              <th>Conclusion</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(result, index) in results.details" :key="index" :class="getRowClass(result.status)">
              <td>{{ result.line_num }}</td>
              <td>{{ result.source_url }}</td>
              <td>{{ result.target_url }}</td>
              <td>{{ result.final_url }}</td>
              <td>{{ result.status_code }}</td>
              <td>{{ result.conclusion }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  methods: {
    getRowClass(status) {
      if (status === 'CORRECT') return 'status-correct';
      if (status === 'INCORRECT') return 'status-incorrect';
      return 'status-error';
    }
  }
};

// Application principale
const app = Vue.createApp({
  // Gestionnaire d'erreurs global pour Vue
  errorCaptured(err, vm, info) {
    // Utiliser notre logger pour enregistrer l'erreur
    if (window.logger) {
      window.logger.error(`Vue Error: ${err.message}`, {
        component: vm?.$options?.name || 'Unknown',
        info: info,
        stack: err.stack
      });
    }
    // Retourner false pour empêcher la propagation de l'erreur
    return false;
  },
  mounted() {
    // Ajouter un écouteur d'événement pour détecter les changements de fichier
    const fileInput = document.getElementById('csv-file');
    if (fileInput) {
      fileInput.addEventListener('change', this.handleFileChange);
    }
  },
  components: {
    ProgressBar,
    LogViewer,
    ResultsViewer
  },
  data() {
    return {
      isUploading: false,
      uploadProgress: 0,
      processingProgress: 0,
      taskId: null,
      taskStatus: '',
      taskMessage: '',
      taskStartTime: null,
      taskLogs: [],
      showProgressDetails: false,
      results: null,
      error: null,
      retryCount: 0,
      lastProgress: 0,
      lastMessage: '',
      selectedFile: null,
      fileSelected: false
    };
  },
  methods: {
    handleFileChange(event) {
      const file = event.target.files[0];
      if (file) {
        this.selectedFile = file;
        this.fileSelected = true;
        this.error = null; // Effacer les erreurs précédentes
        this.addTaskLog(`Fichier sélectionné: ${file.name} (${this.formatFileSize(file.size)})`);
      } else {
        this.selectedFile = null;
        this.fileSelected = false;
      }
    },
      
    uploadCSV() {
      // Utiliser le fichier déjà stocké dans selectedFile
      const file = this.selectedFile;
      
      if (window.logger) {
        window.logger.info("Début de l'upload CSV", { fileName: file?.name, fileSize: file?.size });
      }
      
      if (!file) {
        this.error = "Veuillez sélectionner un fichier CSV.";
        this.addTaskLog("Erreur: Aucun fichier sélectionné");
        if (window.logger) {
          window.logger.warn("Tentative d'upload sans fichier sélectionné");
        }
        return;
      }
      
      // Réinitialiser les états
      this.isUploading = true;
      this.uploadProgress = 0;
      this.processingProgress = 0;
      this.taskId = null;
      this.taskStatus = '';
      this.taskMessage = '';
      this.taskStartTime = new Date();
      this.taskLogs = [];
      this.results = null;
      this.error = null;
      this.retryCount = 0;
      
      this.addTaskLog(`Début de l'upload du fichier: ${file.name} (${this.formatFileSize(file.size)})`);
      
      const formData = new FormData();
      formData.append('file', file);
      
      // Créer une requête XMLHttpRequest pour suivre la progression
      const xhr = new XMLHttpRequest();
      
      // Suivre la progression de l'upload
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          this.uploadProgress = Math.round((event.loaded / event.total) * 100);
          this.addTaskLog(`Progression de l'upload: ${this.uploadProgress}%`);
        }
      });
      
      xhr.addEventListener('load', (e) => {
        if (xhr.status === 200) {
          // Masquer le message JSON brut et extraire uniquement l'ID de tâche
          const response = JSON.parse(xhr.responseText);
          this.taskId = response.task_id;
          this.taskStartTime = new Date();
          this.addTaskLog(`Fichier envoyé avec succès`);
          
          // Commencer à vérifier l'état de la tâche
          setTimeout(() => this.checkTaskStatus(), 1000);
        } else {
          this.isUploading = false;
          
          // Essayer de parser la réponse JSON pour obtenir un message d'erreur
          let errorMessage = "Une erreur est survenue lors de l'envoi du fichier.";
          try {
            const response = JSON.parse(xhr.responseText);
            if (response.message) {
              errorMessage = response.message;
            }
          } catch (e) {
            // Si on ne peut pas parser la réponse, utiliser le statut HTTP
            errorMessage = `Erreur HTTP: ${xhr.status}`;
          }
          
          // Gérer spécifiquement les erreurs 404
          if (xhr.status === 404) {
            errorMessage = "Erreur 404: Le point d'API n'a pas été trouvé. Veuillez vérifier que le serveur est correctement démarré.";
            // Utiliser le message par défaut si impossible de parser la réponse
          }
          
          this.error = errorMessage;
          this.addTaskLog(`Erreur HTTP: ${xhr.status} - ${errorMessage}`);
          
          // L'erreur sera affichée automatiquement via la variable error dans le template Vue
        }
      });
      
      xhr.addEventListener('error', (e) => {
        this.isUploading = false;
        this.error = "Erreur de connexion au serveur.";
        this.addTaskLog(`Erreur de connexion au serveur`);
        
        // L'erreur sera affichée automatiquement via la variable error dans le template Vue
      });
      
      xhr.open('POST', '/api/upload');
      xhr.send(formData);
    },
    
    // Ajouter un log à la tâche
    addTaskLog(message) {
      const timestamp = new Date().toLocaleTimeString();
      const logMessage = `[${timestamp}] ${message}`;
      this.taskLogs.push(logMessage);
    },
    
    // Fonction pour vérifier l'état de la tâche
    checkTaskStatus() {
      if (!this.taskId) return;
      
      if (window.logger) {
        window.logger.debug(`Vérification du statut de la tâche ${this.taskId}`);
      }
      
      fetch(`/api/task/${this.taskId}/status`)
        .then(response => {
          if (!response.ok) {
            const errorMsg = `Erreur HTTP: ${response.status}`;
            if (window.logger) {
              window.logger.error(errorMsg, { taskId: this.taskId, status: response.status });
            }
            throw new Error(errorMsg);
          }
          return response.json();
        })
        .then(data => {
          this.taskStatus = data.status;
          this.taskMessage = data.message || '';
          this.processingProgress = Math.round(data.progress * 100);
          
          // Ajouter un log si le message a changé
          if (data.message && data.message !== this.lastMessage) {
            this.lastMessage = data.message;
            this.addTaskLog(data.message);
          }
          
          // Ajouter un log pour la progression
          if (this.lastProgress !== this.processingProgress) {
            this.lastProgress = this.processingProgress;
            this.addTaskLog(`Progression: ${this.processingProgress}%`);
          }
          
          if (data.status === 'completed') {
            this.isUploading = false;
            this.results = data.results;
            this.addTaskLog(`Tâche terminée avec succès. ${data.results?.total_urls || 0} URLs traitées.`);
            
            // Rediriger vers la page des résultats
            window.location.href = `/results/${this.taskId}`;
          } else if (data.status === 'failed') {
            this.isUploading = false;
            this.error = data.message || "Une erreur est survenue lors du traitement.";
            this.addTaskLog(`Échec: ${data.message}`);
            if (data.error_details) {
              this.addTaskLog(`Détails de l'erreur: ${data.error_details}`);
            }
          } else {
            // Continuer à vérifier l'état toutes les secondes
            setTimeout(() => this.checkTaskStatus(), 1000);
          }
        })
        .catch(error => {
          // Si l'erreur est temporaire, réessayer après un délai
          if (this.retryCount < 3) {
            this.retryCount = (this.retryCount || 0) + 1;
            const retryMsg = `Erreur de connexion, nouvelle tentative ${this.retryCount}/3...`;
            this.addTaskLog(retryMsg);
            
            if (window.logger) {
              window.logger.warn(retryMsg, { 
                taskId: this.taskId, 
                error: error.message,
                retryCount: this.retryCount 
              });
            }
            
            setTimeout(() => this.checkTaskStatus(), 2000);
          } else {
            this.isUploading = false;
            this.error = "Erreur lors de la vérification de l'état de la tâche.";
            const failMsg = `Échec après 3 tentatives: ${error.message}`;
            this.addTaskLog(failMsg);
            
            if (window.logger) {
              window.logger.error(failMsg, { 
                taskId: this.taskId, 
                error: error.message,
                stack: error.stack
              });
            }
          }
        });
    },
    
    // Formater la taille du fichier
    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' bytes';
      else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
      else return (bytes / 1048576).toFixed(1) + ' MB';
    },
    
    // Réinitialiser le formulaire
    resetForm() {
      this.isUploading = false;
      this.uploadProgress = 0;
      this.processingProgress = 0;
      this.taskId = null;
      this.taskStatus = '';
      this.taskMessage = '';
      this.taskLogs = [];
      this.results = null;
      this.error = null;
      this.selectedFile = null;
      this.fileSelected = false;
      
      // Réinitialiser le champ de fichier
      const fileInput = document.getElementById('csv-file');
      if (fileInput) fileInput.value = '';
    },
    
    // Télécharger les résultats en CSV
    downloadResults() {
      if (!this.results) return;
      
      // Créer le contenu CSV
      let csvContent = "Ligne,URL Source,URL Cible,URL Finale,Statut,Conclusion\n";
      
      this.results.details.forEach(result => {
        const line = [
          result.line_num,
          `"${result.source_url}"`,
          `"${result.target_url}"`,
          `"${result.final_url}"`,
          result.status_code,
          `"${result.conclusion}"`
        ].join(',');
        
        csvContent += line + "\n";
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
    }
  },
  computed: {
    elapsedTime() {
      if (!this.taskStartTime) return '0 secondes';
      const seconds = Math.floor((new Date() - this.taskStartTime) / 1000);
      
      if (seconds < 60) return `${seconds} secondes`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes} min ${remainingSeconds} sec`;
    }
  }
});

// Monter l'application
document.addEventListener('DOMContentLoaded', function() {
  app.mount('#app');
});
