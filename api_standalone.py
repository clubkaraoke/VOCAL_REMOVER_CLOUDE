#!/usr/bin/env python3
"""
PISTA IA - Audio DAW Standalone API
Simple API to sync MVSep and serve projects
Run: python api_standalone.py
"""

import os
import sys
import requests
import sqlite3
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env
load_dotenv()
MVSEP_TOKEN = os.getenv("MVSEP_API_TOKEN")
if not MVSEP_TOKEN:
    print("❌ ERROR: MVSEP_API_TOKEN not set in .env")
    print("Create .env file with: MVSEP_API_TOKEN=your_token_here")
    sys.exit(1)

# Setup
app = Flask(__name__)
CORS(app)
DB_PATH = Path("projects.db")

print("\n" + "="*60)
print("🎵 PISTA IA - Audio DAW API v1.0")
print("="*60)
print(f"📡 MVSep Token: {MVSEP_TOKEN[:15]}...")
print(f"📁 Database: {DB_PATH}")
print("="*60 + "\n")

# Database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            mvsep_hash TEXT UNIQUE,
            title TEXT,
            stem_count INTEGER,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS stems (
            id INTEGER PRIMARY KEY,
            project_id INTEGER,
            name TEXT,
            url TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Routes
@app.route('/api/sync-mvsep', methods=['POST'])
def sync_mvsep():
    print("\n🔄 SYNC START")
    try:
        # Get hashes
        r = requests.get("https://mvsep.com/api/app/separation_history",
                        params={"api_token": MVSEP_TOKEN}, timeout=30)
        r.raise_for_status()
        hashes = r.json()
        print(f"✅ Found {len(hashes)} jobs: {hashes[:2]}")
        
        synced = 0
        for h in hashes:
            try:
                # Get details
                jr = requests.get("https://mvsep.com/api/separation/get",
                                params={"hash": h}, timeout=15)
                jr.raise_for_status()
                jdata = jr.json()
                
                if jdata.get("status") != "done":
                    continue
                
                # Extract stems
                stems = []
                d = jdata.get("data", {})
                if isinstance(d, dict):
                    for f in d.get("files", []):
                        if isinstance(f, dict):
                            stems.append({
                                "name": f.get("name", "?"),
                                "url": f.get("link", "")
                            })
                
                if not stems:
                    continue
                
                title = jdata.get("name", f"Job {h[:10]}")
                
                # Save to DB
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO projects (mvsep_hash, title, stem_count, created_at) VALUES (?, ?, ?, ?)",
                             (h, title, len(stems), datetime.now().isoformat()))
                    pid = c.lastrowid
                    
                    for s in stems:
                        c.execute("INSERT INTO stems (project_id, name, url) VALUES (?, ?, ?)",
                                 (pid, s["name"], s["url"]))
                    
                    conn.commit()
                    synced += 1
                    print(f"  ✅ {title}")
                except sqlite3.IntegrityError:
                    print(f"  ⏭️  Already exists: {title}")
                finally:
                    conn.close()
            
            except Exception as e:
                print(f"  ❌ {str(e)[:50]}")
        
        print(f"✅ SYNC COMPLETE: {synced} projects\n")
        return jsonify({"status": "ok", "synced": synced})
    
    except Exception as e:
        print(f"❌ SYNC ERROR: {e}\n")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, stem_count, created_at FROM projects ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    
    return jsonify([{
        "id": r[0],
        "title": r[1],
        "stem_count": r[2],
        "created_at": r[3]
    } for r in rows])

@app.route('/api/projects/<int:pid>', methods=['GET'])
def get_project(pid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id, title, stem_count FROM projects WHERE id = ?", (pid,))
    p = c.fetchone()
    if not p:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    
    c.execute("SELECT id, name, url FROM stems WHERE project_id = ?", (pid,))
    stems = c.fetchall()
    conn.close()
    
    return jsonify({
        "id": p[0],
        "title": p[1],
        "stem_count": p[2],
        "stems": [{"id": s[0], "name": s[1], "url": s[2]} for s in stems]
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "1.0"})

if __name__ == '__main__':
    print("🚀 Starting server on http://localhost:5000")
    print("📖 Open: https://clubkaraoke.github.io/VOCAL_REMOVER_CLOUDE/")
    print("   (Update docs/index.html to use http://localhost:5000/api)\n")
    app.run(debug=False, host='0.0.0.0', port=5000)
