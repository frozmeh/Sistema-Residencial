from sqlalchemy.orm import Session


# Función para reducir líneas de código al hacer commit y refresh en la DB
def guardar_y_refrescar(db: Session, obj):
    db.commit()
    db.refresh(obj)
