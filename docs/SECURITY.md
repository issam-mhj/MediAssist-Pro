# Sécurité - MediAssist-Pro

Ce document explique le système de sécurité, l'authentification JWT et le hachage de mots de passe.

## Vue d'ensemble

MediAssist-Pro utilise un système d'authentification moderne basé sur :
- **JWT (JSON Web Tokens)** : Tokens stateless pour l'authentification
- **Bcrypt** : Algorithme de hachage sécurisé pour les mots de passe
- **OAuth2 Password Bearer** : Standard OAuth2 pour les APIs

## Architecture de sécurité

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (Frontend)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    1. POST /auth/register
                    (username, email, password)
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Backend API                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  2. Hash password avec bcrypt                       │    │
│  │     password → hash (non réversible)                │    │
│  └────────────────────────┬───────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────┐    │
│  │  3. Sauvegarder dans PostgreSQL                     │    │
│  │     (username, email, hashed_password)              │    │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                    4. Retour UserResponse (sans password)
                            │
                    5. POST /auth/login
                    (username, password)
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Backend API                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  6. Vérifier password                               │    │
│  │     bcrypt.verify(password, hashed_password)        │    │
│  └────────────────────────┬───────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────┐    │
│  │  7. Générer JWT Token                               │    │
│  │     {"sub": username, "exp": timestamp}             │    │
│  │     Signé avec SECRET_KEY                           │    │
│  └────────────────────────┬───────────────────────────┘    │
└───────────────────────────┼─────────────────────────────────┘
                            │
                    8. Retour Token
                    {"access_token": "eyJ...", "token_type": "bearer"}
                            │
                    9. Requêtes authentifiées
                    Header: Authorization: Bearer eyJ...
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Backend API                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  10. Décoder et valider JWT                         │    │
│  │      jwt.decode(token, SECRET_KEY)                  │    │
│  └────────────────────────┬───────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────┐    │
│  │  11. Récupérer l'utilisateur                        │    │
│  │      db.query(User).filter(username=...)            │    │
│  └────────────────────────┬───────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────┐    │
│  │  12. Exécuter la requête                            │    │
│  │      (utilisateur authentifié)                      │    │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Module de sécurité (`app/core/security.py`)

### 1. Hachage de mots de passe (Bcrypt)

#### Configuration

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

**Paramètres** :
- `schemes=["bcrypt"]` : Utilise l'algorithme bcrypt
- `deprecated="auto"` : Marque automatiquement les anciens hash comme obsolètes

#### Fonction : `get_password_hash()`

```python
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

**Rôle** : Transforme un mot de passe en clair en hash sécurisé

**Exemple** :
```python
password = "SecurePassword123!"
hashed = get_password_hash(password)
# $2b$12$KIXhFZq8Y2tW5oMFVXqPyOmKGJN1vY3Q5f0RZz8xBwHqT6vLnK3Yy
```

**Caractéristiques bcrypt** :
- **Salt automatique** : Chaque hash est unique même pour le même mot de passe
- **Facteur de travail** : Ralentit intentionnellement le calcul (résistant aux attaques par force brute)
- **Non réversible** : Impossible de retrouver le mot de passe original
- **Adaptatif** : Le facteur de travail peut être augmenté avec le temps

**Sécurité** :
```python
# Même mot de passe → Hash différents à chaque fois
hash1 = get_password_hash("password123")  # $2b$12$abc...
hash2 = get_password_hash("password123")  # $2b$12$xyz...
# hash1 != hash2 (grâce au salt)
```

#### Fonction : `verify_password()`

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Rôle** : Vérifie si un mot de passe correspond à un hash

**Exemple** :
```python
# Lors de l'inscription
password = "SecurePassword123!"
hashed = get_password_hash(password)
# Sauvegarder hashed dans la DB

# Lors de la connexion
input_password = "SecurePassword123!"
is_valid = verify_password(input_password, hashed)  # True

wrong_password = "WrongPassword"
is_valid = verify_password(wrong_password, hashed)  # False
```

**Comment ça marche** :
1. Extrait le salt du hash stocké
2. Hash le mot de passe en clair avec ce salt
3. Compare les deux hash
4. Retourne True si identiques

### 2. JWT (JSON Web Tokens)

#### Configuration

```python
from jose import jwt
from app.config import settings

