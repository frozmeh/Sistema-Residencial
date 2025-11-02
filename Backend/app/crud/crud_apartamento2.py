from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from .. import models

# --------------------
# TORRES
# --------------------

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from .. import models, schemas

# --------------------
# TORRES
# --------------------


def obtener_torres(db: Session):
    """
    Devuelve todas las torres con:
    - nombre
    - cantidad de pisos
    - cantidad de apartamentos
    - pisos opcionalmente cargados
    """
    torres = db.query(models.Torre).options(joinedload(models.Torre.pisos).joinedload(models.Piso.apartamentos)).all()

    resultado = []
    for torre in torres:
        pisos_schema = []
        for piso in torre.pisos:
            apartamentos_schema = [schemas.ApartamentoOut.from_orm(apt) for apt in piso.apartamentos]
            piso_schema = schemas.PisoOut(
                id=piso.id,
                numero=piso.numero,
                id_torre=piso.id_torre,
                descripcion=piso.descripcion,
                cantidad_apartamentos=len(piso.apartamentos),
                apartamentos=apartamentos_schema,
            )
            pisos_schema.append(piso_schema)

        torre_schema = schemas.TorreOut(
            id=torre.id,
            nombre=torre.nombre,
            descripcion=torre.descripcion,
            cantidad_pisos=len(torre.pisos),
            cantidad_apartamentos=sum(len(p.apartamentos) for p in torre.pisos),
            pisos=pisos_schema,
        )
        resultado.append(torre_schema)

    return resultado


def obtener_torre_por_id(db: Session, id_torre: int):
    torre = (
        db.query(models.Torre)
        .options(joinedload(models.Torre.pisos).joinedload(models.Piso.apartamentos))
        .filter(models.Torre.id == id_torre)
        .first()
    )

    if not torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")

    pisos_schema = []
    for piso in torre.pisos:
        apartamentos_schema = [schemas.ApartamentoOut.from_orm(apt) for apt in piso.apartamentos]
        piso_schema = schemas.PisoOut(
            id=piso.id,
            numero=piso.numero,
            id_torre=piso.id_torre,
            descripcion=piso.descripcion,
            cantidad_apartamentos=len(piso.apartamentos),
            apartamentos=apartamentos_schema,
        )
        pisos_schema.append(piso_schema)

    return schemas.TorreOut(
        id=torre.id,
        nombre=torre.nombre,
        descripcion=torre.descripcion,
        cantidad_pisos=len(torre.pisos),
        cantidad_apartamentos=sum(len(p.apartamentos) for p in torre.pisos),
        pisos=pisos_schema,
    )


from sqlalchemy.orm import Session
from fastapi import HTTPException
from .. import models

# --------------------
# PISOS
# --------------------


def obtener_pisos_por_torre(db: Session, id_torre: int):
    pisos = db.query(models.Piso).filter(models.Piso.id_torre == id_torre).all()
    if not pisos:
        raise HTTPException(status_code=404, detail="No se encontraron pisos")

    resultado = []
    for piso in pisos:
        cantidad_apartamentos = db.query(models.Apartamento).filter(models.Apartamento.id_piso == piso.id).count()
        resultado.append(
            {
                "id": piso.id,
                "numero": piso.numero,
                "id_torre": piso.id_torre,
                "cantidad_apartamentos": cantidad_apartamentos,
            }
        )
    print("Pasé por aquí")
    return resultado


def obtener_piso_por_id_torre(db: Session, id_torre: int, id_piso: int):
    piso = db.query(models.Piso).filter(models.Piso.id == id_piso, models.Piso.id_torre == id_torre).first()

    if not piso:
        raise HTTPException(status_code=404, detail="Piso no encontrado")

    cantidad_apartamentos = db.query(models.Apartamento).filter(models.Apartamento.id_piso == piso.id).count()

    return {
        "id": piso.id,
        "numero": piso.numero,
        "id_torre": piso.id_torre,
        "cantidad_apartamentos": cantidad_apartamentos,
    }


# --------------------
# APARTAMENTOS
# --------------------


def obtener_apartamentos_por_torre(db: Session, id_torre: int):
    apartamentos = db.query(models.Apartamento).join(models.Piso).filter(models.Piso.id_torre == id_torre).all()

    if not apartamentos:
        raise HTTPException(status_code=404, detail="No se encontraron apartamentos en esta torre")

    resultado = []
    for apt in apartamentos:
        tipo = db.query(models.TipoApartamento).filter(models.TipoApartamento.id == apt.id_tipo_apartamento).first()
        resultado.append(
            {
                "id": apt.id,
                "numero": apt.numero,
                "id_piso": apt.id_piso,
                "estado": apt.estado,
                "tipo_apartamento": {
                    "id": tipo.id,
                    "nombre": tipo.nombre,
                    "habitaciones": tipo.habitaciones,
                    "banos": tipo.banos,
                    "porcentaje_aporte": float(tipo.porcentaje_aporte),
                },
            }
        )
    return resultado


def obtener_apartamentos_por_piso(db: Session, id_piso: int):
    apartamentos = db.query(models.Apartamento).filter(models.Apartamento.id_piso == id_piso).all()

    if not apartamentos:
        raise HTTPException(status_code=404, detail="No se encontraron apartamentos en este piso")

    resultado = []
    for apt in apartamentos:
        tipo = db.query(models.TipoApartamento).filter(models.TipoApartamento.id == apt.id_tipo_apartamento).first()
        resultado.append(
            {
                "id": apt.id,
                "numero": apt.numero,
                "id_piso": apt.id_piso,
                "estado": apt.estado,
                "tipo_apartamento": {
                    "id": tipo.id,
                    "nombre": tipo.nombre,
                    "habitaciones": tipo.habitaciones,
                    "banos": tipo.banos,
                    "porcentaje_aporte": float(tipo.porcentaje_aporte),
                },
            }
        )
    return resultado


def obtener_apartamento_en_piso(db: Session, id_torre: int, id_piso: int, id_apartamento: int):
    apt = (
        db.query(models.Apartamento)
        .join(models.Piso)
        .filter(models.Apartamento.id == id_apartamento, models.Piso.id == id_piso, models.Piso.id_torre == id_torre)
        .first()
    )

    if not apt:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")

    tipo = db.query(models.TipoApartamento).filter(models.TipoApartamento.id == apt.id_tipo_apartamento).first()

    return {
        "id": apt.id,
        "numero": apt.numero,
        "id_piso": apt.id_piso,
        "estado": apt.estado,
        "tipo_apartamento": {
            "id": tipo.id,
            "nombre": tipo.nombre,
            "habitaciones": tipo.habitaciones,
            "banos": tipo.banos,
            "porcentaje_aporte": float(tipo.porcentaje_aporte),
        },
    }
