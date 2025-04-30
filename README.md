# Détecteur de Boucles de Redirection

Ce projet fournit une application web simple basée sur FastAPI pour analyser un fichier CSV contenant des redirections d'URL. Il détecte les boucles de redirection globales et fournit une analyse détaillée de chaque redirection spécifiée dans le fichier.

## Fonctionnalités

*   **Upload de fichier CSV :** Permet d'uploader un fichier CSV contenant les redirections à analyser.
*   **Préfixe de domaine optionnel :** Possibilité d'ajouter un préfixe de domaine (ex: `https://www.example.com`) aux URLs relatives trouvées dans le CSV.
*   **Détection de boucles globales :** Identifie les séquences d'URL qui redirigent en boucle (A -> B -> C -> A).
*   **Analyse détaillée :** Pour chaque ligne du CSV, suit la chaîne de redirection depuis la `source_url` et compare l'URL finale atteinte avec la `target_url` spécifiée.
*   **Interface Web :** Une interface simple pour uploader le fichier et visualiser les résultats.
*   **Export CSV :** Permet de télécharger les résultats de l'analyse détaillée au format CSV.
*   **Logging :** Enregistre les informations d'exécution dans la console et dans un fichier `app.log`.

## Format du fichier CSV d'entrée

Le fichier CSV doit contenir au moins deux colonnes avec les en-têtes suivants :

*   `source_url` : L'URL de départ de la redirection.
*   `target_url` : L'URL vers laquelle la `source_url` est censée rediriger.

Exemple :

```csv
source_url,target_url
https://site.com/a,https://site.com/b
https://site.com/b,/c # URL relative
/c,https://site.com/a # URL relative
https://site.com/x,https://site.com/y
/page1,/page2
```

## Installation

1.  **Cloner le dépôt (si vous l'avez mis sur GitHub) :**
    ```bash
    git clone https://github.com/VOTRE_USERNAME/RedirectionTracer.git
    cd RedirectionTracer
    ```
2.  **Créer un environnement virtuel (recommandé) :**
    ```bash
    python -m venv venv
    ```
    *   Sur Windows : `.\venv\Scripts\activate`
    *   Sur macOS/Linux : `source venv/bin/activate`
3.  **Installer les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

## Utilisation

1.  **Lancer l'application FastAPI :**
    ```bash
    uvicorn main:app --reload
    ```
    L'application sera accessible par défaut à l'adresse `http://127.0.0.1:8000`.

2.  **Ouvrir votre navigateur** à cette adresse.

3.  **Uploader votre fichier CSV** via le formulaire.

4.  **(Optionnel)** Entrez un **préfixe de domaine** si votre fichier CSV contient des URLs relatives (commençant par `/`). Ce préfixe sera ajouté devant ces URLs relatives (ex: `/page1` deviendra `https://votredomaine.com/page1`).

5.  **Cliquez sur "Analyser les boucles"**.

6.  **Consultez les résultats** affichés sur la page :
    *   Un tableau détaillé analysant chaque ligne du CSV.
    *   Une liste des boucles globales détectées.

7.  **(Optionnel)** Cliquez sur **"Télécharger les détails en CSV"** pour exporter le tableau d'analyse.

8.  Les **logs d'exécution** sont visibles dans la console où `uvicorn` a été lancé et sont également enregistrés dans le fichier `app.log` à la racine du projet.

## Pistes d'Amélioration Futures

*   Gestion plus fine des erreurs (format CSV, encodage, erreurs réseau si suivi externe).
*   Optimisation pour les fichiers CSV très volumineux.
*   Implémentation du suivi réel des redirections externes (via requêtes HTTP).
*   Amélioration de l'interface utilisateur (barre de progression, tris/filtres, framework CSS).
*   Ajout de tests automatisés.
*   Configuration externe de certains paramètres (ex: profondeur max de suivi).
*   Création d'un Dockerfile pour faciliter le déploiement.
