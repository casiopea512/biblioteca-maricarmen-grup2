from django.contrib.auth import authenticate
from ninja import NinjaAPI, Schema
from ninja.security import HttpBasicAuth, HttpBearer
from .models import *
from typing import List, Optional, Union, Literal
import secrets
from ninja.files import UploadedFile
import csv

strcataleg = Literal["llibre", "indefinit"]

api = NinjaAPI()


# Autenticació bàsica
class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(username=username, password=password)
        if user:
            # Genera un token simple
            token = secrets.token_hex(16)
            user.auth_token = token
            user.save()
            return token
        return None

# Autenticació per Token Bearer
class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            user = Usuari.objects.get(auth_token=token)
            return user
        except Usuari.DoesNotExist:
            return None

# Endpoint per obtenir un token
@api.get("/token", auth=BasicAuth())
@api.get("/token/", auth=BasicAuth())
def obtenir_token(request):
    return {"token": request.auth}


# Endpoint para obetener el tipo de usuario
class UserInfo(Schema):
    id: int
    username: str
    is_staff: bool
    is_superuser: bool
    email: str
    first_name: str
    last_name: str
    imatge: Optional[str]
    telefon: str
    centre: Optional[str]
    cicle: Optional[str]

@api.get("/usuari/qui-soc", response=UserInfo, auth=AuthBearer())
def qui_soc(request):
    user = request.auth
    return {
        "id": user.id,
        "username": user.username,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "imatge": user.imatge.url if user.imatge else None,
        "telefon": user.telefon,
        "centre": user.centre.nom if hasattr(user, "centre") and user.centre else None,
        "cicle": user.cicle.nom if hasattr(user, "cicle") and user.cicle else None,
    }

# Endpoint per actualitzar el perfil d'usuari
class UpdateUserProfile(Schema):
    username: str
    email: str
    first_name: str
    last_name: str
    telefon: str
    centre: Optional[str]  # Se espera el nom del centre
    cicle: Optional[str]   # Se espera el nom del cicle

@api.put("/usuari/actualitzar-perfil", auth=AuthBearer())
def update_profile(request, payload: UpdateUserProfile):
    user = request.auth
    user.username = payload.username
    user.email = payload.email
    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.telefon = payload.telefon
    if payload.centre:
        centre_obj, _ = Centre.objects.get_or_create(nom=payload.centre)
        user.centre = centre_obj
    else:
        user.centre = None
    if payload.cicle:
        cicle_obj, _ = Cicle.objects.get_or_create(nom=payload.cicle)
        user.cicle = cicle_obj
    else:
        user.cicle = None
    user.save()
    return {"success": True}


class CatalegOut(Schema):
    id: int
    titol: str
    autor: Optional[str]

class LlibreOut(CatalegOut):
    editorial: Optional[str]
    ISBN: Optional[str]

class ExemplarOut(Schema):
    id: int
    registre: str
    exclos_prestec: bool
    baixa: bool
    cataleg: Union[LlibreOut,CatalegOut]
    tipus: strcataleg

class LlibreIn(Schema):
    titol: str
    editorial: str


@api.get("/cataleg", response=List[Union[LlibreOut, CatalegOut]])
@api.get("/cataleg/", response=List[Union[LlibreOut, CatalegOut]])
def get_llibres(request):
    qs = Cataleg.objects.all()
    result = []
    for item in qs:
        if hasattr(item, "llibre"):
            schema = LlibreOut.from_orm(item.llibre)
        else:
            schema = CatalegOut.from_orm(item)
        result.append(schema)
    return result

