/**
 * Gestion de l'authentification côté client pour RedirectionTracer
 * Version améliorée pour éviter les boucles de redirection
 */

// Fonction pour vérifier si l'utilisateur est connecté
function isAuthenticated() {
    return localStorage.getItem('access_token') !== null;
}

// Fonction pour récupérer le token d'authentification
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Fonction pour ajouter le token aux en-têtes de requête
function getAuthHeaders() {
    const token = getAuthToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Fonction pour se déconnecter
function logout() {
    console.log('Déconnexion de l\'utilisateur');
    
    try {
        // Supprimer le token du localStorage et sessionStorage
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token');
        
        // Supprimer tous les cookies possibles liés à l'authentification
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'jwt=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        
        // Envoyer une requête au serveur pour invalider la session côté serveur
        const logoutXhr = new XMLHttpRequest();
        logoutXhr.open('GET', '/api/auth/logout', false); // Requête synchrone
        try {
            logoutXhr.send();
        } catch (e) {
            console.error('Erreur lors de la déconnexion:', e);
        }
    } catch (e) {
        console.error('Erreur lors de la suppression des tokens:', e);
    }
    
    // Forcer une redirection immédiate avec paramètres pour éviter le cache
    window.location.replace('/login?logout=true&t=' + new Date().getTime());
}

// Fonction pour configurer l'intercepteur fetch
function setupFetchInterceptor() {
    // Vérifier si l'intercepteur est déjà configuré
    if (window._fetchInterceptorConfigured) {
        console.log('Intercepteur fetch déjà configuré, ignoré');
        return;
    }
    
    // Sauvegarder la fonction fetch originale
    const _originalFetch = window.fetch;
    
    window.fetch = function(url, options = {}) {
        // Ne pas intercepter les requêtes vers /api/auth/token (login)
        if (url.includes('/api/auth/token')) {
            return _originalFetch(url, options);
        }
        
        // Ajouter les en-têtes d'authentification si nécessaire
        if (isAuthenticated()) {
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${getAuthToken()}`
            };
        }
        
        return _originalFetch(url, options)
            .then(response => {
                // Si on reçoit une erreur 401, déconnecter l'utilisateur
                if (response.status === 401) {
                    console.log('Réponse 401 détectée, déconnexion automatique');
                    logout();
                }
                return response;
            });
    };
    
    // Marquer l'intercepteur comme configuré
    window._fetchInterceptorConfigured = true;
    console.log('Intercepteur fetch configuré avec succès');
}

// Fonction pour rediriger vers la page de connexion si non authentifié
function redirectIfNotAuthenticated() {
    if (!isAuthenticated()) {
        console.log('Utilisateur non authentifié, redirection vers la page de connexion');
        const currentPath = window.location.pathname;
        // Éviter une boucle de redirection si déjà sur la page de connexion
        if (currentPath !== '/login') {
            window.location.href = '/login?redirect=' + encodeURIComponent(currentPath);
        }
    } else {
        console.log('Utilisateur authentifié, pas de redirection nécessaire');
    }
}

// Fonction pour récupérer les informations de l'utilisateur connecté
async function getCurrentUser() {
    if (!isAuthenticated()) {
        return null;
    }
    
    try {
        const response = await fetch('/api/auth/me', {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            // Token invalide ou expiré
            logout();
            return null;
        }
    } catch (error) {
        console.error('Erreur lors de la récupération des informations utilisateur:', error);
        return null;
    }
}

// Fonction pour mettre à jour l'interface utilisateur en fonction de l'état d'authentification
async function updateAuthUI() {
    const authSection = document.getElementById('auth-section');
    if (!authSection) return;
    
    const user = await getCurrentUser();
    
    if (user) {
        // Utilisateur connecté
        authSection.innerHTML = `
            <div class="flex items-center mb-6 px-3">
                <div class="flex-shrink-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full p-1">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-gray-800">${user.username || user.email.split('@')[0]}</p>
                    <p class="text-xs text-gray-500">${user.email}</p>
                </div>
            </div>
            <button id="sidebar-logout-btn" style="background-color: #ef4444; color: white; border-radius: 12px; padding: 8px 16px; font-weight: 500; width: 75%; text-align: center; margin: 0 auto; display: block; transition: background-color 0.2s ease; border: none;" class="px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors font-medium w-3/4 text-center block mx-auto">Déconnexion</button>
        `;
        
        // Ajouter l'événement de déconnexion
        const logoutBtn = document.getElementById('sidebar-logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', logout);
            
            // Ajouter les événements pour le style hover
            logoutBtn.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#dc2626';
            });
            
            logoutBtn.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '#ef4444';
            });
        }
    } else {
        // Utilisateur non connecté
        authSection.innerHTML = `
            <div class="flex flex-col items-center space-y-3">
                <a href="/login" class="px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors font-medium w-3/4 text-center">
                    Connexion
                </a>
                <a href="/register" class="px-4 py-2 bg-green-500 text-white rounded-xl hover:bg-green-600 transition-colors font-medium w-3/4 text-center">
                    Inscription
                </a>
            </div>
        `;
    }
}

// Exécuter updateAuthUI dès que possible
function initAuth() {
    // Mettre à jour l'interface utilisateur immédiatement
    updateAuthUI();
    
    // Réappliquer les styles après un court délai pour s'assurer qu'ils sont appliqués
    setTimeout(function() {
        const logoutBtn = document.getElementById('sidebar-logout-btn');
        if (logoutBtn) {
            logoutBtn.style.backgroundColor = '#ef4444';
            logoutBtn.style.color = 'white';
            logoutBtn.style.borderRadius = '12px';
            logoutBtn.style.padding = '8px 16px';
            logoutBtn.style.fontWeight = '500';
            logoutBtn.style.width = '75%';
            logoutBtn.style.textAlign = 'center';
            logoutBtn.style.margin = '0 auto';
            logoutBtn.style.display = 'block';
            logoutBtn.style.border = 'none';
        }
    }, 100);
}

// Fonction d'initialisation principale
function initAuth() {
    console.log('Initialisation de l\'authentification');
    
    // Configurer l'intercepteur fetch
    setupFetchInterceptor();
    
    // Vérifier si nous sommes sur une page protégée
    const protectedPages = ['/results/'];
    const currentPath = window.location.pathname;
    
    if (protectedPages.some(page => currentPath.startsWith(page))) {
        redirectIfNotAuthenticated();
    }
}

// Exécuter l'initialisation au chargement de la page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuth);
} else {
    initAuth();
}

// L'intercepteur fetch est déjà configuré dans la fonction setupFetchInterceptor()
