"""
Audio DAW - MVSep Integration
Backend FastAPI para cargar y editar proyectos de MVSep
"""

import os
import sys
import json
import asyncio
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
from dotenv import load_dotenv

# Load environment
load_dotenv()
MVSEP_API_TOKEN = os.getenv("MVSEP_API_TOKEN")
MVSEP_API_URL = "https://mvsep.com/api"

if not MVSEP_API_TOKEN:
    raise ValueError("❌ MVSEP_API_TOKEN no está seteado en .env")

# Import MVSep client
sys.path.insert(0, str(Path(__file__).parent))
from mvsep_client import get_separation_history, get_separation_status, format_job_for_db
from database import (
    init_db, create_track, create_stem, get_all_tracks,
    get_track_with_stems, save_silent_regions, get_silent_regions
)

# FastAPI app
app = FastAPI(
    title="Audio DAW - MVSep",
    description="Web DAW para editar proyectos de MVSep"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

print("✅ Audio DAW - MVSep Integration")
print(f"📡 MVSep Token: {MVSEP_API_TOKEN[:20]}...")
print(f"🌐 API URL: {MVSEP_API_URL}")


@app.on_event("startup")
async def startup():
    """Initialize database"""
    print("🚀 Inicializando base de datos...")
    init_db()
    print("✅ Base de datos lista")


# ============================================================
# FRONTEND
# ============================================================

@app.get("/")
async def index(request: Request):
    """Render main page"""
    return templates.TemplateResponse("index.html", {"request": request})


# ============================================================
# MVSep Integration API
# ============================================================

@app.post("/api/sync-mvsep")
async def sync_mvsep_history():
    """
    Sincronizar histórico de MVSep con DB
    Trae todos los jobs completados
    """
    print("🔄 Sincronizando con MVSep...")
    
    try:
        history_list = get_separation_history()
        
        if not history_list:
            return {
                "status": "error",
                "message": "No se pudo obtener histórico de MVSep",
                "synced": 0
            }
        
        synced = 0
        errors = 0
        
        # Si history_list contiene diccionarios completos, usarlos directamente
        # Si contiene strings (hashes), obtener detalles de cada uno
        for item in history_list:
            try:
                # Determinar si es un diccionario o string
                if isinstance(item, str):
                    # Es un hash, obtener detalles completos
                    print(f"  📡 Obteniendo detalles de {item[:30]}...")
                    job = get_separation_status(item)
                    if not job or job.get('status') != 'done':
                        continue
                else:
                    # Ya es un diccionario con detalles
                    job = item
                    if job.get('status') != 'done':
                        continue
                
                # Formatear para DB
                formatted_job = format_job_for_db(job)
                if not formatted_job or not formatted_job.get('stems'):
                    continue
                
                # Evitar duplicados
                existing_tracks = get_all_tracks()
                if any(t['name'] == formatted_job['mvsep_hash'] for t in existing_tracks):
                    print(f"  ⏭️  Saltando (ya existe): {formatted_job['title']}")
                    continue
                
                # Crear track
                track_id = create_track(
                    name=formatted_job['mvsep_hash'],
                    bpm=0,
                    duration=0,
                    stem_count=len(formatted_job['stems']),
                    original_filename=formatted_job['title']
                )
                
                # Crear stems con URLs de MVSep
                for stem in formatted_job['stems']:
                    create_stem(
                        track_id=track_id,
                        name=stem['name'],
                        filename='',
                        duration=0,
                        url=stem['url'],
                        file_size=stem.get('size', 0)
                    )
                
                synced += 1
                print(f"  ✅ Importado: {formatted_job['title']}")
            
            except Exception as e:
                errors += 1
                print(f"  ❌ Error procesando job: {e}")
        
        return {
            "status": "synced",
            "total_found": len(history_list),
            "new_projects": synced,
            "errors": errors,
            "message": f"{synced} nuevos proyectos sincronizados desde MVSep"
        }
    
    except Exception as e:
        print(f"❌ Error en sync-mvsep: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects")
async def get_projects():
    """
    GET lista de proyectos
    """
    try:
        projects = get_all_tracks()
        
        return [
            {
                "id": p['id'],
                "title": p['original_filename'] or p['name'],
                "name": p['name'],
                "duration": p['duration'],
                "stem_count": p['stem_count'],
                "created_at": p['created_at']
            }
            for p in projects
        ]
    
    except Exception as e:
        print(f"❌ Error obteniendo proyectos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    """
    GET proyecto específico con stems URLs
    """
    try:
        project = get_track_with_stems(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "id": project['id'],
            "title": project['original_filename'] or project['name'],
            "name": project['name'],
            "duration": project['duration'],
            "stem_count": project['stem_count'],
            "stems": [
                {
                    "id": s['id'],
                    "name": s['name'],
                    "url": s.get('url', '')
                }
                for s in project['stems']
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo proyecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/silent-regions")
async def save_silent_regions_endpoint(project_id: int, silent_regions: Dict):
    """
    POST guardar silencios
    Formato: {0: [[0, 1000], [5000, 6000]], 1: [], ...}
    """
    try:
        # Verificar que existe
        project = get_track_with_stems(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Guardar
        save_silent_regions(project_id, silent_regions)
        
        return {"status": "saved", "message": "Silent regions saved"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error guardando silencios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/export")
async def export_mix(project_id: int, format: str = "mp3"):
    """
    POST exportar mezcla con silencios aplicados
    """
    try:
        print(f"🎵 Exportando mezcla del proyecto {project_id}...")
        
        # Obtener datos
        project = get_track_with_stems(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        stems = project['stems']
        if not stems:
            raise HTTPException(status_code=400, detail="No stems available")
        
        # Crear directorio temporal
        temp_dir = Path(tempfile.mkdtemp())
        print(f"📁 Directorio temporal: {temp_dir}")
        
        # Descargar stems
        import requests
        stem_files = {}
        
        for stem in stems:
            try:
                print(f"  📥 Descargando {stem['name']}...")
                response = requests.get(stem['url'], timeout=60)
                response.raise_for_status()
                
                stem_file = temp_dir / f"{stem['name']}.wav"
                stem_file.write_bytes(response.content)
                stem_files[stem['name']] = str(stem_file)
                
                print(f"    ✅ Descargado: {len(response.content) / 1024 / 1024:.1f} MB")
            
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        if not stem_files:
            raise HTTPException(status_code=400, detail="No stems downloaded")
        
        # Output file
        output_file = OUTPUT_DIR / f"{project['name']}_mix.{format}"
        output_file.parent.mkdir(exist_ok=True)
        
        # FFmpeg - Simple mix sin silencios (por ahora)
        ffmpeg_cmd = ['ffmpeg', '-y']
        
        for stem_path in stem_files.values():
            ffmpeg_cmd.extend(['-i', stem_path])
        
        # Filter: amix
        num_stems = len(stem_files)
        filter_complex = f"amix=inputs={num_stems}:duration=longest"
        
        ffmpeg_cmd.extend([
            '-filter_complex', filter_complex,
            '-c:a', 'aac',
            str(output_file)
        ])
        
        print(f"🎵 Ejecutando FFmpeg...")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            raise Exception("FFmpeg export failed")
        
        # Limpiar temporal
        import shutil
        shutil.rmtree(temp_dir)
        
        print(f"✅ Export completado: {output_file.name}")
        
        return {
            "status": "success",
            "filename": output_file.name,
            "download_url": f"/output/{output_file.name}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error durante export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "mvsep_token": "configured" if MVSEP_API_TOKEN else "missing"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
