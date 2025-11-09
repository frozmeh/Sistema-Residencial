import os


def contar_lineas_en_archivo(ruta_archivo):
    """Cuenta las líneas de un solo archivo."""
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except Exception as e:
        print(f"Error al leer {ruta_archivo}: {e}")
        return 0


def contar_lineas_en_directorio(ruta_directorio):
    """Cuenta las líneas de código en todos los archivos .py de un directorio y sus subdirectorios."""
    total_lineas = 0
    for directorio_actual, _, nombres_archivos in os.walk(ruta_directorio):
        for nombre_archivo in nombres_archivos:
            if nombre_archivo.endswith(".py"):
                ruta_completa = os.path.join(directorio_actual, nombre_archivo)
                total_lineas += contar_lineas_en_archivo(ruta_completa)
    return total_lineas


# Ejemplo de uso:
# Reemplaza 'ruta/a/tu/proyecto' con la ruta de tu carpeta
ruta_proyecto = "C:/Proyecto/Backend/"
if os.path.exists(ruta_proyecto):
    lineas = contar_lineas_en_directorio(ruta_proyecto)
    print(f"El total de líneas de código es: {lineas}")
else:
    print("La ruta especificada no existe.")
