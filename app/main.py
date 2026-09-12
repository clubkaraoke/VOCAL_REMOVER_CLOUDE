import os
import sys
import subprocess
import tempfile
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from dotenv import load_dotenv

# Load env
load_dotenv()
MVSEP_TOKEN = os.getenv("MVSEP_API_TOKEN")
MVSEP_URL = "https://mvsep.com/api"

if not MVSEP_TOKEN:
    raise ValueError("MVSEP_API_TOKEN missing")

# Import DB
sys.path.insert(0, str(Path(__file__).parent))
from database import init_db, create_track, create_stem, get_all_tracks, get_track_with_stems

# FastAPI setup
app = FastAPI(title="Audio DAW - MVSep")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE_DIR = Path(__file__).parent
for d in [BASE_DIR / "uploads", BASE_DIR / "output", BASE_DIR / "static", BASE_DIR / "templates"]:
    d.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/output", StaticFiles(directory=str(BASE_DIR / "output")), name="output")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

print(f"✅ Audio DAW - MVSep Integration")
print(f"📡 Token: {MVSEP_TOKEN[:15]}...")

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ============================================================
# MVSEP SYNC
# ============================================================

@app.post("/api/sync-mvsep")
async def sync_mvsep():
    """Sync MVSep projects to database"""
    print("🔄 Starting MVSep sync...")
    
    try:
        # Step 1: Get job hashes from MVSep
        print("📡 Fetching MVSep history...")
        resp = requests.get(
            f"{MVSEP_URL}/app/separation_history",
            params={"api_token": MVSEP_TOKEN},
            timeout=30
        )
        resp.raise_for_status()
        job_hashes = resp.json()
        print(f"✅ Found {len(job_hashes)} jobs")
        
        if not job_hashes:
            return {"status": "ok", "synced": 0, "message": "No jobs found"}
        
        synced = 0
        errors = 0
        
        # Step 2: Process each job hash
        for job_hash in job_hashes:
            try:
                # Ensure we have a string
                if not isinstance(job_hash, str):
                    print(f"  ⏭️  Skipping non-string: {type(job_hash)}")
                    continue
                
                print(f"  📥 Processing: {job_hash[:25]}...")
                
                # Step 3: Get full job details
                job_resp = requests.get(
                    f"{MVSEP_URL}/separation/get",
                    params={"hash": job_hash},
                    timeout=15
                )
                job_resp.raise_for_status()
                job_data = job_resp.json()
                
                # Check status
                if job_data.get("status") != "done":
                    print(f"    ⏭️  Not done: {job_data.get('status')}")
                    continue
                
                # Extract stems
                stems = []
                if job_data.get("data") and isinstance(job_data["data"], dict):
                    files = job_data["data"].get("files", [])
                    if isinstance(files, list):
                        for f in files:
                            if isinstance(f, dict):
                                stems.append({
                                    "name": f.get("name", "Unknown"),
                                    "url": f.get("link", ""),
                                    "size": f.get("size", 0)
                                })
                
                if not stems:
                    print(f"    ⏭️  No stems")
                    continue
                
                # Get title
                title = job_data.get("name", f"Job {job_hash[:10]}")
                
                # Check for duplicates
                existing = get_all_tracks()
                if any(t['name'] == job_hash for t in existing):
                    print(f"    ⏭️  Already imported: {title}")
                    continue
                
                # Create track
                track_id = create_track(
                    name=job_hash,
                    bpm=0,
                    duration=0,
                    stem_count=len(stems),
                    original_filename=title
                )
                
                # Create stems
                for stem in stems:
                    create_stem(
                        track_id=track_id,
                        name=stem["name"],
                        filename="",
                        duration=0,
                        url=stem["url"],
                        file_size=stem.get("size", 0)
                    )
                
                synced += 1
                print(f"    ✅ Imported: {title}")
            
            except Exception as e:
                errors += 1
                print(f"    ❌ Error: {str(e)[:100]}")
        
        return {
            "status": "synced",
            "synced": synced,
            "errors": errors,
            "message": f"{synced} projects imported"
        }
    
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PROJECTS API
# ============================================================

@app.get("/api/projects")
async def get_projects():
    """List all projects"""
    try:
        projects = get_all_tracks()
        return [
            {
                "id": p["id"],
                "title": p["original_filename"] or p["name"],
                "stem_count": p["stem_count"],
                "created_at": p["created_at"]
            }
            for p in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    """Get project with stems"""
    try:
        project = get_track_with_stems(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Not found")
        
        return {
            "id": project["id"],
            "title": project["original_filename"] or project["name"],
            "stem_count": project["stem_count"],
            "stems": [
                {"id": s["id"], "name": s["name"], "url": s.get("url", "")}
                for s in project["stems"]
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
