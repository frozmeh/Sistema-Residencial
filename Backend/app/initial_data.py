from sqlalchemy.orm import Session
from decimal import Decimal
from .models import Torre, Piso, TipoApartamento, Apartamento


def inicializar_db(db: Session, limpiar: bool = False):
    # ---- (Opcional) limpiar datos previos ----
    if limpiar:
        db.query(Apartamento).delete()
        db.query(Piso).delete()
        db.query(Torre).delete()
        db.query(TipoApartamento).delete()
        db.commit()

    # ---- Evitar reinserciones ----
    if db.query(Torre).count() > 0:
        print("La base de datos ya fue inicializada previamente. ❌")
        return

    # ---- Tipos de apartamentos ----
    tipos = [
        {"nombre": "1 hab/1 baño", "habitaciones": 1, "banos": 1, "porcentaje_aporte": Decimal("0.27")},
        {"nombre": "2 hab/2 baños", "habitaciones": 2, "banos": 2, "porcentaje_aporte": Decimal("0.45")},
        {"nombre": "3 hab/2 baños", "habitaciones": 3, "banos": 2, "porcentaje_aporte": Decimal("0.60")},
    ]

    tipo_objetos = {}
    for t in tipos:
        tipo = TipoApartamento(**t)
        db.add(tipo)
        db.flush()
        tipo_objetos[t["habitaciones"]] = tipo.id

    # ---- Torres ----
    torres = ["Santa Fe", "Mochima", "Tigrillo"]
    torre_objetos = {}
    for nombre in torres:
        torre = Torre(nombre=nombre)
        db.add(torre)
        db.flush()
        torre_objetos[nombre] = torre.id

    # ---- Pisos y Apartamentos ----
    for torre_nombre, torre_id in torre_objetos.items():
        for piso_num in range(0, 14):  # Planta baja=0 hasta piso 13
            piso = Piso(numero=piso_num, id_torre=torre_id)
            db.add(piso)
            db.flush()

            # Definir apartamentos según piso
            if piso_num == 0:
                apt_list = [{"numero": f"{piso_num}-{i+1}", "habitaciones": 3} for i in range(2)]
            elif 1 <= piso_num <= 6 or 10 <= piso_num <= 12:
                secuencia = [2, 1, 2, 2, 1, 2]
                apt_list = [{"numero": f"{piso_num}-{i+1}", "habitaciones": h} for i, h in enumerate(secuencia)]
            elif 7 <= piso_num <= 9:
                apt_list = [{"numero": f"{piso_num}-{i+1}", "habitaciones": 3} for i in range(4)]
            elif piso_num == 13:
                apt_list = [{"numero": f"{piso_num}-{i+1}", "habitaciones": 2} for i in range(4)]
            else:
                apt_list = []

            for apt in apt_list:
                a = Apartamento(
                    numero=apt["numero"],
                    id_piso=piso.id,
                    id_tipo_apartamento=tipo_objetos[apt["habitaciones"]],
                    estado="Disponible",
                )
                db.add(a)

    db.commit()

    print(
        f"Inicialización completa ✅ ({len(torres)} torres, {db.query(Piso).count()} pisos, {db.query(Apartamento).count()} apartamentos)"
    )
