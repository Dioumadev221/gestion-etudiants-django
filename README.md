# Gestion des étudiants – API Django

API REST de gestion des étudiants avec Django REST Framework, PostgreSQL (Docker) et authentification JWT par rôles (étudiant, admin, responsable formation).

TP Django DBE – P6, année 2025-2026.

## Technologies

- Python 3.13, Django 6.1
- Django REST Framework + SimpleJWT
- PostgreSQL 17 dans Docker
- Pillow (photos de profil et documents)

## Structure du projet

```
TP/
├── backend/
│   ├── manage.py
│   ├── gestion_etudiants/   # configuration (settings, urls)
│   └── etudiants/           # l'application (modèles, vues, API)
├── docker-compose.yml       # base de données PostgreSQL
├── requirements.txt
└── .env.example             # modèle du fichier .env
```

## Installation

Prérequis : Python 3.13, Git et Docker Desktop (ouvert).

### 1. Cloner le projet

```bash
git clone https://github.com/Dioumadev221/gestion-etudiants-django.git
cd gestion-etudiants-django
```

### 2. Créer le fichier `.env`

Copier `.env.example` en `.env` :

```bash
copy .env.example .env
```

Ouvrir `.env` et remplacer les deux `change-moi` par vos propres valeurs (n'importe quel texte). Pour générer une clé secrète :

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

> Chacun a son propre `.env` : il ne faut jamais le partager ni le mettre sur GitHub.
> Si le port `5433` est déjà utilisé sur votre PC, changez `DB_PORT`.

### 3. Installer l'environnement Python

```bash
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```

### 4. Lancer la base de données

```bash
docker compose up -d
```

### 5. Lancer Django

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

L'API est disponible sur http://127.0.0.1:8000/api/ et le dashboard admin sur http://127.0.0.1:8000/admin/.

### Lancer les tests

```bash
cd backend
python manage.py test etudiants
```

## Rôles

| Rôle | Description |
|---|---|
| `etudiant` | Rôle par défaut à l'inscription |
| `responsable` | Responsable formation |
| `admin` | Administrateur (un superuser est automatiquement admin) |

Seul un admin peut créer un compte `admin` ou `responsable`, depuis l'API ou depuis le dashboard `/admin/` (Utilisateurs > Ajouter : le profil se remplit sur la même page).

## Endpoints

Adresse de base : `http://127.0.0.1:8000`

| Méthode | Endpoint | Accès | Description |
|---|---|---|---|
| GET | `/api/` | Public | Accueil : message de bienvenue et filières |
| GET | `/api/filieres/` | Public | Liste des filières |
| POST | `/api/inscription/` | Public / admin | Crée un utilisateur et son profil |
| POST | `/api/connexion/` | Public | Connexion : tokens JWT et rôle |
| POST | `/api/token/refresh/` | Public | Nouveau token `access` |
| POST | `/api/deconnexion/` | Connecté | Déconnexion (refresh token invalidé) |
| GET | `/api/moi/` | Connecté | Utilisateur connecté |
| GET | `/api/etudiants/` | Admin, responsable | Étudiants (prénom, nom, filière) |
| GET | `/api/etudiants/?filiere=<id>` | Admin, responsable | Étudiants d'une filière |
| GET | `/api/documents/` | Connecté | Documents (l'étudiant ne voit que les siens) |
| POST | `/api/documents/` | Admin | Ajouter un document à un étudiant |
| GET / PUT / PATCH / DELETE | `/api/documents/<id>/` | Admin (lecture pour l'étudiant concerné) | Gérer un document |

### Inscription

`POST /api/inscription/` en **form-data** (à cause de la photo) :

| Champ | Obligatoire | Remarque |
|---|---|---|
| `username` | oui | |
| `first_name` | oui | prénom |
| `last_name` | oui | nom |
| `email` | oui | |
| `password` | oui | 8 caractères minimum, pas trop simple |
| `filiere` | oui | id de la filière (voir `/api/filieres/`) |
| `photo` | oui | fichier image |
| `telephone` | non | |
| `role` | non | `etudiant` par défaut ; autre valeur réservée à l'admin |

### Connexion

```http
POST /api/connexion/
Content-Type: application/json

{"username": "awa", "password": "MotDePasse123"}
```

Réponse :

```json
{
  "refresh": "...",
  "access": "...",
  "user": {
    "id": 1,
    "username": "awa",
    "first_name": "Awa",
    "last_name": "Diop",
    "email": "awa@example.com",
    "role": "etudiant",
    "filiere": "Génie Logiciel",
    "photo": "http://127.0.0.1:8000/media/photos/awa.png"
  }
}
```

Pour les endpoints qui demandent d'être connecté, ajouter l'en-tête :

```
Authorization: Bearer <access>
```

Le token `access` expire après 1 heure. Pour en obtenir un nouveau :

```http
POST /api/token/refresh/
Content-Type: application/json

{"refresh": "<refresh>"}
```

### Déconnexion

```http
POST /api/deconnexion/
Authorization: Bearer <access>
Content-Type: application/json

{"refresh": "<refresh>"}
```

### Ajout d'un document (admin)

`POST /api/documents/` en **form-data** : `etudiant` (id du profil), `titre`, `fichier` (fichier), `description` (facultatif).

### Codes de réponse

| Code | Signification |
|---|---|
| `200` / `201` | Succès / création réussie |
| `205` | Déconnexion réussie |
| `400` | Données invalides (le détail est dans la réponse) |
| `401` | Non connecté ou token expiré |
| `403` | Connecté, mais rôle non autorisé |

## Avancement du TP

- [x] 1. Endpoint d'accueil
- [x] 2. Inscription d'un utilisateur avec profil (filière et photo), création par l'admin depuis son dashboard
- [x] 3. Connexion / déconnexion
- [x] 4. Liste des étudiants (prénom, nom, filière) pour admin et responsable
- [ ] 5. Modifier un profil
- [ ] 6. Supprimer un compte utilisateur (et son profil)
- [ ] 7. Ajouter / supprimer une filière
- [ ] 8. Documents pédagogiques pour tous les étudiants d'une filière
- [ ] 9. Documents académiques pour un étudiant
- [ ] 10. Changement et réinitialisation du mot de passe (optionnel)
- [ ] 11. Gestion des permissions d'accès (decorators)
- [ ] Intégration du frontend React