# SECRET_KEY : Clé secrète pour signer les tokens
# ALGORITHM : HS256 (HMAC avec SHA-256)
```

#### Structure d'un JWT

Un JWT est composé de 3 parties séparées par des points :

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huX2RvZSIsImV4cCI6MTYxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
│                                      │                                           │
│          Header                      │           Payload                         │      Signature
│  (Algorithme + Type)                 │     (Données + Expiration)                │   (Vérification)
```

**Décodé** :
```json
// Header
{
  "alg": "HS256",
  "typ": "JWT"
}

// Payload
{
  "sub": "john_doe",
  "exp": 1616239022
}

// Signature
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  SECRET_KEY
)
```

#### Fonction : `create_access_token()`

```python
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
```

**Rôle** : Génère un token JWT signé

**Paramètres** :
- `data` : Données à inclure dans le token (ex: username)
- `expires_delta` : Durée de validité (optionnel)

**Exemple** :
```python
from datetime import timedelta

# Créer un token pour john_doe valide 30 minutes
token = create_access_token(
    data={"sub": "john_doe"},
    expires_delta=timedelta(minutes=30)
)

print(token)
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Payload du token** :
- `sub` (subject) : Identifiant de l'utilisateur (username)
- `exp` (expiration) : Timestamp d'expiration
- Autres données personnalisées possibles (rôle, permissions, etc.)

#### Fonction : `decode_token()`

```python
def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

**Rôle** : Décode et valide un token JWT

**Exemple** :
```python
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
payload = decode_token(token)

if payload:
    username = payload.get("sub")
    print(f"Token valide pour : {username}")
else:
    print("Token invalide ou expiré")
```

**Vérifications automatiques** :
- ✅ Signature valide (non modifié)
- ✅ Token non expiré
- ✅ Format correct

**Retour** :
- `dict` : Payload du token si valide
- `None` : Si token invalide, expiré, ou signature incorrecte

## Flux d'authentification complet

### 1. Inscription

```python
# Route : POST /auth/register
from app.core.security import get_password_hash

def register(user: UserCreate, db: Session):
    # 1. Vérifier que l'utilisateur n'existe pas
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise UserAlreadyExistsException()
    
    # 2. Hasher le mot de passe
    hashed_password = get_password_hash(user.password)
    
    # 3. Créer l'utilisateur
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password  # Stocke le hash, PAS le password
    )
    
    # 4. Sauvegarder en DB
    db.add(new_user)
    db.commit()
    
    return new_user
```

### 2. Connexion

```python
# Route : POST /auth/login
from app.core.security import verify_password, create_access_token
from datetime import timedelta

def login(username: str, password: str, db: Session):
    # 1. Récupérer l'utilisateur
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 2. Vérifier le mot de passe
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 3. Générer le token JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # 4. Retourner le token
    return {"access_token": access_token, "token_type": "bearer"}
```

### 3. Utilisation du token

**Client** :
```python
import requests

# 1. Se connecter
response = requests.post("/api/auth/login", data={
    "username": "john_doe",
    "password": "password123"
})
token = response.json()["access_token"]

# 2. Utiliser le token pour les requêtes authentifiées
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("/api/users/me", headers=headers)
```

**Backend** :
```python
from fastapi import Depends
from app.api.deps import get_current_user

@app.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    # current_user est automatiquement récupéré via le token
    return current_user
```

## Sécurité des tokens JWT

### Avantages

✅ **Stateless** : Pas besoin de stocker les sessions en base
✅ **Scalable** : Fonctionne sur plusieurs serveurs
✅ **Portable** : Utilisable partout (web, mobile, API)
✅ **Self-contained** : Contient toutes les infos nécessaires

### Points d'attention

⚠️ **Révocation** : Un token est valide jusqu'à son expiration
- Solution : Courte durée de vie (15-30 minutes)
- Alternative : Refresh tokens + blacklist

⚠️ **Vol de token** : Si un token est volé, il peut être utilisé
- Solution : HTTPS obligatoire
- Solution : Stockage sécurisé (httpOnly cookies)
- Solution : Courte expiration

⚠️ **SECRET_KEY** : Si compromise, tous les tokens sont vulnérables
- Solution : Clé très longue et aléatoire
- Solution : Rotation régulière des clés
- Solution : Ne JAMAIS committer dans Git

### Bonnes pratiques

