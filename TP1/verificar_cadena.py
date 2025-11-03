import json
import hashlib
from sistema_biometrico import ConfiguracionGlobal


def verificar_cadena():
    try:
        with open(ConfiguracionGlobal.FICHERO_BLOQUECHAIN, 'r') as f:
            blockchain = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {ConfiguracionGlobal.FICHERO_BLOQUECHAIN}")
        return False
    except json.JSONDecodeError:
        print("Error: El archivo blockchain.json tiene formato inválido")
        return False
    
    if not blockchain:
        print("Error: La cadena de bloques está vacía")
        return False
    
    print("Verificando la cadena de bloques...\n")
    
    prev_hash = "0" * 64 
    bloques_validos = 0
    bloques_invalidos = 0
    
    for i, bloque in enumerate(blockchain, 1):
        if bloque["prev_hash"] != prev_hash:
            print(f"❌ Bloque {i}: El hash anterior no coincide")
            print(f"   Esperado: {prev_hash}")
            print(f"   Obt fruto: {bloque['prev_hash']}")
            bloques_invalidos += 1
            break
        
        datos_bloque = bloque["datos"]
        timestamp = bloque["timestamp"]
        hash_string = f"{prev_hash}{json.dumps(datos_bloque, sort_keys=True)}{timestamp}"
        hash_calculado = hashlib.sha256(hash_string.encode()).hexdigest()
        
        if bloque["hash"] != hash_calculado:
            print(f"❌ Bloque {i}: El hash del bloque es incorrecto")
            print(f"   Esperado: {hash_calculado[:16]}...")
            print(f"   Obtenido: {bloque['hash'][:16]}...")
            bloques_invalidos += 1
            break
        
        bloques_validos += 1
        prev_hash = bloque["hash"]
    
    total_bloques = len(blockchain)
    print(f"\n{'='*60}")
    print(f"Resultado de la verificación:")
    print(f"  Total de bloques: {total_bloques}")
    print(f"  Bloques válidos: {bloques_validos}")
    print(f"  Bloques inválidos: {bloques_invalidos}")
    
    if bloques_invalidos == 0:
        print(f"\n✅ La cadena de bloques es íntegra")
        return True
    else:
        print(f"\n❌ La cadena de bloques tiene errores")
        return False


if __name__ == "__main__":
    verificar_cadena()