@api.get("/exemplars", response=List[ExemplarOut])
@api.get("/exemplars/", response=List[ExemplarOut])
def get_exemplars(request):
    # carreguem objectes amb els proxy models relacionats exactes
    exemplars = Exemplar.objects.select_related(
        "cataleg__llibre",
        "cataleg__revista",
        "cataleg__cd",
        "cataleg__dvd",
        "cataleg__br",
        "cataleg__dispositiu",
    ).all()
    result = []

    for exemplar in exemplars:
        cataleg_instance = exemplar.cataleg

        # Determinar el tipus de l'objecte Cataleg
        if hasattr(cataleg_instance, "llibre"):
            cataleg_schema = LlibreOut.from_orm(cataleg_instance.llibre)
            tipus = "llibre"
        #elif hasattr(cataleg_instance, "dispositiu"):
        #    cataleg_schema = LlibreOut.from_orm(cataleg_instance.dispositiu)
        # TODO: afegir altres esquemes
        else:
            cataleg_schema = CatalegOut.from_orm(cataleg_instance)
            tipus = "indefinit"

        # Afegir l'Exemplar amb el Cataleg serialitzat
        result.append(
            ExemplarOut(
                id=exemplar.id,
                registre=exemplar.registre,
                exclos_prestec=exemplar.exclos_prestec,
                baixa=exemplar.baixa,
                cataleg=cataleg_schema,
                tipus=tipus,
            )
        )

    return result

@api.get("/cataleg/{tipus}/{catalog_pk}", response=Union[LlibreOut, CatalegOut])
def get_cataleg_detail(request, tipus: strcataleg, catalog_pk: int):
    try:
        catalog_item = Cataleg.objects.get(pk=catalog_pk)
    except Cataleg.DoesNotExist:
        return api.create_response(request, {"error": "Catàleg no trobat"}, status=404)
    
    if tipus == "llibre" and hasattr(catalog_item, "llibre"):
        return LlibreOut.from_orm(catalog_item.llibre)
    else:
        return CatalegOut.from_orm(catalog_item)

class CSVImportResult(Schema):
    created: int
    feedback: List[str]

@api.post("/import-csv", response=CSVImportResult)
def import_usuaris(request, file: UploadedFile):
    if not file.name.endswith(".csv"):
        return CSVImportResult(created=0, feedback=["El fitxer no és un .csv"])

    decoded = file.read().decode("utf-8").splitlines()
    if not decoded:
        return CSVImportResult(created=0, feedback=["El fitxer està buit"])
    
    reader = csv.reader(decoded)
    created = 0
    feedback = []

    for i, row in enumerate(reader, start=1):
        if len(row) != 7:
            feedback.append(f"Línia {i}: format incorrecte (esperat 7 columnes)")
            continue

        nom, cognom1, cognom2, email, telefon, centre_nom, cicle_nom = row

        if not nom or not cognom1:
            feedback.append(f"Línia {i}: Falta nom o cognoms")
            continue

        if not email or "@" not in email or "." not in email:
            feedback.append(f"Línia {i}: Correu electrònic invàlid")
            continue

        parts = email.split("@")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            feedback.append(f"Línia {i}: Correu electrònic invàlid")
            continue

        username_part, domain_part = parts
        if domain_part.startswith(".") or domain_part.endswith(".") or "." not in domain_part:
            feedback.append(f"Línia {i}: Correu electrònic invàlid")
            continue

        if not telefon.isdigit() or len(telefon) != 9:
            feedback.append(f"Línia {i}: Telèfon invàlid")
            continue

        if Usuari.objects.filter(email=email).exists():
            feedback.append(f"Línia {i}: Usuari amb aquest correu ja existeix")
            continue

        centre, _ = Centre.objects.get_or_create(nom=centre_nom)
        cicle, _ = Cicle.objects.get_or_create(nom=cicle_nom)

        Usuari.objects.create(
            username=email,
            first_name=nom,
            last_name=f"{cognom1} {cognom2}",
            email=email,
            telefon=telefon,
            centre=centre,
            cicle=cicle,
            password=make_password('user123')
        )
        created += 1
        feedback.append(f"Línia {i}: Usuari afegit correctament")

    return CSVImportResult(created=created, feedback=feedback)