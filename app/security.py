"""Authentification JWT, hachage bcrypt et contrôle des droits par rôle."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Utilisateur

ADMIN = "ADMINISTRATEUR"
RESP_ATELIER = "RESPONSABLE_ATELIER"
COLLAB_RESP = "COLLABORATEUR_RESPONSABLE"
OPERATEUR = "OPERATEUR"
ROLES = (ADMIN, RESP_ATELIER, COLLAB_RESP, OPERATEUR)

# Matrice des droits d'écriture (la lecture est ouverte à tout utilisateur connecté).
# Le collaborateur responsable est une spécialisation de l'opérateur : il reprend ses droits.
ECRITURE_PRODUCTION = (ADMIN, RESP_ATELIER)  # ateliers, lignes, lots, produits
ECRITURE_RH = (ADMIN, COLLAB_RESP)  # opérateurs, équipes
ECRITURE_INCIDENTS = (ADMIN, COLLAB_RESP)  # modifier / supprimer incidents, types d'incident
DECLARATION_INCIDENT = (ADMIN, COLLAB_RESP, OPERATEUR)  # déclarer un incident
ECRITURE_MAINTENANCE = (ADMIN, COLLAB_RESP, OPERATEUR)  # machines, maintenances, pièces, achats
ECRITURE_FOURNISSEURS = (ADMIN,)
GESTION_COMPTES = (ADMIN,)

bearer = HTTPBearer(auto_error=False, description="Jeton obtenu via POST /api/auth/login")


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe: str, empreinte: str) -> bool:
    try:
        return bcrypt.checkpw(mot_de_passe.encode("utf-8"), empreinte.encode("utf-8"))
    except ValueError:
        # Empreinte invalide (par exemple les fausses empreintes du script SQL)
        return False


def creer_jeton(utilisateur: Utilisateur) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    charge = {"sub": utilisateur.login, "role": utilisateur.role, "exp": expiration}
    return jwt.encode(charge, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Utilisateur:
    non_authentifie = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise. Veuillez vous connecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise non_authentifie
    try:
        charge = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Votre session a expiré. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise non_authentifie
    utilisateur = db.get(Utilisateur, charge.get("sub"))
    if utilisateur is None or not utilisateur.actif:
        raise non_authentifie
    return utilisateur


def require_roles(*roles: str):
    """Dépendance : refuse la requête (403) si le rôle de l'utilisateur n'est pas autorisé."""

    def verifier(utilisateur: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if utilisateur.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les droits nécessaires pour effectuer cette action.",
            )
        return utilisateur

    return verifier
