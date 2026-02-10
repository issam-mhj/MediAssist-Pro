# Authentification - MediAssist-Pro

Ce document explique le système d'authentification OAuth2 avec JWT et comment protéger les routes.

## Vue d'ensemble

MediAssist-Pro utilise le standard OAuth2 Password Flow avec tokens JWT pour l'authentification.

## Flux d'authentification

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ 1. POST /api/auth/register
       │    {username, email, password}
       │
┌──────▼──────────────────────────────────────┐
│  Backend                                     │
│  ┌─────────────────────────────────────┐   │
│  │ Hash password (bcrypt)               │   │
│  │ Save user to database                │   │
│  └─────────────────┬───────────────────┘   │
└────────────────────┼────────────────────────┘
                     │
       ┌─────────────▼─────────────┐
       │ Return UserResponse        │
       │ {id, username, email, role}│
       └────────────────────────────┘
                     │
       │ 2. POST /api/auth/login
       │    {username, password}
       │
┌──────▼──────────────────────────────────────┐
│  Backend                                     │
│  ┌─────────────────────────────────────┐   │
│  │ Verify password                      │   │
│  │ Generate JWT token                   │   │
│  └─────────────────┬───────────────────┘   │
└────────────────────┼────────────────────────┘
                     │
       ┌─────────────▼─────────────┐
       │ Return Token               │
       │ {access_token, token_type} │
       └────────────────────────────┘
                     │
       │ 3. Authenticated requests
       │    Header: Authorization: Bearer <token>
       │
┌──────▼──────────────────────────────────────┐
│  Backend                                     │
│  ┌─────────────────────────────────────┐   │
│  │ Decode & validate token              │   │
│  │ Get user from database               │   │
│  │ Execute protected route              │   │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Endpoints d'authentification

### POST /api/auth/register

**Description** : Inscription d'un nouvel utilisateur

**Body** :
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Réponse 201** :
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user"
}
```

**Erreurs** :
- `400` : Username ou email déjà utilisé
- `422` : Validation échouée (email invalide, champ manquant)

**Exemple cURL** :
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

**Exemple Python** :
```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/register",
    json={
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePassword123!"
    }
)
user = response.json()
print(f"User created: {user['username']}")
```

---

### POST /api/auth/login

**Description** : Connexion et obtention d'un token JWT

**Body (form-data)** :
```
username=john_doe
password=SecurePassword123!
```

**Réponse 200** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Erreurs** :
- `401` : Username ou mot de passe incorrect

**Exemple cURL** :
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=SecurePassword123!"
```

**Exemple Python** :
```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/login",
    data={
        "username": "john_doe",
        "password": "SecurePassword123!"
    }
)
token = response.json()["access_token"]
print(f"Token: {token}")
```

---

## Routes protégées

### GET /api/users/me

**Description** : Récupère le profil de l'utilisateur connecté

**Headers** :
```
Authorization: Bearer <access_token>
```

**Réponse 200** :
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user"
}
```

**Erreurs** :
- `401` : Token invalide, expiré ou manquant

**Exemple cURL** :
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

**Exemple Python** :
```python
import requests

headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/users/me",
    headers=headers
)
profile = response.json()
print(f"Logged in as: {profile['username']}")
```

---

## Dépendances d'authentification

### get_current_user

**Fichier** : `app/api/deps.py`

**Rôle** : Récupère l'utilisateur connecté depuis le token JWT

**Usage dans une route** :
```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}"}
```

**Comment ça fonctionne** :
1. Extrait le token du header `Authorization: Bearer <token>`
2. Décode le token JWT avec `decode_token()`
3. Récupère le username depuis le payload (`sub`)
4. Interroge la base de données pour obtenir l'utilisateur
5. Retourne l'objet `User`
6. Lève `CredentialsException` si une étape échoue

---

### get_current_admin_user

**Fichier** : `app/api/deps.py`

**Rôle** : Vérifie que l'utilisateur connecté est un admin

**Usage dans une route** :
```python
from app.api.deps import get_current_admin_user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user)
):
    # Seuls les admins peuvent exécuter cette route
    return {"message": "User deleted"}
