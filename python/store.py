



from arduino.app_bricks.dbstorage_sqlstore import SQLStore
from app_frame import AppFrame
from typing import Any

import os
import shutil


_PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = "/app" if os.path.isdir("/app") else os.path.dirname(_PYTHON_DIR)
DATA_DIR = os.path.join(_PROJ_ROOT, "data")



DB_FILENAME = "frames.db"
DB_PATH = os.path.join(DATA_DIR, DB_FILENAME)


TRAJECTORY_ASSETS_DIR = os.path.join(_PROJ_ROOT, "assets", "common", "img", "trajectories")

class SafeSQLStoreWrapper:
    def __init__(self, original, on_failure_cb=None):
        self._orig = original
        self._ok = True
        self._on_failure = on_failure_cb
    
    def start(self):
        try:
            self._orig.start()
        except Exception as e:
            print(f"[SQLStoreWrapper] Failed to start: {e}")
            self._ok = False
            if self._on_failure:
                self._on_failure(e)
            
    def __getattr__(self, name):
        if not self._ok:
            def dummy_method(*args, **kwargs):
                print(f"[SQLStoreWrapper] Dummy method {name} called (DB is offline)")
                if name == "read":
                    return []
                elif name == "execute_sql":
                    return []
                return None
            return dummy_method
        return getattr(self._orig, name)


db = SafeSQLStoreWrapper(SQLStore(database_name=DB_FILENAME))

def init_db():
    
    import getpass
    import sqlite3
    
    
    if not os.path.exists(DATA_DIR):
        print(f"[db_frames] Creating canonical data directory: {DATA_DIR}")
        try: os.makedirs(DATA_DIR, exist_ok=True)
        except Exception as e: print(f"[db_frames] ERROR creating dir: {e}")

    print(f"[db_frames] Initializing as user: {getpass.getuser()}")
    print(f"[db_frames] SQLStore assigned filename: {DB_FILENAME}")
    print(f"[db_frames] Physical DB Path expected: {DB_PATH}")

    
    try:
        test_conn = sqlite3.connect(DB_PATH, timeout=2)
        test_conn.execute("SELECT 1")
        test_conn.close()
        print(f"[db_frames] Raw SQLite connectivity to {DB_PATH}: SUCCESS")
    except Exception as e:
        print(f"[db_frames] Raw SQLite connectivity to {DB_PATH}: FAILED - {e}")

    
    try:
        db.start()
        print(f"[db_frames] SQLStore Brick started successfully.")
    except Exception as e:
        print(f"[db_frames] FAILED to start SQLStore Brick: {e}")
        
        wrong_path = os.path.join(_PYTHON_DIR, "data", DB_FILENAME)
        if os.path.exists(wrong_path):
            print(f"[db_frames] WARNING: Found database in forbidden path: {wrong_path}")
    
    db.create_table(
        "trajectories",
        {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "cell_image": "TEXT",
        }
    )
    
    try:
        db.execute_sql("ALTER TABLE trajectories ADD COLUMN cell_image TEXT")
    except Exception as e:
        if "duplicate column name" not in str(e).lower():
            print(f"[db_frames] Migration info: {e}")
    
    
    db.create_table(
        "frames",
        {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "duration_ms": "INTEGER",
            "position": "INTEGER",
            "brightness_levels": "INTEGER",
            "rows": "TEXT",  
            "trajectory_id": "INTEGER",
            "command": "TEXT",
        }
    )
    
    try:
        db.execute_sql("ALTER TABLE frames ADD COLUMN command TEXT")
    except Exception as e:
        if "duplicate column name" not in str(e).lower():
            print(f"[db_frames] Migration info (frames.command): {e}")

    
    db.create_table(
        "users",
        {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "games_played": "INTEGER",
            "games_won": "INTEGER",
            "games_lost": "INTEGER",
            "avatar": "TEXT",
            "color": "TEXT",
            "world": "TEXT",
        }
    )
    
    try:
        db.execute_sql("ALTER TABLE users ADD COLUMN color TEXT")
    except Exception as e:
        if "duplicate column name" not in str(e).lower():
            print(f"[db_frames] Migration info (users.color): {e}")
    
    try:
        db.execute_sql("ALTER TABLE users ADD COLUMN world TEXT")
    except Exception as e:
        if "duplicate column name" not in str(e).lower():
            print(f"[db_frames] Migration info (users.world): {e}")
    
    db.create_table(
        "game_history",
        {
            "id": "INTEGER PRIMARY KEY",
            "user_id": "INTEGER",
            "trajectory_id": "INTEGER",
            "mistakes": "INTEGER",
            "total_steps": "INTEGER",
            "completed_steps": "INTEGER",
            "timestamp": "TEXT",
            "duration_seconds": "INTEGER",
            "won": "BOOLEAN",
        }
    )
    abs_db_path = os.path.abspath(DB_PATH)
    print(f"[db_frames] SQLStore started. Database file: {abs_db_path}")
    print("[db_frames] Tables ready: frames, trajectories, users, game_history.")






