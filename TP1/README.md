# Sistema Concurrente de Análisis Biométrico con Cadena de Bloques Local

## Descripción

Este sistema simula un análisis biométrico concurrente de una prueba de esfuerzo utilizando multiprocessing en Python. El sistema genera datos biométricos en tiempo real (frecuencia cardíaca, presión arterial y saturación de oxígeno), los procesa en paralelo mediante procesos independientes, y almacena los resultados en una cadena de bloques local para garantizar la integridad de los datos.

## Requisitos

- Python ≥ 3.9
- Dependencias: `numpy` 

## Estructura de Archivos

- `sistema_biometrico.py`: Sistema principal con todos los procesos concurrentes
- `verificar_cadena.py`: Script de verificación de integridad de la cadena de bloques
- `generar_reporte.py`: Script de generación del reporte final
- `blockchain.json`: Archivo generado con la cadena de bloques
- `reporte.txt`: Archivo generado con el reporte estadístico

## Instrucciones de Ejecución

### Paso 1: Ejecutar el sistema principal

python sistema_biometrico.py

Este comando:
- Generará 60 muestras de datos biométricos 
- Procesará los datos en paralelo en 3 analizadores
- Construirá la cadena de bloques y la guardará en `blockchain.json`
- Mostrará el progreso por pantalla

### Paso 2: Verificar la integridad de la cadena

python verificar_cadena.py

Este script verifica:
- Que todos los bloques estén correctamente encadenados
- Que los hashes SHA-256 sean correctos
- Que no haya corrupción en los datos

### Paso 3: Generar el reporte final

python generar_reporte.py

Este script genera un reporte con:
- Cantidad total de bloques
- Número de bloques con alertas
- Promedios generales de frecuencia, presión y oxígeno

## Ejecución Completa

python sistema_biometrico.py && python verificar_cadena.py && python generar_reporte.py



