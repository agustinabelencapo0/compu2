import multiprocessing as mp
import json
import hashlib
import time
import random
from datetime import datetime
from collections import deque
import numpy as np


class ConfiguracionGlobal:
    #Configuración global del sistema
    TOTAL_MUESTRAS = 60
    VENTANA_MOVIL = 30
    FICHERO_BLOQUECHAIN = "blockchain.json"
    FICHERO_REPORTE = "reporte.txt"


def calcular_desviacion_estandar(valores):
    if len(valores) < 2:
        return 0.0
    return np.std(valores)


def generar_datos_biometricos():

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "frecuencia": random.randint(60, 180),
        "presion": [random.randint(110, 180), random.randint(70, 110)],
        "oxigeno": random.randint(90, 100)
    }


def proceso_analizador_frecuencia(conn, resultado_queue):
    ventana = deque(maxlen=ConfiguracionGlobal.VENTANA_MOVIL)
    
    try:
        for _ in range(ConfiguracionGlobal.TOTAL_MUESTRAS):
            # Recibir datos del proceso principal
            datos = conn.recv()
            frecuencia = datos["frecuencia"]
            
            # Actualizar ventana móvil
            ventana.append(frecuencia)
            
            # Calcular media y desviación estándar
            media = np.mean(list(ventana))
            desv = calcular_desviacion_estandar(list(ventana))
            
            # Enviar resultado al verificador
            resultado = {
                "tipo": "frecuencia",
                "timestamp": datos["timestamp"],
                "media": float(media),
                "desv": float(desv)
            }
            resultado_queue.put(resultado)
            
    except EOFError:
        pass
    finally:
        conn.close()


def proceso_analizador_presion(conn, resultado_queue):
    ventana = deque(maxlen=ConfiguracionGlobal.VENTANA_MOVIL)
    
    try:
        for _ in range(ConfiguracionGlobal.TOTAL_MUESTRAS):
            datos = conn.recv()
            presion_sistolica = datos["presion"][0]
            
            ventana.append(presion_sistolica)
            
            media = np.mean(list(ventana))
            desv = calcular_desviacion_estandar(list(ventana))
            
            resultado = {
                "tipo": "presion",
                "timestamp": datos["timestamp"],
                "media": float(media),
                "desv": float(desv)
            }
            resultado_queue.put(resultado)
            
    except EOFError:
        pass
    finally:
        conn.close()


def proceso_analizador_oxigeno(conn, resultado_queue):
    ventana = deque(maxlen=ConfiguracionGlobal.VENTANA_MOVIL)
    
    try:
        for _ in range(ConfiguracionGlobal.TOTAL_MUESTRAS):
            datos = conn.recv()
            oxigeno = datos["oxigeno"]
            
            ventana.append(oxigeno)
            
            media = np.mean(list(ventana))
            desv = calcular_desviacion_estandar(list(ventana))
            
            resultado = {
                "tipo": "oxigeno",
                "timestamp": datos["timestamp"],
                "media": float(media),
                "desv": float(desv)
            }
            resultado_queue.put(resultado)
            
    except EOFError:
        pass
    finally:
        conn.close()