def create_user(name: str, avatar: str = "fas fa-robot", color: str = "#3b82f6", world: str = "world-space") -> int:
    
    record = {
        "name": name,
        "avatar": avatar,
        "color": color,
        "world": world,
        "games_played": 0,
        "games_won": 0,
        "games_lost": 0
    }
    db.store("users", record, create_table=False)
    last = db.execute_sql("SELECT last_insert_rowid() as id")
    return last[0].get("id") if last else None

def get_user(uid: int) -> dict[str, Any] | None:
    
    res = db.read("users", condition=f"id = {int(uid)}") or []
    return res[0] if res else None

def list_users() -> list[dict[str, Any]]:
    
    return db.read("users", order_by="name ASC") or []

def update_user(uid: int, data: dict) -> bool:
    
    
    if 'id' in data:
        del data['id']
    if not data:
        return False
    db.update("users", data, condition=f"id = {int(uid)}")
    return True

def delete_user(uid: int) -> bool:
    
    db.delete("users", condition=f"id = {int(uid)}")
    return True


def record_game(uid: int, trajectory_id: int | None, won: bool, mistakes: int = 0, total_steps: int = 0, completed_steps: int = 0, duration_seconds: int = 0) -> bool:
    
    uid = int(uid)
    if uid <= 0:
        raise ValueError(f"uid must be a positive integer, got {uid}")

    from datetime import datetime
    record = {
        "user_id": uid,
        "trajectory_id": trajectory_id,
        "won": won,
        "mistakes": mistakes,
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "duration_seconds": duration_seconds,
        "timestamp": datetime.now().isoformat()
    }
    db.store("game_history", record)
    
    
    
    won_col = "games_won" if won else "games_lost"
    sql = (
        f"UPDATE users "
        f"SET games_played = games_played + 1, "
        f"    {won_col} = {won_col} + 1 "
        f"WHERE id = {uid}"
    )
    db.execute_sql(sql)
    return True

def list_game_history(user_id: int = None, trajectory_id: int = None) -> list[dict]:
    
    conds = []
    if user_id: conds.append(f"gh.user_id = {int(user_id)}")
    if trajectory_id: conds.append(f"gh.trajectory_id = {int(trajectory_id)}")
    
    condition = f"WHERE {' AND '.join(conds)}" if conds else ""
    sql = (
        "SELECT gh.*, t.name AS trajectory_name "
        "FROM game_history gh "
        "LEFT JOIN trajectories t ON t.id = gh.trajectory_id "
        f"{condition} "
        "ORDER BY gh.timestamp DESC"
    )
    return db.execute_sql(sql) or []














def list_frames(trajectory_id: int = None, order_by: str = "position ASC, id ASC") -> list[dict[str, Any]]:
    
    condition = f"trajectory_id = {int(trajectory_id)}" if trajectory_id is not None else None
    res = db.read("frames", condition=condition, order_by=order_by) or []
    return res


def get_frame_by_id(fid: int) -> dict[str, Any] | None:
    
    res = db.read("frames", condition=f"id = {int(fid)}") or []
    if not res:
        return None
    return res[0]


