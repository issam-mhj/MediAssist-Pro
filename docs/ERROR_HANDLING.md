# Gestion des erreurs - MediAssist-Pro

Ce document liste toutes les exceptions personnalisées et leurs codes HTTP.

## Vue d'ensemble

MediAssist-Pro utilise des exceptions personnalisées pour gérer les erreurs de manière cohérente à travers l'API.

## Exceptions personnalisées

### CredentialsException

**Code HTTP** : `401 Unauthorized`

**Message** : "Could not validate credentials"

**Headers** : `WWW-Authenticate: Bearer`

**Usage** : Levée lorsque :
- Le token JWT est invalide
- Le token JWT est expiré
- Le token JWT est manquant
- L'utilisateur dans le token n'existe pas

**Exemple** :
```python
from app.core.exceptions import CredentialsException

if not token_valid:
    raise CredentialsException()
```

**Réponse JSON** :
```json
{
  "detail": "Could not validate credentials"
}
```

---

### UserNotFoundException

**Code HTTP** : `404 Not Found`

**Message** : "User not found"

**Usage** : Levée lorsque :
- Un utilisateur demandé n'existe pas
- Recherche d'un utilisateur par ID inexistant

**Exemple** :
```python
from app.core.exceptions import UserNotFoundException

user = db.query(User).filter(User.id == user_id).first()
if not user:
    raise UserNotFoundException()
```

**Réponse JSON** :
```json
{
  "detail": "User not found"
}
```

---

### UserAlreadyExistsException

**Code HTTP** : `400 Bad Request`

**Message** : "User already exists"

**Usage** : Levée lorsque :
- Tentative d'inscription avec un username déjà pris
- Tentative de création d'utilisateur en doublon

**Exemple** :
```python
from app.core.exceptions import UserAlreadyExistsException

existing_user = db.query(User).filter(User.username == username).first()
if existing_user:
    raise UserAlreadyExistsException()
```

**Réponse JSON** :
```json
{
  "detail": "User already exists"
}
```

---

### DocumentProcessingException

**Code HTTP** : `500 Internal Server Error`

**Message** : Personnalisable (par défaut : "Error processing document")

**Usage** : Levée lorsque :
- Erreur lors du chargement d'un PDF
- Erreur lors du chunking
- Erreur lors de la génération d'embeddings
- Erreur lors de l'indexation

**Exemple** :
```python
from app.core.exceptions import DocumentProcessingException

try:
    process_pdf(file_path)
except Exception as e:
    raise DocumentProcessingException(detail=f"Failed to process PDF: {str(e)}")
```

**Réponse JSON** :
```json
{
  "detail": "Error processing document"
}
```

---

## Exceptions FastAPI standard

En plus des exceptions personnalisées, l'API utilise les exceptions HTTP standard de FastAPI.

### 401 Unauthorized

**Usage** : Authentification invalide

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"}
)
```

### 403 Forbidden

**Usage** : Permissions insuffisantes

```python
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not enough permissions"
)
```

### 404 Not Found

**Usage** : Ressource non trouvée

```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)
```

### 400 Bad Request

**Usage** : Données invalides

```python
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid data provided"
)
```

### 422 Unprocessable Entity

**Usage** : Validation Pydantic échouée (automatique)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Mapping des codes HTTP

| Code | Nom | Usage |
|------|-----|-------|
| 200 | OK | Succès général |
| 201 | Created | Ressource créée (inscription) |
| 400 | Bad Request | Données invalides |
| 401 | Unauthorized | Authentification requise/invalide |
| 403 | Forbidden | Permissions insuffisantes |
| 404 | Not Found | Ressource inexistante |
| 422 | Unprocessable Entity | Validation échouée |
| 500 | Internal Server Error | Erreur serveur |

---

## Gestion globale des exceptions

FastAPI gère automatiquement les exceptions non capturées et retourne un code 500.

**Exemple de handler personnalisé** :
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
```

---

## Bonnes pratiques

### 1. Utiliser les exceptions personnalisées

```python
# ✅ Bon
raise CredentialsException()

# ❌ Moins bien
raise HTTPException(status_code=401, detail="Invalid credentials")
```

### 2. Messages d'erreur clairs

```python
# ✅ Bon
raise HTTPException(
    status_code=400,
    detail="Password must be at least 8 characters"
)

# ❌ Mauvais
raise HTTPException(status_code=400, detail="Error")
```

### 3. Ne pas exposer d'informations sensibles

```python
# ✅ Bon
raise HTTPException(status_code=401, detail="Invalid credentials")

# ❌ DANGEREUX
raise HTTPException(
    status_code=401,
    detail=f"User {username} not found in database"
)
```

### 4. Logger les erreurs serveur

```python
import logging

logger = logging.getLogger(__name__)

try:
    process_document()
except Exception as e:
    logger.error(f"Document processing failed: {str(e)}")
    raise DocumentProcessingException()
```

---

## Tests d'erreurs

### Tester une exception

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_invalid_credentials():
    response = client.post("/api/auth/login", data={
        "username": "invalid",
        "password": "wrong"
    })
    assert response.status_code == 401
    assert "detail" in response.json()
```

### Tester la validation Pydantic

```python
def test_register_invalid_email():
    response = client.post("/api/auth/register", json={
        "username": "test",
        "email": "not-an-email",  # Email invalide
        "password": "password123"
    })
    assert response.status_code == 422
```

---

## Documentation Swagger

FastAPI génère automatiquement la documentation des erreurs dans Swagger UI (`/docs`).

**Exemple de documentation d'endpoint** :
```python
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    responses={
        400: {"description": "User already exists"},
        422: {"description": "Validation error"}
    }
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    ...
```

---

## Résumé

| Exception | Code | Quand l'utiliser |
|-----------|------|------------------|
| CredentialsException | 401 | Token invalide/expiré |
| UserNotFoundException | 404 | Utilisateur introuvable |
| UserAlreadyExistsException | 400 | Username déjà pris |
| DocumentProcessingException | 500 | Erreur traitement PDF/RAG |
