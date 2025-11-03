import json
from sistema_biometrico import ConfiguracionGlobal


def generar_reporte():
    try:
        with open(ConfiguracionGlobal.FICHERO_BLOQUECHAIN, 'r') as f:
            blockchain = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {ConfiguracionGlobal.FICHERO_BLOQUECHAIN}")
        return
    except json.JSONDecodeError:
        print("Error: El archivo blockchain.json tiene formato JSON inválido")
        return
    
    if not blockchain:
        print("Error: La cadena de bloques está vacía")
        return
    
    # Calcular estadísticas
    total_bloques = len(blockchain)
    bloques_con_alerta = sum(1 for bloque in blockchain if bloque.get("alerta", False))
    
    # Calcular promedios generales
    suma_frecuencia = sum(bloque["datos"]["frecuencia"]["media"] for bloque in blockchain)
    suma_presion = sum(bloque["datos"]["presion"]["media"] for bloque in blockchain)
    suma_oxigeno = sum(bloque["datos"]["oxigeno"]["media"] for bloque in blockchain)
    
    promedio_frecuencia = suma_frecuencia / total_bloques if total_bloques > 0 else 0
    promedio_presion = suma_presion / total_bloques if total_bloques > 0 else 0
    promedio_oxigeno = suma_oxigeno / total_bloques if total_bloques > 0 else 0
    
    # Generar reporte
    reporte = f"""REPORTE FINAL DEL ANALISIS BIOMETRICO
==================================================

CANTIDAD TOTAL DE BLOQUES: {total_bloques}

BLOQUES CON ALERTAS: {bloques_con_alerta} ({bloques_con_alerta/total_bloques*100:.2f}% del total)

PROMEDIO GENERAL:
  Frecuencia cardiaca: {promedio_frecuencia:.2f} BPM
  Presion arterial: {promedio_presion:.2f} mmHg
  Saturacion de oxigeno: {promedio_oxigeno:.2f}%

"""
    
    # Guardar reporte en archivo
    with open(ConfiguracionGlobal.FICHERO_REPORTE, 'w') as f:
        f.write(reporte)
    
    # Mostrar reporte en pantalla
    print(reporte)
    print(f"Reporte guardado en: {ConfiguracionGlobal.FICHERO_REPORTE}")


if __name__ == "__main__":
    generar_reporte()

