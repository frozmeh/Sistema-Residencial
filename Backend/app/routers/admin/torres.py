from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ... import crud, schemas, models
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/torres", tags=["Torres (Administración)"])

# =================
# ---- Torres ----
# =================


@router.get("/", response_model=list[schemas.TorreOut])
def obtener_torres(db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_torres(db)


@router.get("/{slug_torre}", response_model=schemas.TorreCompletaOut)
def obtener_torre_detallada(slug_torre: str, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    return crud.obtener_torre_detallada_por_slug(db, slug_torre)


# =================
# ---- Pisos ----
# =================


@router.get("/{slug_torre}/pisos", response_model=list[schemas.PisoOut])
def obtener_pisos_torre(slug_torre: str, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    return crud.obtener_pisos_por_torre(db, torre.id)


@router.get("/{slug_torre}/pisos/{numero_piso}", response_model=schemas.PisoOut)
def obtener_piso_por_numero(
    slug_torre: str, numero_piso: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    return crud.obtener_piso_por_numero(db, torre.id, numero_piso)


# ========================
# ---- Apartamentos ----
# ========================


@router.get("/{slug_torre}/pisos/{numero_piso}/apartamentos", response_model=list[schemas.ApartamentoOut])
def obtener_apartamentos_por_piso(
    slug_torre: str, numero_piso: int, db: Session = Depends(get_db), admin=Depends(verificar_admin)
):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    piso = crud.obtener_piso_por_numero(db, torre.id, numero_piso)
    return crud.obtener_apartamentos_por_piso(db, piso["id"])


@router.get("/{slug_torre}/pisos/{numero_piso}/apartamentos/{id_apartamento}", response_model=schemas.ApartamentoOut)
def obtener_apartamento(
    slug_torre: str,
    numero_piso: int,
    id_apartamento: int,
    db: Session = Depends(get_db),
    admin=Depends(verificar_admin),
):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    piso = crud.obtener_piso_por_numero(db, torre.id, numero_piso)
    return crud.obtener_apartamento_en_piso(db, piso["id"], id_apartamento)


@router.get("/{slug_torre}/apartamentos", response_model=list[schemas.ApartamentoOut])
def obtener_apartamentos_por_torre(slug_torre: str, db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    return crud.obtener_apartamentos_por_torre(db, torre.id)


@router.get("/estadisticas/generales")
def estadisticas_generales_torres(db: Session = Depends(get_db), admin=Depends(verificar_admin)):
    torres = crud.obtener_torres(db)
    total_apartamentos = sum(t.cantidad_apartamentos for t in torres)
    apartamentos_ocupados = db.query(models.Apartamento).filter(models.Apartamento.estado == "Ocupado").count()

    return {
        "total_torres": len(torres),
        "total_apartamentos": total_apartamentos,
        "apartamentos_ocupados": apartamentos_ocupados,
        "apartamentos_disponibles": total_apartamentos - apartamentos_ocupados,
        "tasa_ocupacion": (apartamentos_ocupados / total_apartamentos * 100) if total_apartamentos > 0 else 0,
    }