#### 1. Durée de vie courte

```python
# ✅ Bon : 30 minutes maximum
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ❌ Mauvais : Trop long (risque de sécurité)
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 jours
```

#### 2. SECRET_KEY sécurisée

```python
# ✅ Bon : Longue et aléatoire
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7

# ❌ Mauvais : Trop simple
SECRET_KEY=secret123
```

**Générer une clé sécurisée** :
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -hex 32
```

#### 3. HTTPS obligatoire

```python
# Ne JAMAIS envoyer de tokens en HTTP (non chiffré)
# Toujours utiliser HTTPS en production
```

#### 4. Valider tous les tokens

```python
# ✅ Bon : Vérifier la signature et l'expiration
payload = decode_token(token)
if payload is None:
    raise CredentialsException()

# ❌ Mauvais : Faire confiance sans vérifier
payload = jwt.decode(token, verify=False)  # DANGEREUX !
```

## Bcrypt : Détails techniques

### Pourquoi bcrypt ?

**Avantages** :
- **Lent par conception** : Ralentit les attaques par force brute
- **Salt automatique** : Chaque hash est unique
- **Adaptatif** : Le coût peut augmenter avec le temps
- **Éprouvé** : Utilisé depuis 1999

**Comparaison avec d'autres algorithmes** :
- ❌ MD5 : Obsolète, trop rapide, cassé
- ❌ SHA-256 : Trop rapide pour les mots de passe
- ✅ Bcrypt : Recommandé
- ✅ Argon2 : Alternative moderne
- ✅ Scrypt : Alternative moderne

### Facteur de travail

Le "rounds" ou "cost factor" détermine la difficulté :

```python
# Par défaut : 12 rounds (recommandé)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ajuster si nécessaire
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=13)
```

**Impact** :
- 10 rounds : ~100ms
- 12 rounds : ~400ms (défaut)
- 14 rounds : ~1.6s
- 16 rounds : ~6.4s

**Recommandation** : 12 rounds (équilibre sécurité/performance)

### Structure d'un hash bcrypt

```
$2b$12$KIXhFZq8Y2tW5oMFVXqPyOmKGJN1vY3Q5f0RZz8xBwHqT6vLnK3Yy
│  │  │                     │                              │
│  │  │                     │                              └─ Hash (31 chars)
│  │  │                     └─ Salt (22 chars)
│  │  └─ Cost factor (12 rounds)
│  └─ Version de bcrypt
└─ Identificateur d'algorithme
```

## Tests de sécurité

### Tester le hachage

```python
from app.core.security import get_password_hash, verify_password

def test_password_hashing():
    password = "SecurePassword123!"
    
    # Hash le mot de passe
    hashed = get_password_hash(password)
    
    # Vérifications
    assert hashed != password  # Le hash est différent
    assert verify_password(password, hashed)  # Vérifie correctement
    assert not verify_password("WrongPassword", hashed)  # Rejette les mauvais
    
    # Deux hash du même password sont différents
    hashed2 = get_password_hash(password)
    assert hashed != hashed2  # Grâce au salt
```

### Tester JWT

```python
from app.core.security import create_access_token, decode_token
from datetime import timedelta

def test_jwt_token():
    # Créer un token
    token = create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(minutes=30)
    )
    
    # Décoder le token
    payload = decode_token(token)
    
    assert payload is not None
    assert payload["sub"] == "testuser"
    
    # Token invalide
    invalid_token = "invalid.token.here"
    payload = decode_token(invalid_token)
    assert payload is None
```

## Monitoring et logs

**À logger** :
- ✅ Tentatives de connexion (réussies/échouées)
- ✅ Inscription de nouveaux utilisateurs
- ✅ Tokens expirés
- ❌ Mots de passe (JAMAIS !)
- ❌ Tokens JWT complets (sensibles)

```python
import logging

logger = logging.getLogger("mediassist.auth")

# ✅ Bon
logger.info(f"User {username} logged in successfully")
logger.warning(f"Failed login attempt for {username}")

# ❌ Mauvais
logger.info(f"User password: {password}")  # DANGEREUX !
logger.info(f"JWT token: {token}")  # SENSIBLE !
```

## Ressources

- [JWT.io](https://jwt.io/) : Décoder et tester des JWT
- [Passlib Documentation](https://passlib.readthedocs.io/)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
