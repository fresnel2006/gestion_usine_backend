"""Remplace les fausses empreintes du script SQL par de vraies empreintes bcrypt.

Usage (depuis le dossier backend, venv activé) :
    python seed_users.py

Le script est idempotent : on peut le relancer sans risque.
"""
from app.database import SessionLocal
from app.models import Utilisateur
from app.security import hacher_mot_de_passe

MOTS_DE_PASSE_TEST = {
    "admin": "Admin@2026",
    "itoure": "Atelier@2026",
    "mbamba": "Equipe@2026",
    "knguessan": "Operateur@2026",
}


def main() -> None:
    with SessionLocal() as db:
        for login, mot_de_passe in MOTS_DE_PASSE_TEST.items():
            utilisateur = db.get(Utilisateur, login)
            if utilisateur is None:
                print(f"  - {login} : compte absent de la base, ignoré")
                continue
            utilisateur.mot_de_passe = hacher_mot_de_passe(mot_de_passe)
            print(f"  - {login} ({utilisateur.role}) : mot de passe = {mot_de_passe}")
        db.commit()
    print("Empreintes bcrypt enregistrées.")


if __name__ == "__main__":
    main()
