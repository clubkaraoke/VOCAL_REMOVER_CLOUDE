import os, sys, subprocess, tempfile, requests
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("MVSEP_API_TOKEN")
if not TOKEN:
    raise ValueError("MVSEP_API_TOKEN required")

sys.path.insert(0, str(Path(__file__).parent))
from database import init_db, create_track, create_stem, get_all_tracks, get_track_with_stems

app = FastAPI(title="Audio DAW - MVSep")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE_DIR = Path(__file__).parent
for d in [BASE_DIR / "uploads", BASE_DIR / "output", BASE_DIR / "static", BASE_DIR / "templates"]:
    d.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/output", StaticFiles(directory=str(BASE_DIR / "output")), name="output")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

print("=" * 50)
print("✅ AUDIO DAW v2 - MVSEP INTEGRATION - NEW VERSION")
print("=" * 50)

@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Database initialized")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/sync-mvsep")
async def sync_mvsep():
    print("\n" + "="*50)
    print("🔄 STARTING MVSEP SYNC - NEW LOGIC")
    print("="*50 + "\n")
    
    try:
        # Get job hashes
        print("📡 Fetching MVSep job hashes...")
        r = requests.get("https://mvsep.com/api/app/separation_history",
                        params={"api_token": TOKEN}, timeout=30)
        r.raise_for_status()
        hashes = r.json()
        print(f"✅ Got {len(hashes)} job hashes: {hashes}")
        
        synced = 0
        for h in hashes:
            try:
                print(f"\n  Processing hash: {h[:20]}...")
                
                # Get job details
                jr = requests.get("https://mvsep.com/api/separation/get",
                                params={"hash": h}, timeout=15)
                jr.raise_for_status()
                jdata = jr.json()
                print(f"  Status: {jdata.get('status')}")
                
                if jdata.get("status") != "done":
                    print(f"  Skipping (not done)")
                    continue
                
                # Extract stems
                stems = []
                d = jdata.get("data", {})
                if isinstance(d, dict):
                    for f in d.get("files", []):
                        if isinstance(f, dict):
                            stems.append({
                                "name": f.get("name", "?"),
                                "url": f.get("link", ""),
                                "size": f.get("size", 0)
                            })
                
                print(f"  Found {len(stems)} stems")
                if not stems:
                    continue
                
                title = jdata.get("name", f"Job {h[:10]}")
                print(f"  Title: {title}")
                
                # Check duplicate
                if any(t['name'] == h for t in get_all_tracks()):
                    print(f"  Already imported, skipping")
                    continue
                
                # Import
                tid = create_track(name=h, bpm=0, duration=0,
                                  stem_count=len(stems),
                                  original_filename=title)
                
                for s in stems:
                    create_stem(track_id=tid, name=s["name"],
                               filename="", duration=0,
                               url=s["url"], file_size=s.get("size", 0))
                
                synced += 1
                print(f"  ✅ IMPORTED: {title}")
            
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)[:80]}")
        
        print(f"\n✅ SYNC COMPLETE: {synced} projects imported\n")
        return {"status": "ok", "synced": synced}
    
    except Exception as e:
        print(f"❌ SYNC FAILED: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def get_projects():
    try:
        return [{"id": p["id"], "title": p["original_filename"] or p["name"],
                "stem_count": p["stem_count"]} for p in get_all_tracks()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{pid}")
async def get_project(pid: int):
    try:
        p = get_track_with_stems(pid)
        if not p:
            raise HTTPException(status_code=404)
        return {"id": p["id"], "title": p["original_filename"] or p["name"],
                "stem_count": p["stem_count"],
                "stems": [{"id": s["id"], "name": s["name"], "url": s.get("url", "")}
                         for s in p["stems"]]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
