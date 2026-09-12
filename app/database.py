"""
SQLite database management for MVSep DAW
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import contextmanager
from datetime import datetime

# Database file location
DB_PATH = Path(__file__).parent / "daw.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize the database schema"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                bpm REAL,
                duration REAL,
                stem_count INTEGER,
                original_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS stems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                filename TEXT,
                duration REAL,
                url TEXT,
                file_size INTEGER,
                cached_locally INTEGER DEFAULT 0,
                cached_path TEXT,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_stems_track_id ON stems(track_id);

            CREATE TABLE IF NOT EXISTS silent_regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                stem_index INTEGER NOT NULL,
                start_ms REAL NOT NULL,
                end_ms REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                UNIQUE(track_id, stem_index, start_ms, end_ms)
            );

            CREATE INDEX IF NOT EXISTS idx_silent_regions_track_id ON silent_regions(track_id);
        """)


def create_track(
    name: str,
    bpm: Optional[float] = None,
    duration: Optional[float] = None,
    stem_count: Optional[int] = None,
    original_filename: Optional[str] = None
) -> int:
    """Create a new track"""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tracks (name, bpm, duration, stem_count, original_filename)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, bpm, duration, stem_count, original_filename)
        )
        return cursor.lastrowid


def create_stem(
    track_id: int,
    name: str,
    filename: str = "",
    duration: Optional[float] = None,
    url: Optional[str] = None,
    file_size: Optional[int] = None
) -> int:
    """Create a new stem"""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO stems (track_id, name, filename, duration, url, file_size)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (track_id, name, filename, duration, url, file_size)
        )
        return cursor.lastrowid


def get_all_tracks() -> List[Dict]:
    """Get all tracks"""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tracks ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def get_track_with_stems(track_id: int) -> Optional[Dict]:
    """Get track with all its stems"""
    with get_db() as conn:
        track = conn.execute(
            "SELECT * FROM tracks WHERE id = ?",
            (track_id,)
        ).fetchone()
        
        if not track:
            return None
        
        stems = conn.execute(
            "SELECT * FROM stems WHERE track_id = ? ORDER BY id",
            (track_id,)
        ).fetchall()
    
    track_dict = dict(track)
    track_dict['stems'] = [dict(s) for s in stems]
    return track_dict


def track_exists(track_id: int) -> bool:
    """Check if track exists"""
    with get_db() as conn:
        result = conn.execute(
            "SELECT id FROM tracks WHERE id = ?",
            (track_id,)
        ).fetchone()
    return result is not None


def delete_track(track_id: int) -> bool:
    """Delete a track and all its stems"""
    with get_db() as conn:
        result = conn.execute(
            "DELETE FROM tracks WHERE id = ?",
            (track_id,)
        )
    return result.rowcount > 0


def save_silent_regions(track_id: int, silent_regions: Dict) -> None:
    """
    Save silent regions for a track
    Format: {0: [[0, 1000], [5000, 6000]], 1: [], ...}
    """
    with get_db() as conn:
        # Limpiar previos
        conn.execute("DELETE FROM silent_regions WHERE track_id = ?", (track_id,))
        
        # Guardar nuevos
        for stem_index, regions in silent_regions.items():
            for start_ms, end_ms in regions:
                conn.execute(
                    """
                    INSERT INTO silent_regions (track_id, stem_index, start_ms, end_ms)
                    VALUES (?, ?, ?, ?)
                    """,
                    (track_id, int(stem_index), start_ms, end_ms)
                )


def get_silent_regions(track_id: int) -> Dict:
    """
    Get silent regions for a track formatted
    Returns: {0: [[0, 1000], [5000, 6000]], 1: [], ...}
    """
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT stem_index, start_ms, end_ms FROM silent_regions
            WHERE track_id = ?
            ORDER BY stem_index, start_ms
            """,
            (track_id,)
        ).fetchall()
    
    result = {}
    for row in rows:
        stem_index = row['stem_index']
        if stem_index not in result:
            result[stem_index] = []
        result[stem_index].append((row['start_ms'], row['end_ms']))
    
    return result
