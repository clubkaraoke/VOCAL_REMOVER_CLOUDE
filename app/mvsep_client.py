"""
MVSep API Client - Wrapper para integración con spleeter-web
Simplifica llamadas a MVSep API para traer histórico y metadatos
"""

import requests
import os
import time
from typing import Dict, List, Optional
from datetime import datetime

# Config
MVSEP_API_TOKEN = os.getenv("MVSEP_API_TOKEN")
MVSEP_API_URL = "https://mvsep.com/api"

if not MVSEP_API_TOKEN:
    raise ValueError("❌ MVSEP_API_TOKEN no está seteado en .env")

print(f"✅ MVSep client inicializado con token: {MVSEP_API_TOKEN[:20]}...")


def get_separation_history() -> List[Dict]:
    """
    GET https://mvsep.com/api/app/separation_history
    
    Trae TODO el histórico de separaciones completadas en tu cuenta MVSep
    
    Returns:
        [
            {
                "hash": "20240115120530-8f7a2c1d-13-Soy_Cubano.mp3",
                "name": "Soy_Cubano.mp3",
                "status": "done",
                "files": [
                    {"name": "Vocals", "link": "https://..."},
                    {"name": "Drums", "link": "https://..."},
                    ...
                ],
                "credits_used": 3.5
            },
            ...
        ]
    """
    try:
        print("📡 Obteniendo histórico de MVSep...")
        response = requests.get(
            f"{MVSEP_API_URL}/app/separation_history",
            params={"api_token": MVSEP_API_TOKEN},
            timeout=30
        )
        response.raise_for_status()
        jobs = response.json()
        print(f"✅ Histórico obtenido: {len(jobs)} trabajos encontrados")
        return jobs
    
    except requests.exceptions.Timeout:
        print("❌ Timeout: MVSep no responde")
        return []
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: Verifica tu internet")
        return []
    except Exception as e:
        print(f"❌ Error obteniendo histórico MVSep: {e}")
        return []