```

**Erreur** :
- `403 Forbidden` : Si l'utilisateur n'est pas admin

---

## OAuth2PasswordBearer

**Configuration** :
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
```

**Rôle** :
- Définit où obtenir le token (endpoint `/api/auth/login`)
- Ajoute automatiquement le bouton "Authorize" dans Swagger UI
- Extrait le token du header `Authorization: Bearer <token>`

**Utilisation** :
```python
def get_current_user(token: str = Depends(oauth2_scheme)):
    # token contient le JWT extrait automatiquement
    ...
```

---

## Swagger UI (Documentation interactive)

### Tester l'authentification dans Swagger

1. Ouvrir `http://localhost:8000/docs`
2. Cliquer sur "Authorize" (🔓)
3. Entrer username et password
4. Cliquer sur "Authorize"
5. Les requêtes authentifiées incluent automatiquement le token

**Endpoints disponibles** :
- `POST /api/auth/register` : Inscription
- `POST /api/auth/login` : Connexion (🔒 Génère le token)
- `GET /api/users/me` : Profil (🔒 Protégé)

---

## Sécurité

### Headers requis

**Pour les routes authentifiées** :
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Format** :
- Type : `Bearer`
- Token : JWT généré par `/api/auth/login`

### Validation du token

FastAPI + JWT vérifient automatiquement :
- ✅ Signature valide (SECRET_KEY)
- ✅ Token non expiré (`exp` claim)
- ✅ Format correct

### Gestion des erreurs

**Token manquant** :
```json
{
  "detail": "Not authenticated"
}
```

**Token invalide/expiré** :
```json
{
  "detail": "Could not validate credentials"
}
```

**Permissions insuffisantes** :
```json
{
  "detail": "Not enough permissions"
}
```

---

## Exemple complet d'utilisation

### Script Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# 1. Inscription
print("1. Inscription...")
register_response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "username": "marie_tech",
        "email": "marie@hospital.com",
        "password": "SecurePass123!"
    }
)
print(f"   User created: {register_response.json()}")

# 2. Connexion
print("\n2. Connexion...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "marie_tech",
        "password": "SecurePass123!"
    }
)
token = login_response.json()["access_token"]
print(f"   Token received: {token[:50]}...")

# 3. Accès au profil
print("\n3. Récupération du profil...")
headers = {"Authorization": f"Bearer {token}"}
profile_response = requests.get(
    f"{BASE_URL}/users/me",
    headers=headers
)
profile = profile_response.json()
print(f"   Profile: {profile}")

# 4. Requête sans token (échouera)
print("\n4. Tentative sans token...")
try:
    requests.get(f"{BASE_URL}/users/me").raise_for_status()
except requests.HTTPError as e:
    print(f"   Erreur (normal): {e}")
```

---

## Tests

### Test d'inscription

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register():
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "hashed_password" not in data  # Ne doit pas être exposé
```

### Test de connexion

```python
def test_login():
    # Inscription d'abord
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })
    
    # Connexion
    response = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

### Test de route protégée

```python
def test_protected_route():
    # Connexion
    login_response = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    # Accès avec token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    
    # Accès sans token
    response = client.get("/api/users/me")
    assert response.status_code == 401
```

---

## Bonnes pratiques

### 1. Toujours utiliser HTTPS en production

```python
# ❌ Mauvais (production)
http://api.example.com/auth/login

# ✅ Bon (production)
https://api.example.com/auth/login
```

### 2. Stocker le token de manière sécurisée

```javascript
// ✅ Bon (Frontend)
localStorage.setItem('token', token);  // OK pour des apps simples

// 🔒 Meilleur (httpOnly cookies)
// Le serveur définit le cookie, inaccessible en JavaScript
```

### 3. Gérer l'expiration du token

```python
# Le token expire après ACCESS_TOKEN_EXPIRE_MINUTES
# Implémenter un système de refresh token pour les sessions longues
```

### 4. Ne jamais logger les tokens

```python
# ❌ DANGEREUX
logger.info(f"Token: {token}")

# ✅ Bon
logger.info(f"User {username} logged in")
```

---

## Ressources

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth2 Password Flow](https://oauth.net/2/grant-types/password/)
- [JWT.io](https://jwt.io/) - Décoder des tokens JWT
