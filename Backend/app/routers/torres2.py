from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from .. import crud, schemas, models
from ..database import get_db

router = APIRouter(prefix="/torres", tags=["Torres"])


# ---- GET /torres ----
@router.get("/", response_model=list[schemas.TorreOut])
def listar_torres(db: Session = Depends(get_db)):
    torres = db.query(models.Torre).options(joinedload(models.Torre.pisos).joinedload(models.Piso.apartamentos)).all()
    if not torres:
        raise HTTPException(status_code=404, detail="No se encontraron torres")

    resultado = []
    for torre in torres:
        resultado.append(
            {
                "id": torre.id,
                "nombre": torre.nombre,
                "descripcion": torre.descripcion,
                "pisos": [],  # opcional, vacío para este endpoint
                "cantidad_pisos": len(torre.pisos),
                "cantidad_apartamentos": sum(len(p.apartamentos) for p in torre.pisos),
            }
        )
    return resultado


# ---- GET /torres/{id_torre} ----
@router.get("/{id_torre}", response_model=schemas.PisoOut)
def obtener_torre(id_torre: int, db: Session = Depends(get_db)):
    piso = (
        db.query(models.Piso).options(joinedload(models.Piso.apartamentos)).filter(models.Torre.id == id_torre).first()
    )
    if not piso:
        raise HTTPException(status_code=404, detail="Piso no encontrado")

    return piso


# ---- GET /torres/{id_torre}/pisos ----
@router.get("/{id_torre}/pisos", response_model=list[schemas.PisoOut])
def listar_pisos_por_torre(id_torre: int, db: Session = Depends(get_db)):
    pisos = (
        db.query(models.Piso)
        .options(joinedload(models.Piso.apartamentos))
        .filter(models.Piso.id_torre == id_torre)
        .all()
    )
    if not pisos:
        raise HTTPException(status_code=404, detail="No se encontraron pisos")

    return pisos


# ---- GET /torres/{id_torre}/pisos/{id_piso} ----
@router.get("/{id_torre}/pisos/{id_piso}", response_model=schemas.PisoOut)
def obtener_piso(id_torre: int, id_piso: int, db: Session = Depends(get_db)):
    piso = (
        db.query(models.Piso)
        .options(joinedload(models.Piso.apartamentos))
        .filter(models.Piso.id_torre == id_torre, models.Piso.id == id_piso)
        .first()
    )
    if not piso:
        raise HTTPException(status_code=404, detail="Piso no encontrado")

    return piso


# ---- GET /torres/{id_torre}/apartamentos ----
@router.get("/{id_torre}/apartamentos", response_model=list[schemas.ApartamentoOut])
def listar_apartamentos_por_torre(id_torre: int, db: Session = Depends(get_db)):
    apartamentos = (
        db.query(models.Apartamento)
        .join(models.Piso)
        .options(joinedload(models.Apartamento.piso))
        .filter(models.Piso.id_torre == id_torre)
        .all()
    )
    if not apartamentos:
        raise HTTPException(status_code=404, detail="No se encontraron apartamentos")

    return apartamentos


# ---- GET /torres/{id_torre}/pisos/{id_piso}/apartamentos ----
@router.get("/{id_torre}/pisos/{id_piso}/apartamentos", response_model=list[schemas.ApartamentoOut])
def listar_apartamentos_por_piso(id_torre: int, id_piso: int, db: Session = Depends(get_db)):
    apartamentos = db.query(models.Apartamento).filter(models.Apartamento.id_piso == id_piso).all()
    if not apartamentos:
        raise HTTPException(status_code=404, detail="No se encontraron apartamentos en este piso")

    return apartamentos


# ---- GET /torres/{id_torre}/pisos/{id_piso}/apartamentos/{id_apartamento} ----
@router.get("/{id_torre}/pisos/{id_piso}/apartamentos/{id_apartamento}", response_model=schemas.ApartamentoOut)
def obtener_apartamento(id_torre: int, id_piso: int, id_apartamento: int, db: Session = Depends(get_db)):
    apartamento = (
        db.query(models.Apartamento)
        .join(models.Piso)
        .filter(
            models.Apartamento.id == id_apartamento,
            models.Apartamento.id_piso == id_piso,
            models.Piso.id_torre == id_torre,
        )
        .first()
    )
    if not apartamento:
        raise HTTPException(status_code=404, detail="Apartamento no encontrado")

    return apartamento
