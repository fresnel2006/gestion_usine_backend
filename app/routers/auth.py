from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Utilisateur
from app.schemas import Jeton, LoginIn, UtilisateurConnecte
from app.security import creer_jeton, get_current_user, verifier_mot_de_passe

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


def utilisateur_connecte(u: Utilisateur) -> dict:
    return {
        "login": u.login,
        "role": u.role,
        "matricule": u.matricule,
        "nom_complet": u.operateur.nom_complet if u.operateur else None,
    }


@router.post("/login", response_model=Jeton, summary="Se connecter et obtenir un jeton JWT")
def login(donnees: LoginIn, db: Session = Depends(get_db)):
    utilisateur = db.get(Utilisateur, donnees.login.lower())
    if utilisateur is None or not verifier_mot_de_passe(donnees.mot_de_passe, utilisateur.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect.",
        )
    if not utilisateur.actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé. Contactez l'administrateur.",
        )
    return {"access_token": creer_jeton(utilisateur), "utilisateur": utilisateur_connecte(utilisateur)}


@router.get("/me", response_model=UtilisateurConnecte, summary="Utilisateur connecté")
def moi(utilisateur: Utilisateur = Depends(get_current_user)):
    return utilisateur_connecte(utilisateur)
