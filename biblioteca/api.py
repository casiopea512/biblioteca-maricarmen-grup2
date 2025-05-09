import requests
from django.contrib.auth import authenticate
from django.utils import timezone
from django.http import JsonResponse
from ninja import NinjaAPI, Schema
from ninja.security import HttpBasicAuth, HttpBearer
from .models import *
from typing import List, Optional, Union, Literal
import secrets
from ninja.files import UploadedFile
import csv
from google.oauth2 import id_token
# from google.auth.transport import requests
from django.contrib.auth.models import User

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
    grup: Optional[str]

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
        "telefon": user.telefon or "",  # <-- Cambia esto
        "centre": user.centre.nom if hasattr(user, "centre") and user.centre else None,
        "grup": user.grup.nom if hasattr(user, "grup") and user.grup else None,
    }


# Endpoint per actualitzar el perfil d'usuari
class UpdateUserProfile(Schema):
    username: str
    email: str
    first_name: str
    last_name: str
    telefon: str
    centre: Optional[str]  # Se espera el nom del centre
    grup: Optional[str]   # Se espera el nom del grup

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
    if payload.grup:
        grup_obj, _ = Grup.objects.get_or_create(nom=payload.grup)
        user.grup = grup_obj
    else:
        user.grup = None
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


#Endpoint per obtenir la llista d'usuaris
class UserSearchOut(Schema):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    telefon : int

@api.get("/users/{userInfoSearch}", response=List[UserSearchOut])
def search_users(request, userInfoSearch: str):
    users = Usuari.objects.filter(
        models.Q(username__icontains=userInfoSearch) | 
        models.Q(first_name__icontains=userInfoSearch) | 
        models.Q(last_name__icontains(userInfoSearch)) |
        models.Q(email=userInfoSearch) |
        models.Q(telefon__icontains=userInfoSearch)
    )
    return [
        UserSearchOut(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            telefon=user.telefon
        )
        for user in users
    ]

# Endpoint para efectuar un préstamo
from datetime import timedelta

# Endpoint para efectuar un préstamo
@api.post("/makeBorrow/{user_id}/{exemplar_id}", auth=AuthBearer())
def make_borrow(request, user_id: int, exemplar_id: int):
    try:
        # Obtener el usuario autenticado 
        librarian = request.auth 

        # Obtener el usuario por ID
        student = Usuari.objects.get(id=user_id)

        # Obtener el ejemplar por ID
        exemplar = Exemplar.objects.get(id=exemplar_id)

        # Verificar si el ejemplar está disponible para préstamo
        if exemplar.exclos_prestec or exemplar.baixa:
            return JsonResponse({"error": "El ejemplar no está disponible para préstamo."}, status=400)

        # Calcular la fecha devolución (1s)
        data_prestec = now()
        data_retorn = data_prestec + timedelta(weeks=1)

        # Realizar el préstamo
        prestec = Prestec.objects.create(
            usuari=student,          # Estudiante al que se le hace el préstamo
            exemplar=exemplar,       # Ejemplar que se presta
            data_prestec=data_prestec,  # Fecha actual del préstamo
            data_retorn=data_retorn,    # Fecha de retodevoluciónrno
        )

        # Marcar el ejemplar como prestado
        exemplar.exclos_prestec = True
        exemplar.save()

        # Devolver la respuesta
        return JsonResponse({"message": "Préstamo realizado con éxito.", "prestamo_id": prestec.id}, status=200)

    except Usuari.DoesNotExist:
        return JsonResponse({"error": "Usuario no encontrado."}, status=404)
    except Exemplar.DoesNotExist:
        return JsonResponse({"error": "Ejemplar no encontrado."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Endpoint para listar los préstamos de un usuario
class PrestecOut(Schema):
    titol: str
    exemplar: str
    data_prestec: str
    data_retorn: Optional[str]
    retornat: bool
    anotacions: Optional[str]

@api.get("/usuari/{user_id}/prestecs", response=List[PrestecOut], auth=AuthBearer())
def llistar_prestecs(request, user_id: int):
    prestecs = Prestec.objects.filter(usuari_id=user_id).select_related(
        "exemplar__cataleg"
    )

    result = []
    for p in prestecs:
        result.append(PrestecOut(
            titol=p.exemplar.cataleg.titol,
            exemplar=p.exemplar.registre or "",
            data_prestec=p.data_prestec.isoformat(),
            data_retorn=p.data_retorn.isoformat() if p.data_retorn else None,
            retornat=p.retornat,
            anotacions=p.anotacions,
        ))
    return result


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

        nom, cognom1, cognom2, email, telefon, centre_nom, grup_nom = row

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
        grup, _ = Grup.objects.get_or_create(nom=grup_nom)

        Usuari.objects.create(
            username=email,
            first_name=nom,
            last_name=f"{cognom1} {cognom2}",
            email=email,
            telefon=telefon,
            centre=centre,
            grup=grup,
            password=make_password('user123')
        )
        created += 1
        feedback.append(f"Línia {i}: Usuari afegit correctament")

    return CSVImportResult(created=created, feedback=feedback)


def verify_google_token(id_token: str):
    res = requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}')
    if (res.status_code != 200):
        raise ValueError("Token de Google inválido")
    return res.json()


class SocialLoginSchema(Schema):
    token: str
    provider: str 


@api.post("/social-login/")
def social_login(request, data: SocialLoginSchema):
    try:
        if data.provider == "google":
            user_info = verify_google_token(data.token)
            email = user_info["email"]
            name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
            full_name = user_info.get("name", "")
            # Si no hay given_name/family_name, intenta separar el name
            if not name or not last_name:
                if full_name and " " in full_name:
                    name = full_name.split(" ")[0]
                    last_name = " ".join(full_name.split(" ")[1:])
                else:
                    name = full_name or email.split("@")[0]
                    last_name = ""
            # Puedes obtener más campos si los necesitas, como picture, etc.

        else:
            return api.create_response(request, {"error": "Proveïdor no suportat"}, status=400)

        # Buscar usuario por email
        user = Usuari.objects.filter(email=email).first()
        if not user:
            # Si no existe, crear usuario como en seed_db.py
            # Puedes asignar centro y grup por defecto si quieres
            centre, _ = Centre.objects.get_or_create(nom='Institut Esteve Terrades i Illa')
            grup, _ = Grup.objects.get_or_create(nom='AWS2')
            user = Usuari.objects.create(
                username=email.split("@")[0],
                email=email,
                first_name=name,
                last_name=last_name,
                is_active=True,
                centre=centre,
                grup=grup,
                telefon="",  # Google no da teléfono, puedes dejarlo vacío
            )
            # No hay contraseña, solo login social

        # Generar token propio
        token = secrets.token_hex(16)
        user.auth_token = token
        user.save()

        return {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": "Usuari"
            }
        }

    except Exception as e:
        return api.create_response(request, {"error": str(e)}, status=400)