# RedirectionTracer - Analyseur de Redirections URL

RedirectionTracer est une application web moderne basée sur FastAPI qui permet d'analyser des fichiers CSV contenant des redirections d'URL. Elle détecte les boucles de redirection, vérifie la validité des redirections et fournit une analyse détaillée avec une interface utilisateur intuitive et élégante.

## Fonctionnalités

### Analyse de Redirections
* **Upload de fichier CSV :** Permet d'uploader un fichier CSV contenant les redirections à analyser
* **Préfixe de domaine optionnel :** Possibilité d'ajouter un préfixe de domaine aux URLs relatives
* **Détection de boucles :** Identifie les séquences d'URL qui redirigent en boucle (A → B → C → A)
* **Analyse détaillée :** Suit la chaîne de redirection depuis la `source_url` et compare avec la `target_url` spécifiée

### Interface Utilisateur Moderne
* **Design minimaliste et élégant :** Interface utilisateur intuitive avec un design moderne
* **Tableaux de bord statistiques :** Visualisation des résultats avec des cartes statistiques colorées
* **Graphiques interactifs :** Représentation graphique de la répartition des résultats
* **Tableau de résultats détaillé :** Affichage complet des informations pour chaque redirection

### Filtrage et Recherche
* **Filtres par statut :** Filtrer les résultats par statut (Corrects, Incorrects, Erreurs, Redirections multiples)
* **Filtres par code HTTP :** Filtrer par code de statut HTTP (200, 301, 302, 404, etc.)
* **Barre de recherche :** Rechercher par URL ou mot-clé dans les résultats

### Fonctionnalités Avancées
* **Popup de détails :** Affichage détaillé des informations de redirection en cliquant sur une ligne
* **Export CSV :** Export des résultats filtrés au format CSV
* **Traitement asynchrone :** Analyse en arrière-plan avec barre de progression
* **Logging :** Enregistrement des informations d'exécution dans la console et dans un fichier `app.log`

## Format du fichier CSV d'entrée

Le fichier CSV doit contenir au moins deux colonnes avec les en-têtes suivants :

* `source_url` : L'URL de départ de la redirection
* `target_url` : L'URL vers laquelle la `source_url` est censée rediriger

Exemple :

```csv
source_url,target_url
https://site.com/a,https://site.com/b
https://site.com/b,/c
/c,https://site.com/a
https://site.com/x,https://site.com/y
/page1,/page2
```

**Note :** Les URLs relatives (commençant par `/`) seront automatiquement complétées avec le préfixe de domaine spécifié lors de l'upload.

## Installation

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/votre-username/RedirectionTracer.git
   cd RedirectionTracer
   ```

2. **Créer un environnement virtuel (recommandé) :**
   ```bash
   python -m venv venv
   ```
   * Sur Windows : `venv\Scripts\activate`
   * Sur macOS/Linux : `source venv/bin/activate`

3. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

4. **Vérifier les dépendances :**
   L'application nécessite les packages suivants :
   * fastapi
   * uvicorn
   * jinja2
   * python-multipart
   * aiofiles
   * requests

## Utilisation

1. **Lancer l'application FastAPI :**
   ```bash
   uvicorn main:app --reload
   ```
   L'application sera accessible par défaut à l'adresse `http://127.0.0.1:8000`

2. **Analyser un fichier CSV :**
   * Ouvrez votre navigateur à l'adresse indiquée
   * Uploadez votre fichier CSV via le formulaire
   * (Optionnel) Entrez un préfixe de domaine pour les URLs relatives
   * Cliquez sur "Analyser les redirections"

3. **Consulter les résultats :**
   * **Tableau de bord statistique :** Visualisation des résultats avec pourcentages
   * **Graphique de répartition :** Représentation visuelle des différents types de redirections
   * **Tableau détaillé :** Liste complète des redirections analysées

4. **Filtrer et rechercher :**
   * Utilisez les filtres par statut pour afficher uniquement certains types de redirections
   * Utilisez les filtres par code HTTP pour filtrer par code de statut
   * Utilisez la barre de recherche pour trouver des URLs spécifiques

5. **Exporter les résultats :**
   * Cliquez sur "Exporter résultats" pour télécharger les données filtrées au format CSV

6. **Démarrer une nouvelle analyse :**
   * Cliquez sur "Nouvelle analyse" pour revenir à la page d'accueil

## Structure du Projet

```
RedirectionTracer/
├── app/                    # Package principal de l'application
│   ├── __init__.py         # Initialisation du package
│   ├── api.py              # Endpoints API
│   ├── csv_processor.py    # Traitement des fichiers CSV
│   ├── http_utils.py       # Utilitaires HTTP
│   ├── logger.py           # Configuration des logs
│   ├── models.py           # Modèles de données
│   ├── routes.py           # Routes web
│   ├── task_manager.py     # Gestionnaire de tâches asynchrones
│   ├── url_parser.py       # Analyse des URLs
│   └── url_processor.py    # Traitement des redirections
├── static/                 # Fichiers statiques
│   ├── css/                # Feuilles de style
│   ├── js/                 # Scripts JavaScript
│   └── images/             # Images
├── templates/              # Templates Jinja2
│   └── partials/           # Fragments de templates
├── main.py                 # Point d'entrée de l'application
├── requirements.txt        # Dépendances Python
└── README.md               # Documentation
```

## Fonctionnalités Techniques

* **Architecture asynchrone :** Utilisation de FastAPI et de tâches asynchrones pour un traitement efficace
* **Templating avec Jinja2 :** Génération dynamique des pages HTML
* **HTMX pour l'interactivité :** Mise à jour partielle de la page sans rechargement complet
* **Chart.js pour les graphiques :** Visualisation des données avec des graphiques interactifs
* **Feather Icons :** Utilisation d'icônes vectorielles modernes

## Pistes d'Amélioration Futures

* **Authentification :** Ajout d'un système de connexion pour sauvegarder les analyses
* **Historique des analyses :** Stockage et consultation des analyses précédentes
* **API complète :** Développement d'une API RESTful pour l'intégration avec d'autres services
* **Tests automatisés :** Ajout de tests unitaires et d'intégration
* **Optimisation pour les fichiers volumineux :** Traitement par lots pour les grands fichiers CSV
* **Analyse en temps réel :** Suivi des redirections en direct via des requêtes HTTP
* **Dockerisation :** Création d'un Dockerfile pour faciliter le déploiement

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
