from django.contrib.auth import authenticate
from ninja import NinjaAPI, Schema
from ninja.security import HttpBasicAuth, HttpBearer
from .models import *
from typing import List, Optional, Union, Literal
import secrets
from ninja.files import UploadedFile
import csv

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


###########


class CatalegOut(Schema):
    id: int
    titol: Optional[str]
    autor: Optional[str]

class LlibreOut(CatalegOut):
    editorial: Optional[str]
    ISBN: Optional[str]

@api.get("/cataleg", response=List[ CatalegOut])
@api.get("/cataleg/", response=List[CatalegOut])
def get_llibres(request):
    qs = Cataleg.objects.all()
    result = []
    for item in qs:
        if hasattr(item, "llibre"):
            schema = LlibreOut.from_orm(item.llibre)
        else:
            schema = CatalegOut.from_orm(item)

        if schema.autor is None:
            schema.autor = "No es coneix l'autor"
        
        result.append(schema)
    return result


# Endpoint per obtenir detalls d'un Cataleg específic
@api.get("/cataleg/{id}", response=dict)
def get_cataleg(request, id: int):
    try:
        cataleg = Cataleg.objects.get(id=id)
    except Cataleg.DoesNotExist:
        return {"detail": "Catàleg no trobat"}
    
    # Datos comunes a todos los Cataleg
    data = {
        "id": cataleg.id,
        "titol": cataleg.titol,
        "titol_original": cataleg.titol_original,
        "autor": cataleg.autor,
        "CDU": cataleg.CDU,
        "signatura": cataleg.signatura,
        "data_edicio": cataleg.data_edicio.isoformat() if cataleg.data_edicio else None,
        "resum": cataleg.resum,
        "anotacions": cataleg.anotacions,
        "mides": cataleg.mides,
        "tags": [tag.nom for tag in cataleg.tags.all()]  # Se asume que Categoria tiene el campo 'nom'
    }
    
    # Datos de la subclase específica, si aplica
    subclass_data = {}
    
    if hasattr(cataleg, 'llibre'):
        llibre = cataleg.llibre
        subclass_data = {
            "type": "Llibre",
            "ISBN": llibre.ISBN,
            "editorial": llibre.editorial,
            "colleccio": llibre.colleccio,
            "lloc": llibre.lloc,
            "pais": llibre.pais.nom if llibre.pais else None,
            "llengua": llibre.llengua.nom if llibre.llengua else None,
            "numero": llibre.numero,
            "volums": llibre.volums,
            "pagines": llibre.pagines,
            "info_url": llibre.info_url,
            "preview_url": llibre.preview_url,
            "thumbnail_url": llibre.thumbnail_url
        }
    elif hasattr(cataleg, 'revista'):
        revista = cataleg.revista
        subclass_data = {
            "type": "Revista",
            "ISSN": revista.ISSN,
            "editorial": revista.editorial,
            "lloc": revista.lloc,
            "pais": revista.pais.nom if revista.pais else None,
            "llengua": revista.llengua.nom if revista.llengua else None,
            "numero": revista.numero,
            "volums": revista.volums,
            "pagines": revista.pagines
        }
    elif hasattr(cataleg, 'cd'):
        cd = cataleg.cd
        subclass_data = {
            "type": "CD",
            "discografica": cd.discografica,
            "estil": cd.estil,
            "duracio": str(cd.duracio)
        }
    elif hasattr(cataleg, 'dvd'):
        dvd = cataleg.dvd
        subclass_data = {
            "type": "DVD",
            "productora": dvd.productora,
            "duracio": str(dvd.duracio)
        }
    elif hasattr(cataleg, 'br'):
        br = cataleg.br
        subclass_data = {
            "type": "BR",
            "productora": br.productora,
            "duracio": str(br.duracio)
        }
    elif hasattr(cataleg, 'dispositiu'):
        dispositiu = cataleg.dispositiu
        subclass_data = {
            "type": "Dispositiu",
            "marca": dispositiu.marca,
            "model": dispositiu.model
        }
    else:
        subclass_data = {"type": "Cataleg"}
    
    data["subclass"] = subclass_data

    # Incluir todos los ejemplares asociados a este Cataleg
    exemplars = cataleg.exemplar_set.all()
    exemplar_list = []
    for exemplar in exemplars:
        exemplar_list.append({
            "id": exemplar.id,
            "registre": exemplar.registre,
            "exclos_prestec": exemplar.exclos_prestec,
            "baixa": exemplar.baixa,
            "centre": exemplar.centre.nom if exemplar.centre else "No disponible"
        })
    
    data["exemplars"] = exemplar_list

    return data


###########


# Endpoint per importar usuaris des d'un fitxer CSV
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