def save_frame(frame: AppFrame) -> int:
    
    
    condition = f"trajectory_id = {int(frame.trajectory_id)}" if frame.trajectory_id is not None else "trajectory_id IS NULL"
    mx_rows = db.read("frames", columns=["MAX(position) as maxpos"], condition=condition) or []
    maxpos = mx_rows[0].get("maxpos") if mx_rows and len(mx_rows) > 0 else None
    next_position = (int(maxpos) if maxpos is not None else 0) + 1
    
    position = frame.position if frame.position is not None else next_position
    
    record = frame.to_record()
    record['position'] = position
    
    record.pop('id', None)
    
    db.store("frames", record, create_table=False)
    
    last = db.execute_sql("SELECT last_insert_rowid() as id")
    new_id = last[0].get("id") if last else None
    
    
    if new_id and (not frame.name or frame.name.strip() == ''):
        frame.name = f'Frame {new_id}'
        frame.id = new_id
        db.update("frames", {"name": frame.name}, condition=f"id = {new_id}")
    
    return new_id


def update_frame(frame: AppFrame) -> bool:
    
    if frame.id is None:
        raise ValueError("Cannot update frame without id")
    
    record = frame.to_record()
    
    fid = record.pop('id')
    
    db.update("frames", record, condition=f"id = {int(fid)}")
    return True


def bulk_update_frame_duration(duration) -> bool:
    
    if duration < 1:
        raise ValueError("Valid duration must be provided for bulk update")
    db.update("frames", {"duration_ms": int(duration)})
    return True

def delete_frame(fid: int) -> bool:
    
    
    frame = get_frame_by_id(fid)
    if not frame:
        return False
        
    db.delete("frames", condition=f"id = {int(fid)}")
    
    
    traj_id = frame.get('trajectory_id')
    condition = f"trajectory_id = {int(traj_id)}" if traj_id is not None else "trajectory_id IS NULL"
    
    rows = db.read("frames", condition=condition, order_by="position ASC, id ASC") or []
    for pos, r in enumerate(rows, start=1):
        db.update("frames", {"position": pos}, condition=f"id = {int(r.get('id'))}")
    return True


def reorder_frames(order: list[int]) -> bool:
    
    for idx, fid in enumerate(order, start=1):
        db.update("frames", {"position": idx}, condition=f"id = {int(fid)}")
    return True


def get_last_frame() -> AppFrame | None:
    
    records = db.read("frames", order_by="position DESC, id DESC") or []
    if not records:
        return None
    return AppFrame.from_record(records[0])


def get_or_create_active_frame(brightness_levels: int = 8) -> AppFrame:
    
    last = get_last_frame()
    if last is not None:
        return last
    
    
    frame = AppFrame.create_empty(
        id=None,
        name="",
        position=1,
        duration_ms=1000,
        brightness_levels=brightness_levels
    )
    
    
    frame.id = save_frame(frame)
    
    
    record = get_frame_by_id(frame.id)
    if record:
        return AppFrame.from_record(record)
    
    return frame






def create_trajectory(name: str) -> int:
    
    db.store("trajectories", {"name": name}, create_table=False)
    last = db.execute_sql("SELECT last_insert_rowid() as id")
    return last[0].get("id") if last else None


def get_trajectory_by_id(tid: int) -> dict[str, Any] | None:
    
    res = db.read("trajectories", condition=f"id = {int(tid)}") or []
    return res[0] if res else None


def list_trajectories() -> list[dict[str, Any]]:
    
    return db.read("trajectories", order_by="id ASC") or []


def update_trajectory(tid: int, data: dict) -> bool:
    
    if 'id' in data:
        del data['id']
    if not data:
        return False
    db.update("trajectories", data, condition=f"id = {int(tid)}")
    return True


def delete_trajectory(tid: int) -> bool:
    
    
    db.delete("frames", condition=f"trajectory_id = {int(tid)}")
    
    db.delete("trajectories", condition=f"id = {int(tid)}")
    return True
