"""Schémas Pydantic v2 : validation des entrées et forme des réponses."""
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, field_validator


def Texte(max_length: int):
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=max_length)]


def Code(max_length: int):
    """Identifiant saisi (matricule, référence, code) : sans espaces autour, en majuscules."""
    return Annotated[
        str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=max_length)
    ]


TexteOptionnel200 = Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=200)]
Telephone = Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=20)]
Montant = Annotated[float, Field(ge=0, le=9_999_999_999)]
Numero = Annotated[int, Field(gt=0, le=2_147_483_647)]
ListeOperateurs = Annotated[
    list[Code(10)],
    Field(min_length=1),
    AfterValidator(lambda v: _sans_doublon(v)),
]
def _sans_doublon(v: list[str]) -> list[str]:
    if len(set(v)) != len(v):
        raise ValueError("Un opérateur ne peut être sélectionné qu'une seule fois.")
    return v


Role = Literal["ADMINISTRATEUR", "RESPONSABLE_ATELIER", "COLLABORATEUR_RESPONSABLE", "OPERATEUR"]


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(Schema):
    detail: str


# ---------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------
class LoginIn(Schema):
    login: Texte(40)
    mot_de_passe: Annotated[str, StringConstraints(min_length=1, max_length=128)]


class UtilisateurConnecte(Schema):
    login: str
    role: str
    matricule: str | None
    nom_complet: str | None


class Jeton(Schema):
    access_token: str
    token_type: str = "bearer"
    utilisateur: UtilisateurConnecte


# ---------------------------------------------------------------------
# Références courtes réutilisées dans les réponses
# ---------------------------------------------------------------------
class OperateurCourt(Schema):
    matricule: str
    nom: str
    prenom: str


# ---------------------------------------------------------------------
# Ateliers
# ---------------------------------------------------------------------
class AtelierIn(Schema):
    num_atelier: Numero
    libelle: Texte(100)
    matricule_responsable: Code(10)


class AtelierUpdate(Schema):
    libelle: Texte(100)
    matricule_responsable: Code(10)


class AtelierOut(Schema):
    num_atelier: int
    libelle: str
    matricule_responsable: str
    responsable: OperateurCourt
    nb_lignes: int = 0


# ---------------------------------------------------------------------
# Lignes de production
# ---------------------------------------------------------------------
class LigneIn(Schema):
    num_ligne: Numero
    nb_operateurs_necessaires: Annotated[int, Field(gt=0, le=1000)]
    num_atelier: Numero


class LigneUpdate(Schema):
    nb_operateurs_necessaires: Annotated[int, Field(gt=0, le=1000)]
    num_atelier: Numero


class LigneOut(Schema):
    num_ligne: int
    nb_operateurs_necessaires: int
    num_atelier: int
    atelier_libelle: str
    nb_machines: int = 0
    nb_lots: int = 0


class MachineCourte(Schema):
    num_machine: int
    designation: str


class LotCourt(Schema):
    num_lot: int
    date_production: date
    reference_produit: str
    designation_produit: str


class LigneDetail(LigneOut):
    machines: list[MachineCourte]
    lots: list[LotCourt]


# ---------------------------------------------------------------------
# Produits
# ---------------------------------------------------------------------
class ProduitIn(Schema):
    reference: Code(20)
    designation: Texte(100)
    prix_vente_unitaire: Montant
    quantite_stock: Annotated[int, Field(ge=0, le=2_147_483_647)]


class ProduitUpdate(Schema):
    designation: Texte(100)
    prix_vente_unitaire: Montant
    quantite_stock: Annotated[int, Field(ge=0, le=2_147_483_647)]


class ProduitOut(Schema):
    reference: str
    designation: str
    prix_vente_unitaire: float
    quantite_stock: int


# ---------------------------------------------------------------------
# Lots de production
# ---------------------------------------------------------------------
class LotIn(Schema):
    num_lot: Numero
    date_production: date
    num_ligne: Numero
    reference_produit: Code(20)
    operateurs: ListeOperateurs


class LotUpdate(Schema):
    date_production: date
    num_ligne: Numero
    reference_produit: Code(20)
    operateurs: ListeOperateurs


class LotOut(Schema):
    num_lot: int
    date_production: date
    num_ligne: int
    num_atelier: int
    atelier_libelle: str
    reference_produit: str
    designation_produit: str
    operateurs: list[OperateurCourt]
    nb_incidents: int = 0
    temps_arret_total: int = 0


