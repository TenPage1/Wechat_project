# db.py —— SQLite 数据层（零配置，适合大创调试；后期可换 MySQL）
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'aed.db')


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row   # 让查询结果可用列名访问
    return conn


def init_db():
    """建表 + 插入示例数据（仅首次）"""
    conn = get_conn()
    cur = conn.cursor()

    # 无人机点位表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS points (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT NOT NULL,              -- takeoff / landing
            name        TEXT NOT NULL,
            longitude   REAL NOT NULL,
            latitude    REAL NOT NULL,
            qr_id       TEXT UNIQUE,                -- 停靠点二维码唯一标识
            status      TEXT DEFAULT 'available'    -- available / occupied
        )
    ''')

    # 用户表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            openid      TEXT UNIQUE NOT NULL,
            nickname    TEXT,
            create_time TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')

    # 无人机表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS drones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            status          TEXT DEFAULT 'offline',   -- idle / busy / offline
            current_lng     REAL,
            current_lat     REAL,
            last_heartbeat  TEXT
        )
    ''')

    # 呼叫订单表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_openid   TEXT NOT NULL,
            drone_id      INTEGER,
            from_point_id INTEGER,
            to_point_id   INTEGER,
            status        TEXT DEFAULT 'pending',   -- pending/taking_off/flying/arrived/done/failed
            drone_lng     REAL,
            drone_lat     REAL,
            create_time   TEXT DEFAULT (datetime('now','localtime')),
            update_time   TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')

    # 建议反馈表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            openid      TEXT,
            content     TEXT NOT NULL,
            create_time TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')

    conn.commit()

    # 首次插入示例点位（上海佘山一带）
    cur.execute('SELECT COUNT(*) AS c FROM points')
    if cur.fetchone()['c'] == 0:
        samples = [
            ('takeoff', '起飞点A-佘山站', 121.196, 31.096, None),
            ('takeoff', '起飞点B-大学城', 121.226, 31.036, None),
            ('landing', '停靠点1-欢乐谷', 121.188, 31.091, 'QR_LAND_001'),
            ('landing', '停靠点2-月湖公园', 121.204, 31.083, 'QR_LAND_002'),
            ('landing', '停靠点3-广富林', 121.219, 31.056, 'QR_LAND_003'),
        ]
        cur.executemany(
            'INSERT INTO points (type,name,longitude,latitude,qr_id) VALUES (?,?,?,?,?)',
            samples
        )

    # 首次插入示例无人机
    cur.execute('SELECT COUNT(*) AS c FROM drones')
    if cur.fetchone()['c'] == 0:
        conn.execute(
            "INSERT INTO drones (name,status,current_lng,current_lat) VALUES ('无人机-01','idle',121.196,31.096)"
        )

    conn.commit()
    conn.close()


# ---------- 点位 ----------
def list_points():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM points ORDER BY type,id').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_point(pid):
    conn = get_conn()
    r = conn.execute('SELECT * FROM points WHERE id=?', (pid,)).fetchone()
    conn.close()
    return dict(r) if r else None


def add_point(p):
    conn = get_conn()
    cur = conn.execute(
        'INSERT INTO points (type,name,longitude,latitude,qr_id,status) VALUES (?,?,?,?,?,?)',
        (p['type'], p['name'], p['longitude'], p['latitude'], p.get('qr_id'), p.get('status', 'available'))
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def update_point(pid, p):
    conn = get_conn()
    conn.execute(
        'UPDATE points SET type=?,name=?,longitude=?,latitude=?,qr_id=?,status=? WHERE id=?',
        (p['type'], p['name'], p['longitude'], p['latitude'], p.get('qr_id'), p.get('status', 'available'), pid)
    )
    conn.commit()
    conn.close()


def delete_point(pid):
    conn = get_conn()
    conn.execute('DELETE FROM points WHERE id=?', (pid,))
    conn.commit()
    conn.close()


def get_point_by_qr(qr_id):
    conn = get_conn()
    r = conn.execute('SELECT * FROM points WHERE qr_id=?', (qr_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


# ---------- 用户 ----------
def get_or_create_user(openid, nickname=None):
    conn = get_conn()
    r = conn.execute('SELECT * FROM users WHERE openid=?', (openid,)).fetchone()
    if r:
        conn.close()
        return dict(r)
    cur = conn.execute('INSERT INTO users (openid,nickname) VALUES (?,?)', (openid, nickname))
    conn.commit()
    uid = cur.lastrowid
    r = conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    conn.close()
    return dict(r)


def list_users():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(uid):
    conn = get_conn()
    conn.execute('DELETE FROM users WHERE id=?', (uid,))
    conn.commit()
    conn.close()


# ---------- 无人机 ----------
def list_drones():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM drones ORDER BY id').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_drone(did):
    conn = get_conn()
    r = conn.execute('SELECT * FROM drones WHERE id=?', (did,)).fetchone()
    conn.close()
    return dict(r) if r else None


def get_idle_drone():
    conn = get_conn()
    r = conn.execute("SELECT * FROM drones WHERE status='idle' ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return dict(r) if r else None


def set_drone_status(did, status):
    conn = get_conn()
    conn.execute(
        "UPDATE drones SET status=?, last_heartbeat=datetime('now','localtime') WHERE id=?",
        (status, did)
    )
    conn.commit()
    conn.close()


def set_drone_position(did, lng, lat):
    conn = get_conn()
    conn.execute(
        "UPDATE drones SET current_lng=?, current_lat=?, last_heartbeat=datetime('now','localtime') WHERE id=?",
        (lng, lat, did)
    )
    conn.commit()
    conn.close()


# ---------- 订单 ----------
def create_order(user_openid, from_point_id, to_point_id, drone_id):
    conn = get_conn()
    cur = conn.execute(
        '''INSERT INTO orders (user_openid,drone_id,from_point_id,to_point_id,status)
           VALUES (?,?,?,?, 'pending')''',
        (user_openid, drone_id, from_point_id, to_point_id)
    )
    conn.commit()
    oid = cur.lastrowid
    conn.close()
    return oid


def get_order(oid):
    conn = get_conn()
    r = conn.execute('SELECT * FROM orders WHERE id=?', (oid,)).fetchone()
    conn.close()
    return dict(r) if r else None


def update_order(oid, **fields):
    if not fields:
        return
    conn = get_conn()
    sets = ', '.join(f'{k}=?' for k in fields)
    vals = list(fields.values())
    vals.append(oid)
    conn.execute(
        f"UPDATE orders SET {sets}, update_time=datetime('now','localtime') WHERE id=?", vals
    )
    conn.commit()
    conn.close()


def list_orders(openid=None):
    conn = get_conn()
    if openid:
        rows = conn.execute('SELECT * FROM orders WHERE user_openid=? ORDER BY id DESC', (openid,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- 反馈 ----------
def add_feedback(openid, content):
    conn = get_conn()
    conn.execute('INSERT INTO feedback (openid,content) VALUES (?,?)', (openid, content))
    conn.commit()
    conn.close()


def list_feedback():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM feedback ORDER BY id DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]
