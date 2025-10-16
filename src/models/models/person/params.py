# person/params.py

from typing import Optional
from enum import Enum
from dataclasses import dataclass

class Sex(Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTER = "neuter"

class PEventType(Enum):
    BIRTH = "birth"
    BAPTISM = "baptism"
    DEATH = "death"
    BURIAL = "burial"
    CREMATION = "cremation"
    ACCOMPLISHMENT = "accomplishment"
    ACQUISITION = "acquisition"
    ADHESION = "adhesion"
    BAPTISM_LDS = "baptismLDS"
    BAR_MITZVAH = "barMitzvah"
    BAT_MITZVAH = "batMitzvah"
    BENEDICTION = "benediction"
    CHANGE_NAME = "changeName"
    CIRCUMCISION = "circumcision"
    CONFIRMATION = "confirmation"
    CONFIRMATION_LDS = "confirmationLDS"
    DECORATION = "decoration"
    DEMOBILISATION_MILITAIRE = "demobilisationMilitaire"
    DIPLOMA = "diploma"
    DISTINCTION = "distinction"
    DOTATION = "dotation"
    DOTATION_LDS = "dotationLDS"
    EDUCATION = "education"
    ELECTION = "election"
    EMIGRATION = "emigration"
    EXCOMMUNICATION = "excommunication"
    FAMILY_LINK_LDS = "familyLinkLDS"
    FIRST_COMMUNION = "firstCommunion"
    FUNERAL = "funeral"
    GRADUATE = "graduate"
    HOSPITALISATION = "hospitalisation"
    ILLNESS = "illness"
    IMMIGRATION = "immigration"
    LISTE_PASSENGER = "listePassenger"
    MILITARY_DISTINCTION = "militaryDistinction"
    MILITARY_PROMOTION = "militaryPromotion"
    MILITARY_SERVICE = "militaryService"
    MOBILISATION_MILITAIRE = "mobilisationMilitaire"
    NATURALISATION = "naturalisation"
    OCCUPATION = "occupation"
    ORDINATION = "ordination"
    PROPERTY = "property"
    RECENSEMENT = "recensement"
    RESIDENCE = "residence"
    RETIRED = "retired"
    SCELLENT_CHILD_LDS = "scellentChildLDS"
    SCELLENT_PARENT_LDS = "scellentParentLDS"
    SCELLENT_SPOUSE_LDS = "scellentSpouseLDS"
    VENTE_BIEN = "venteBien"
    WILL = "will"
    NAME = str

@dataclass
class Title:
    name: str
    # Add more fields as needed

class RelationType(Enum):
    ADOPTION = "adoption"
    RECOGNITION = "recognition"
    CANDIDATE_PARENT = "candidate parent"
    GOD_PARENT = "god parent"
    FOSTER_PARENT = "foster parent"

@dataclass
class Relation:
    r_type: RelationType
    r_fath: Optional[int] = None  # Use person ID
    r_moth: Optional[int] = None  # Use person ID
    r_sources: str = ""
