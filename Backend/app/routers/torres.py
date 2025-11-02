from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/torres", tags=["Torres"])


# ================
# ---- Torres ----
# ================


@router.get("/", response_model=list[schemas.TorreOut])
def obtener_torres(db: Session = Depends(get_db)):
    return crud.obtener_torres(db)


@router.get("/{slug_torre}", response_model=schemas.TorreCompletaOut)
def obtener_torre_detallada(slug_torre: str, db: Session = Depends(get_db)):
    return crud.obtener_torre_detallada_por_slug(db, slug_torre)


# ===============
# ---- Pisos ----
# ===============


@router.get("/{slug_torre}/pisos", response_model=list[schemas.PisoOut])
def obtener_pisos_torre(slug_torre: str, db: Session = Depends(get_db)):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    return crud.obtener_pisos_por_torre(db, torre.id)


@router.get("/{slug_torre}/pisos/{numero_piso}", response_model=schemas.PisoOut)
def obtener_piso_por_numero(slug_torre: str, numero_piso: int, db: Session = Depends(get_db)):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    return crud.obtener_piso_por_numero(db, torre.id, numero_piso)


# ======================
# ---- Apartamentos ----
# ======================


@router.get("/{slug_torre}/pisos/{numero_piso}/apartamentos", response_model=list[schemas.ApartamentoOut])
def obtener_apartamentos_por_piso(slug_torre: str, numero_piso: int, db: Session = Depends(get_db)):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    piso = crud.obtener_piso_por_numero(db, torre.id, numero_piso)
    return crud.obtener_apartamentos_por_piso(db, piso["id"])


@router.get("/{slug_torre}/pisos/{numero_piso}/apartamentos/{id_apartamento}", response_model=schemas.ApartamentoOut)
def obtener_apartamento(slug_torre: str, numero_piso: int, id_apartamento: int, db: Session = Depends(get_db)):
    torre = crud.obtener_torre_por_slug(db, slug_torre)
    piso = crud.obtener_piso_por_numero(db, torre.id, numero_piso)
    return crud.obtener_apartamento_en_piso(db, piso["id"], id_apartamento)
