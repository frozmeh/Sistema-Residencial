from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from ...core.security import verificar_admin

router = APIRouter(prefix="/auditorias", tags=["Auditorias"])


@router.get("/", response_model=list[schemas.AuditoriaOut], dependencies=[Depends(verificar_admin)])
def listar_auditorias(db: Session = Depends(get_db)):
    return crud.obtener_auditorias(db)


@router.get("/{id_auditoria}", response_model=schemas.AuditoriaOut, dependencies=[Depends(verificar_admin)])
def obtener_auditoria(id_auditoria: int, db: Session = Depends(get_db)):
    a = crud.obtener_auditoria_por_id(db, id_auditoria)
    if not a:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return a
