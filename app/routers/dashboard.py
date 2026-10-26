from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.config import settings
from app.database import get_db
from app.schemas import Dashboard
from app.security import get_current_user
from app.serializers import incident_out, maintenance_courte, piece_out

router = APIRouter(prefix="/api/dashboard", tags=["Tableau de bord"])


@router.get("", response_model=Dashboard, summary="Indicateurs du tableau de bord")
def tableau_de_bord(db: Session = Depends(get_db), _=Depends(get_current_user)):
    fin = date.today()
    debut = fin - timedelta(days=6)  # les 7 derniers jours, aujourd'hui compris

    lots_semaine = db.scalar(
        select(func.count())
        .select_from(models.LotProduction)
        .where(models.LotProduction.date_production.between(debut, fin))
    )

    arrets = db.execute(
        select(
            models.Atelier.num_atelier,
            models.Atelier.libelle,
            func.coalesce(func.sum(models.Incident.temps_arret), 0),
        )
        .select_from(models.Atelier)
        .outerjoin(models.LigneProduction, models.LigneProduction.num_atelier == models.Atelier.num_atelier)
        .outerjoin(models.LotProduction, models.LotProduction.num_ligne == models.LigneProduction.num_ligne)
        .outerjoin(models.Incident, models.Incident.num_lot == models.LotProduction.num_lot)
        .group_by(models.Atelier.num_atelier, models.Atelier.libelle)
        .order_by(models.Atelier.num_atelier)
    ).all()

    incidents = db.scalars(
        select(models.Incident)
        .options(
            selectinload(models.Incident.type_incident),
            selectinload(models.Incident.lot).selectinload(models.LotProduction.produit),
            selectinload(models.Incident.lot).selectinload(models.LotProduction.ligne).selectinload(models.LigneProduction.atelier),
        )
        .order_by(models.Incident.num_incident.desc())
        .limit(5)
    ).all()

    pieces = db.scalars(
        select(models.Piece)
        .where(models.Piece.quantite_stock <= settings.seuil_stock_faible)
        .order_by(models.Piece.quantite_stock, models.Piece.reference)
    ).all()

    maintenances = db.scalars(
        select(models.Maintenance)
        .options(selectinload(models.Maintenance.machine))
        .order_by(models.Maintenance.date_heure_debut.desc())
        .limit(5)
    ).all()

    return {
        "lots_semaine": lots_semaine,
        "periode_debut": debut,
        "periode_fin": fin,
        "nb_ateliers": db.scalar(select(func.count()).select_from(models.Atelier)),
        "nb_operateurs": db.scalar(select(func.count()).select_from(models.Operateur)),
        "nb_machines": db.scalar(select(func.count()).select_from(models.Machine)),
        "temps_arret_total": db.scalar(select(func.coalesce(func.sum(models.Incident.temps_arret), 0))),
        "arrets_par_atelier": [
            {"num_atelier": num, "atelier": libelle, "total_minutes": int(total)} for num, libelle, total in arrets
        ],
        "derniers_incidents": [incident_out(i) for i in incidents],
        "pieces_stock_faible": [piece_out(p) for p in pieces],
        "seuil_stock_faible": settings.seuil_stock_faible,
        "dernieres_maintenances": [maintenance_courte(m) for m in maintenances],
    }