# ---------------------------------------------------------------------
# Opérateurs et équipes
# ---------------------------------------------------------------------
class OperateurIn(Schema):
    matricule: Code(10)
    nom: Texte(60)
    prenom: Texte(80)
    date_entree: date
    num_equipe: Numero


class OperateurUpdate(Schema):
    nom: Texte(60)
    prenom: Texte(80)
    date_entree: date
    num_equipe: Numero


class OperateurOut(Schema):
    matricule: str
    nom: str
    prenom: str
    date_entree: date
    num_equipe: int
    equipe_libelle: str
    est_responsable_equipe: bool = False
    atelier_responsable: str | None = None
    compte: str | None = None


class MaintenanceCourte(Schema):
    num_maintenance: int
    date_heure_debut: datetime
    duree: int
    num_machine: int
    designation_machine: str


class OperateurDetail(OperateurOut):
    lots: list[LotCourt]
    maintenances: list[MaintenanceCourte]


class EquipeIn(Schema):
    num_equipe: Numero
    libelle: Texte(100)
    matricule_responsable: Annotated[str | None, StringConstraints(strip_whitespace=True, to_upper=True, max_length=10)] = None


class EquipeUpdate(Schema):
    libelle: Texte(100)
    matricule_responsable: Annotated[str | None, StringConstraints(strip_whitespace=True, to_upper=True, max_length=10)] = None


class EquipeOut(Schema):
    num_equipe: int
    libelle: str
    matricule_responsable: str | None
    responsable: OperateurCourt | None
    nb_operateurs: int = 0
    operateurs: list[OperateurCourt] = []


# ---------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------
class TypeIncidentIn(Schema):
    code_type: Code(10)
    libelle: Texte(100)


class TypeIncidentUpdate(Schema):
    libelle: Texte(100)


class TypeIncidentOut(Schema):
    code_type: str
    libelle: str
    nb_incidents: int = 0


class IncidentIn(Schema):
    num_lot: Numero
    code_type: Code(10)
    temps_arret: Annotated[int, Field(gt=0, le=100_000)]


class IncidentOut(Schema):
    num_incident: int
    temps_arret: int
    num_lot: int
    date_production: date
    num_ligne: int
    atelier_libelle: str
    designation_produit: str
    code_type: str
    type_libelle: str


class StatLigne(Schema):
    cle: str
    libelle: str
    nb_incidents: int
    temps_arret_total: int


class IncidentStats(Schema):
    par_lot: list[StatLigne]
    par_ligne: list[StatLigne]
    par_atelier: list[StatLigne]
    total_minutes: int


# ---------------------------------------------------------------------
# Machines et maintenances
# ---------------------------------------------------------------------
class MachineIn(Schema):
    num_machine: Numero
    designation: Texte(100)
    num_ligne: Numero


class MachineUpdate(Schema):
    designation: Texte(100)
    num_ligne: Numero


class MachineOut(Schema):
    num_machine: int
    designation: str
    num_ligne: int
    atelier_libelle: str
    nb_maintenances: int = 0
    derniere_maintenance: datetime | None = None


class MachineDetail(MachineOut):
    maintenances: list[MaintenanceCourte]


class PieceConsommeeIn(Schema):
    reference_piece: Code(20)
    quantite: Annotated[int, Field(gt=0, le=100_000)]


class PieceConsommeeOut(Schema):
    reference_piece: str
    libelle: str
    quantite: int
    prix_unitaire_ht: float
    montant: float


class MaintenanceIn(Schema):
    num_machine: Numero
    date_heure_debut: datetime
    duree: Annotated[int, Field(gt=0, le=100_000)]
    operateurs: ListeOperateurs
    pieces: list[PieceConsommeeIn] = []

    @field_validator("pieces")
    @classmethod
    def pieces_uniques(cls, v: list[PieceConsommeeIn]) -> list[PieceConsommeeIn]:
        refs = [p.reference_piece for p in v]
        if len(set(refs)) != len(refs):
            raise ValueError("Une même pièce ne peut apparaître qu'une seule fois : regroupez les quantités.")
        return v


class MaintenanceUpdate(Schema):
    num_machine: Numero
    date_heure_debut: datetime
    duree: Annotated[int, Field(gt=0, le=100_000)]
    operateurs: ListeOperateurs


class MaintenanceOut(Schema):
    num_maintenance: int
    date_heure_debut: datetime
    duree: int
    num_machine: int
    designation_machine: str
    num_ligne: int
    operateurs: list[OperateurCourt]
    pieces: list[PieceConsommeeOut]
    cout_pieces: float