def proceso_verificador(resultado_queue, lock):
    blockchain = []
    bloque_anterior_hash = "0" * 64  # Hash inicial
    
    # Diccionario para agrupar resultados por timestamp
    resultados_timestamp = {}
    
    try:
        for _ in range(ConfiguracionGlobal.TOTAL_MUESTRAS):
            # Recibir los tres resultados del mismo timestamp
            resultados = {}
            for _ in range(3):
                resultado = resultado_queue.get()
                resultados[resultado["tipo"]] = resultado
                
                # Guardar timestamp para validar que todos coinciden
                ts = resultado["timestamp"]
                if ts not in resultados_timestamp:
                    resultados_timestamp[ts] = {}
                resultados_timestamp[ts][resultado["tipo"]] = resultado
            
            # Obtener el timestamp del bloque actual
            timestamp = resultados["frecuencia"]["timestamp"]
            
            # Validar valores
            alerta = False
            if (resultados["frecuencia"]["media"] >= 200 or
                resultados["oxigeno"]["media"] < 90 or
                resultados["oxigeno"]["media"] > 100 or
                resultados["presion"]["media"] >= 200):
                alerta = True
            
            # Construir bloque
            datos_bloque = {
                "frecuencia": {
                    "media": resultados["frecuencia"]["media"],
                    "desv": resultados["frecuencia"]["desv"]
                },
                "presion": {
                    "media": resultados["presion"]["media"],
                    "desv": resultados["presion"]["desv"]
                },
                "oxigeno": {
                    "media": resultados["oxigeno"]["media"],
                    "desv": resultados["oxigeno"]["desv"]
                }
            }
            
            # Calcular hash
            hash_string = f"{bloque_anterior_hash}{json.dumps(datos_bloque, sort_keys=True)}{timestamp}"
            hash_bloque = hashlib.sha256(hash_string.encode()).hexdigest()
            
            bloque = {
                "timestamp": timestamp,
                "datos": datos_bloque,
                "alerta": alerta,
                "prev_hash": bloque_anterior_hash,
                "hash": hash_bloque
            }
            
            blockchain.append(bloque)
            bloque_anterior_hash = hash_bloque
            
            # Persistir al archivo
            with lock:
                with open(ConfiguracionGlobal.FICHERO_BLOQUECHAIN, 'w') as f:
                    json.dump(blockchain, f, indent=2)
            
            # Mostrar información del bloque
            alerta_str = " [ALERTA]" if alerta else ""
            print(f"Bloque {len(blockchain)} - Hash: {hash_bloque[:16]}...{alerta_str}")
            
    except Exception as e:
        print(f"Error en verificador: {e}")
    
    print("\nProceso verificador finalizado.")


def proceso_principal():
    # Crear pipes para comunicación con analizadores
    pipe_freq_padre, pipe_freq_hijo = mp.Pipe()
    pipe_pres_padre, pipe_pres_hijo = mp.Pipe()
    pipe_oxi_padre, pipe_oxi_hijo = mp.Pipe()
    
    # Crear cola compartida para resultados
    resultado_queue = mp.Queue()
    
    # Crear lock para sincronización
    lock = mp.Lock()
    
    # Inicializar blockchain vacío
    with open(ConfiguracionGlobal.FICHERO_BLOQUECHAIN, 'w') as f:
        json.dump([], f)
    
    # Crear procesos analizadores
    proc_freq = mp.Process(
        target=proceso_analizador_frecuencia,
        args=(pipe_freq_hijo, resultado_queue)
    )
    proc_pres = mp.Process(
        target=proceso_analizador_presion,
        args=(pipe_pres_hijo, resultado_queue)
    )
    proc_oxi = mp.Process(
        target=proceso_analizador_oxigeno,
        args=(pipe_oxi_hijo, resultado_queue)
    )
    
    # Crear proceso verificador
    proc_verif = mp.Process(
        target=proceso_verificador,
        args=(resultado_queue, lock)
    )
    
    # Iniciar todos los procesos
    proc_freq.start()
    proc_pres.start()
    proc_oxi.start()
    proc_verif.start()
    
    print("Sistema iniciado. Generando datos biométricos...\n")
    
    try:
        # Generar y enviar 60 muestras (1 por segundo)
        for i in range(ConfiguracionGlobal.TOTAL_MUESTRAS):
            datos = generar_datos_biometricos()
            
            # Enviar a los tres analizadores
            pipe_freq_padre.send(datos)
            pipe_pres_padre.send(datos)
            pipe_oxi_padre.send(datos)
            
            # Esperar 1 segundo antes de la siguiente muestra
            time.sleep(1)
            
    finally:
        # Cerrar conexiones padre
        pipe_freq_padre.close()
        pipe_pres_padre.close()
        pipe_oxi_padre.close()
        
        # Esperar a que terminen todos los procesos
        proc_freq.join(timeout=5)
        proc_pres.join(timeout=5)
        proc_oxi.join(timeout=5)
        proc_verif.join(timeout=10)
        
        # Terminar procesos si aún están activos
        for proc in [proc_freq, proc_pres, proc_oxi, proc_verif]:
            if proc.is_alive():
                proc.terminate()
                proc.join()
    
    print("\nProceso principal finalizado.")


if __name__ == "__main__":
    mp.set_start_method('spawn') 
    proceso_principal()