def get_separation_status(job_hash: str, max_polls: int = 120) -> Dict:
    """
    GET https://mvsep.com/api/separation/get?hash=HASH
    
    Obtiene el status de un job específico
    Si está en "waiting" o "processing", espera y reintenta
    
    Args:
        job_hash: Hash del job en MVSep (ej: "20240115120530-8f7a2c1d")
        max_polls: Máximo de reintentos (cada 5 segundos = 10 minutos)
    
    Returns:
        {
            "status": "done",
            "data": {
                "files": [
                    {"name": "Vocals", "link": "https://..."},
                    ...
                ]
            }
        }
    """
    try:
        print(f"🔍 Chequeando status del job {job_hash}...")
        polls = 0
        
        while polls < max_polls:
            response = requests.get(
                f"{MVSEP_API_URL}/separation/get",
                params={"hash": job_hash},
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status")
            print(f"  Status: {status}")
            
            if status == "done":
                print(f"✅ Job completado")
                return result
            
            elif status in ["waiting", "processing"]:
                print(f"  ⏳ Esperando 5 segundos... (intento {polls + 1}/{max_polls})")
                time.sleep(5)
                polls += 1
            
            else:
                print(f"❌ Status inesperado: {status}")
                return {"status": "error", "message": f"Unknown status: {status}"}
        
        print(f"❌ Timeout: Job no completó en {max_polls * 5}s")
        return {"status": "timeout", "message": "Polling timeout"}
    
    except Exception as e:
        print(f"❌ Error obteniendo status: {e}")
        return {"status": "error", "message": str(e)}


def parse_stem_url(url: str) -> Dict:
    """
    Extrae información útil de una URL de stem de MVSep
    
    Args:
        url: "https://mvsep-results.s3.amazonaws.com/20240115120530-xxx-00_Vocals.wav"
    
    Returns:
        {
            "stem_name": "Vocals",
            "stem_index": "00",
            "file_extension": "wav",
            "bucket": "mvsep-results",
            "region": "s3.amazonaws.com"
        }
    """
    try:
        path = url.split("/")[-1]  # "20240115120530-xxx-00_Vocals.wav"
        
        # Extraer nombre: "00_Vocals" -> "Vocals"
        parts = path.split("-")[-1]  # "00_Vocals.wav"
        stem_parts = parts.split("_")
        stem_index = stem_parts[0]  # "00"
        stem_name = "_".join(stem_parts[1:]).split(".")[0]  # "Vocals"
        extension = path.split(".")[-1]  # "wav"
        
        return {
            "stem_name": stem_name,
            "stem_index": stem_index,
            "file_extension": extension,
            "url": url
        }
    
    except:
        return {"stem_name": "Unknown", "url": url}


def format_job_for_db(job: Dict) -> Dict:
    """
    Convierte respuesta de MVSep a formato para guardar en DB
    
    Args:
        job: Respuesta de MVSep (de get_separation_history)
    
    Returns:
        {
            "mvsep_hash": "20240115120530",
            "title": "Soy_Cubano.mp3",
            "status": "done",
            "stem_type": "6-stems",
            "stems": [
                {"name": "Vocals", "url": "https://..."},
                {"name": "Drums", "url": "https://..."},
                ...
            ],
            "created_at": "2024-01-15T12:05:30",
            "synced_at": "2024-01-15T13:05:30"
        }
    """
    try:
        job_hash = job.get("hash", "").split("-")[0]
        
        stems = []
        if "files" in job:
            for file_info in job["files"]:
                parsed = parse_stem_url(file_info.get("link", ""))
                stems.append({
                    "name": file_info.get("name", "Unknown"),
                    "url": file_info.get("link", ""),
                    "size": file_info.get("size", 0)
                })
        
        return {
            "mvsep_hash": job_hash,
            "title": job.get("name", f"Job {job_hash}"),
            "status": job.get("status", "done"),
            "stem_type": f"{len(stems)}-stems",
            "source_file_url": "",  # MVSep no devuelve el archivo original
            "stems": stems,
            "credits_used": job.get("credits_used", 0),
            "created_at": datetime.now().isoformat(),
            "synced_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"❌ Error formateando job: {e}")
        return {}


def validate_token() -> bool:
    """
    Valida que el token de MVSep sea correcto
    
    Returns:
        True si es válido, False si no
    """
    try:
        print("🔐 Validando token de MVSep...")
        response = requests.get(
            f"{MVSEP_API_URL}/app/user",
            params={"api_token": MVSEP_API_TOKEN},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Token válido")
            return True
        else:
            print(f"❌ Token inválido: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error validando token: {e}")
        return False


# Ejemplos de uso
if __name__ == "__main__":
    print("\n=== MVSep Client Demo ===\n")
    
    # 1. Validar token
    if not validate_token():
        print("❌ Por favor, verifica tu MVSEP_API_TOKEN en .env")
        exit(1)
    
    # 2. Obtener histórico
    print("\n📚 Obteniendo histórico...")
    history = get_separation_history()
    
    if history:
        print(f"\n✅ Encontrados {len(history)} trabajos:\n")
        for i, job in enumerate(history[:3], 1):  # Primeros 3
            print(f"{i}. {job.get('name')}")
            print(f"   Hash: {job.get('hash')[:30]}...")
            print(f"   Status: {job.get('status')}")
            print(f"   Stems: {len(job.get('files', []))}")
            print()
    else:
        print("❌ No hay trabajos en el histórico")
    
    # 3. Formatear para DB
    if history:
        first_job = history[0]
        formatted = format_job_for_db(first_job)
        print("📝 Formato para DB:")
        print(f"  Hash: {formatted['mvsep_hash']}")
        print(f"  Título: {formatted['title']}")
        print(f"  Stems: {len(formatted['stems'])}")
