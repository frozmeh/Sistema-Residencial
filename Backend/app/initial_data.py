from sqlalchemy.orm import Session
from decimal import Decimal
from .models import Torre, Piso, TipoApartamento, Apartamento, Rol
from . import models  # Para los roles si los necesitas


def inicializar_db(db: Session, limpiar: bool = False):

    if limpiar:
        db.query(Apartamento).delete()
        db.query(Piso).delete()
        db.query(Torre).delete()
        db.query(TipoApartamento).delete()
        db.query(Rol).delete()
        db.commit()

    initialized = False

    # ---- 1. ROLES ----
    if db.query(Rol).count() == 0:
        print("👥 Inicializando roles...")
        roles = [
            Rol(nombre="Administrador", descripcion="Acceso completo al sistema"),
            Rol(nombre="Residente", descripcion="Acceso limitado a funcionalidades de residente"),
        ]
        db.add_all(roles)
        db.flush()  # Usar flush en lugar de commit para mantener la transacción
        print(f"✅ Roles creados: {[r.nombre for r in roles]}")
        initialized = True

    # ---- 2. ESTRUCTURA DEL CONDOMINIO ----
    if db.query(Torre).count() == 0:
        print("🏢 Inicializando estructura del condominio...")

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
        total_apartamentos = 0
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
                    total_apartamentos += 1

        initialized = True
        print(
            f"Estructura creada: {len(torres)} torres, {db.query(Piso).count()} pisos, {total_apartamentos} apartamentos"
        )

    if initialized:
        db.commit()
        print("Base de datos inicializada completamente")

    return {
        "roles": db.query(Rol).count(),
        "torres": db.query(Torre).count(),
        "pisos": db.query(Piso).count(),
        "apartamentos": db.query(Apartamento).count(),
        "tipos_apartamento": db.query(TipoApartamento).count(),
    }