# ---------------------------------------------------------------------
# Pièces, nomenclature, achats
# ---------------------------------------------------------------------
class PieceIn(Schema):
    reference: Code(20)
    libelle: Texte(100)
    prix_unitaire_ht: Montant
    quantite_stock: Annotated[int, Field(ge=0, le=2_147_483_647)]


class PieceUpdate(Schema):
    libelle: Texte(100)
    prix_unitaire_ht: Montant
    quantite_stock: Annotated[int, Field(ge=0, le=2_147_483_647)]


class PieceOut(Schema):
    reference: str
    libelle: str
    prix_unitaire_ht: float
    quantite_stock: int
    stock_faible: bool = False
    nb_composants: int = 0


class ComposantIn(Schema):
    reference_composant: Code(20)
    quantite: Annotated[int, Field(gt=0, le=100_000)]


class ComposantUpdate(Schema):
    quantite: Annotated[int, Field(gt=0, le=100_000)]


class NoeudNomenclature(Schema):
    reference: str
    libelle: str
    quantite: int
    quantite_stock: int
    composants: list["NoeudNomenclature"] = []


class Nomenclature(Schema):
    reference: str
    libelle: str
    composants: list[NoeudNomenclature]
    utilisee_dans: list[NoeudNomenclature]


class NomenclatureLigne(Schema):
    reference_composee: str
    libelle_composee: str
    reference_composant: str
    libelle_composant: str
    quantite: int


class AchatIn(Schema):
    code_fournisseur: Code(10)
    date_achat: date
    prix_achat: Montant
    quantite: Annotated[int, Field(gt=0, le=1_000_000)]


class AchatGlobalIn(AchatIn):
    reference_piece: Code(20)


class AchatOut(Schema):
    reference_piece: str
    libelle_piece: str
    code_fournisseur: str
    raison_sociale: str
    date_achat: date
    prix_achat: float
    quantite: int
    montant: float


# ---------------------------------------------------------------------
# Fournisseurs
# ---------------------------------------------------------------------
class FournisseurIn(Schema):
    code_fournisseur: Code(10)
    raison_sociale: Texte(120)
    adresse: TexteOptionnel200 = None
    telephone: Telephone = None


class FournisseurUpdate(Schema):
    raison_sociale: Texte(120)
    adresse: TexteOptionnel200 = None
    telephone: Telephone = None


class FournisseurOut(Schema):
    code_fournisseur: str
    raison_sociale: str
    adresse: str | None
    telephone: str | None
    nb_achats: int = 0


class PieceFournie(Schema):
    reference_piece: str
    libelle: str
    nb_achats: int
    quantite_totale: int
    dernier_prix: float
    derniere_date: date


class FournisseurDetail(FournisseurOut):
    pieces: list[PieceFournie]
    achats: list[AchatOut]


# ---------------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------------
class UtilisateurIn(Schema):
    login: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=3, max_length=40, pattern=r"^[a-z0-9._-]+$")]
    mot_de_passe: Annotated[str, StringConstraints(min_length=6, max_length=72)]
    role: Role
    matricule: Annotated[str | None, StringConstraints(strip_whitespace=True, to_upper=True, max_length=10)] = None
    actif: bool = True


class UtilisateurUpdate(Schema):
    role: Role
    matricule: Annotated[str | None, StringConstraints(strip_whitespace=True, to_upper=True, max_length=10)] = None
    actif: bool
    mot_de_passe: Annotated[str | None, StringConstraints(max_length=72)] = None

    @field_validator("mot_de_passe")
    @classmethod
    def longueur(cls, v: str | None) -> str | None:
        if v and len(v) < 6:
            raise ValueError("Le mot de passe doit contenir au moins 6 caractères.")
        return v or None


class UtilisateurOut(Schema):
    login: str
    role: str
    matricule: str | None
    nom_complet: str | None
    actif: bool


# ---------------------------------------------------------------------
# Tableau de bord
# ---------------------------------------------------------------------
class ArretAtelier(Schema):
    num_atelier: int
    atelier: str
    total_minutes: int


class Dashboard(Schema):
    lots_semaine: int
    periode_debut: date
    periode_fin: date
    nb_ateliers: int
    nb_operateurs: int
    nb_machines: int
    temps_arret_total: int
    arrets_par_atelier: list[ArretAtelier]
    derniers_incidents: list[IncidentOut]
    pieces_stock_faible: list[PieceOut]
    seuil_stock_faible: int
    dernieres_maintenances: list[MaintenanceCourte]
