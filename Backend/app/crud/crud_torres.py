from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from .. import models


# ================
# ---- Torres ----
# ================


def obtener_torre_por_slug(db: Session, slug: str):
    nombre_formal = slug.replace("-", " ").title()  # "santa-fe" -> "Santa Fe"
    torre = db.query(models.Torre).filter(models.Torre.nombre == nombre_formal).first()
    if not torre:
        raise HTTPException(status_code=404, detail=f"Torre '{nombre_formal}' no encontrada")
    return torre


def obtener_torre_detallada_por_slug(db: Session, slug: str):
    nombre_formal = slug.replace("-", " ").title()  # "santa-fe" -> "Santa Fe"

    torre = (
        db.query(models.Torre)
        .options(
            joinedload(models.Torre.pisos)
            .joinedload(models.Piso.apartamentos)
            .joinedload(models.Apartamento.tipo_apartamento)
        )
        .filter(models.Torre.nombre == nombre_formal)
        .first()
    )

    if not torre:
        raise HTTPException(status_code=404, detail=f"Torre '{nombre_formal}' no encontrada")

    pisos_data = []
    for piso in torre.pisos:
        apartamentos_data = [
            {
                "id": apt.id,
                "numero": apt.numero,
                "id_piso": apt.id_piso,
                "tipo_apartamento": apt.tipo_apartamento if apt.tipo_apartamento else None,
            }
            for apt in piso.apartamentos
        ]
        pisos_data.append(
            {
                "id": piso.id,
                "numero": piso.numero,
                "apartamentos": apartamentos_data,
            }
        )

    return {
        "id": torre.id,
        "nombre": torre.nombre,
        "cantidad_pisos": len(torre.pisos),
        "cantidad_apartamentos": sum(len(p.apartamentos) for p in torre.pisos),
        "pisos": pisos_data,
    }


def obtener_torres(db: Session):
    torres = db.query(models.Torre).options(joinedload(models.Torre.pisos).joinedload(models.Piso.apartamentos)).all()
    resultado = []

    for torre in torres:
        cantidad_pisos = len(torre.pisos)
        cantidad_apartamentos = sum(len(piso.apartamentos) for piso in torre.pisos)
        resultado.append(
            {
                "id": torre.id,
                "nombre": torre.nombre,
                "cantidad_pisos": cantidad_pisos,
                "cantidad_apartamentos": cantidad_apartamentos,
            }
        )

    return resultado


# ===============
# ---- Pisos ----
# ===============


def obtener_pisos_por_torre(db: Session, id_torre: int):
    torre = db.query(models.Torre).filter(models.Torre.id == id_torre).first()
    if not torre:
        raise HTTPException(status_code=404, detail="Torre no encontrada")

    pisos = torre.pisos  # Gracias al lazy="selectin", ya trae los pisos
    resultado = []
    for piso in pisos:
        resultado.append(
            {
                "id": piso.id,
                "numero": piso.numero,
                "id_torre": piso.id_torre,
                "cantidad_apartamentos": len(piso.apartamentos),
            }
        )
    return resultado


def obtener_piso_por_numero(db: Session, id_torre: int, numero: int):
    piso = db.query(models.Piso).filter(models.Piso.numero == numero, models.Piso.id_torre == id_torre).first()

    if not piso:
        raise HTTPException(status_code=404, detail="Piso no encontrado")

    return {
        "id": piso.id,
        "numero": piso.numero,
        "id_torre": piso.id_torre,
        "cantidad_apartamentos": len(piso.apartamentos),
    }


# ===============================
# ---- Tipos de Apartamentos ----
# ===============================


def obtener_tipos_apartamentos(db: Session):
    return db.query(models.TipoApartamento).all()


def obtener_tipo_apartamento_por_id(db: Session, id_tipo: int):
    tipo = db.query(models.TipoApartamento).filter(models.TipoApartamento.id == id_tipo).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de apartamento no encontrado")
    return tipo


# ======================
# ---- Apartamentos ----
# ======================


def obtener_apartamentos_por_torre(db: Session, id_torre: int):
    apartamentos = (
        db.query(models.Apartamento)
        .join(models.Piso)
        .options(joinedload(models.Apartamento.tipo_apartamento))
        .filter(models.Piso.id_torre == id_torre)
        .all()
    )
    if not apartamentos:
        raise HTTPException(status_code=404, detail="No se encontraron apartamentos en esta torre")
    return apartamentos


def obtener_apartamentos_por_piso(db: Session, id_piso: int):
    return (
        db.query(models.Apartamento)
        .options(
            joinedload(models.Apartamento.tipo_apartamento),
            joinedload(models.Apartamento.residente),  # 👈 Cargamos el residente también
        )
        .filter(models.Apartamento.id_piso == id_piso)
        .all()
    )
    if not apartamentos:
        raise HTTPException(status_code=404, detail="No se encontraron apartamentos en este piso")
    return apartamentos


def obtener_apartamento_en_piso(db: Session, id_piso: int, id_apartamento: int):
    apt = (
        db.query(models.Apartamento)
        .options(joinedload(models.Apartamento.tipo_apartamento), joinedload(models.Apartamento.residente))
        .filter(models.Apartamento.id == id_apartamento, models.Apartamento.id_piso == id_piso)
        .first()
    )
    if not apt:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")
    return apt
