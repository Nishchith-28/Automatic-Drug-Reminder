"""
db.py — all SQLite access lives here.

Uses plain sqlite3 (standard library) on purpose: no extra packages to
install, and the whole app runs with nothing but `pip install flask`.
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drugreminder.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('doctor','patient','guardian')),
    phone TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS guardian_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    guardian_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(patient_id, guardian_id),
    FOREIGN KEY(patient_id) REFERENCES users(id),
    FOREIGN KEY(guardian_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    dosage TEXT,
    times TEXT NOT NULL,               -- JSON list e.g. ["08:00","14:00","20:00"]
    start_date TEXT NOT NULL,          -- YYYY-MM-DD
    duration_days INTEGER NOT NULL,
    instructions TEXT,
    file_path TEXT,
    status TEXT NOT NULL DEFAULT 'active',   -- active / stopped
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(doctor_id) REFERENCES users(id),
    FOREIGN KEY(patient_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    dosage TEXT,
    dose_time TEXT NOT NULL,           -- YYYY-MM-DD HH:MM
    status TEXT NOT NULL DEFAULT 'pending',  -- pending / taken / missed
    snooze_until TEXT,
    responded_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(prescription_id, dose_time),
    FOREIGN KEY(prescription_id) REFERENCES prescriptions(id),
    FOREIGN KEY(patient_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS guardian_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guardian_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    reminder_id INTEGER,
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(guardian_id) REFERENCES users(id),
    FOREIGN KEY(patient_id) REFERENCES users(id),
    FOREIGN KEY(reminder_id) REFERENCES reminders(id)
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- users ----------

def create_user(name, email, password_hash, role, phone=None):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, role, phone) VALUES (?,?,?,?,?)",
        (name, email.strip().lower(), password_hash, role, phone),
    )
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


# ---------- guardian links ----------

def link_guardian(patient_id, guardian_id):
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO guardian_links (patient_id, guardian_id) VALUES (?,?)",
            (patient_id, guardian_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_guardians_for_patient(patient_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT u.* FROM users u
           JOIN guardian_links gl ON gl.guardian_id = u.id
           WHERE gl.patient_id = ?""",
        (patient_id,),
    ).fetchall()
    conn.close()
    return rows


def get_patients_for_guardian(guardian_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT u.* FROM users u
           JOIN guardian_links gl ON gl.patient_id = u.id
           WHERE gl.guardian_id = ?""",
        (guardian_id,),
    ).fetchall()
    conn.close()
    return rows


# ---------- prescriptions ----------

def create_prescription(doctor_id, patient_id, medicine_name, dosage, times_list,
                         start_date, duration_days, instructions, file_path):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO prescriptions
           (doctor_id, patient_id, medicine_name, dosage, times, start_date,
            duration_days, instructions, file_path)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (doctor_id, patient_id, medicine_name, dosage, json.dumps(times_list),
         start_date, duration_days, instructions, file_path),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def get_prescriptions_for_patient(patient_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT p.*, u.name AS doctor_name FROM prescriptions p
           JOIN users u ON u.id = p.doctor_id
           WHERE p.patient_id = ? ORDER BY p.created_at DESC""",
        (patient_id,),
    ).fetchall()
    conn.close()
    return rows


def get_prescriptions_by_doctor(doctor_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT p.*, u.name AS patient_name, u.email AS patient_email FROM prescriptions p
           JOIN users u ON u.id = p.patient_id
           WHERE p.doctor_id = ? ORDER BY p.created_at DESC""",
        (doctor_id,),
    ).fetchall()
    conn.close()
    return rows


def get_patients_for_doctor(doctor_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT DISTINCT u.* FROM users u
           JOIN prescriptions p ON p.patient_id = u.id
           WHERE p.doctor_id = ? ORDER BY u.name""",
        (doctor_id,),
    ).fetchall()
    conn.close()
    return rows


def get_prescription(prescription_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM prescriptions WHERE id = ?", (prescription_id,)).fetchone()
    conn.close()
    return row


def get_active_prescriptions():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prescriptions WHERE status = 'active'").fetchall()
    conn.close()
    return rows


def stop_prescription(prescription_id, doctor_id):
    conn = get_db()
    conn.execute(
        "UPDATE prescriptions SET status = 'stopped' WHERE id = ? AND doctor_id = ?",
        (prescription_id, doctor_id),
    )
    conn.commit()
    conn.close()


# ---------- reminders ----------

def reminder_exists(prescription_id, dose_time):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM reminders WHERE prescription_id = ? AND dose_time = ?",
        (prescription_id, dose_time),
    ).fetchone()
    conn.close()
    return row is not None


def create_reminder(prescription_id, patient_id, medicine_name, dosage, dose_time):
    conn = get_db()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO reminders
               (prescription_id, patient_id, medicine_name, dosage, dose_time)
               VALUES (?,?,?,?,?)""",
            (prescription_id, patient_id, medicine_name, dosage, dose_time),
        )
        conn.commit()
    finally:
        conn.close()


def get_due_reminders_for_patient(patient_id):
    """Pending reminders that are due now (not snoozed into the future)."""
    conn = get_db()
    now = now_str()
    rows = conn.execute(
        """SELECT * FROM reminders
           WHERE patient_id = ? AND status = 'pending'
             AND (snooze_until IS NULL OR snooze_until <= ?)
             AND dose_time <= ?
           ORDER BY dose_time ASC""",
        (patient_id, now, now),
    ).fetchall()
    conn.close()
    return rows


def get_today_reminders_for_patient(patient_id, today_str):
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM reminders WHERE patient_id = ? AND dose_time LIKE ?
           ORDER BY dose_time ASC""",
        (patient_id, today_str + "%"),
    ).fetchall()
    conn.close()
    return rows


def get_reminder(reminder_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
    conn.close()
    return row


def set_reminder_status(reminder_id, status):
    conn = get_db()
    conn.execute(
        "UPDATE reminders SET status = ?, responded_at = ? WHERE id = ?",
        (status, now_str(), reminder_id),
    )
    conn.commit()
    conn.close()


def snooze_reminder(reminder_id, snooze_until):
    conn = get_db()
    conn.execute(
        "UPDATE reminders SET snooze_until = ?, responded_at = ? WHERE id = ?",
        (snooze_until, now_str(), reminder_id),
    )
    conn.commit()
    conn.close()


def get_stale_pending_reminders(cutoff_dose_time):
    """Pending reminders whose dose_time is older than cutoff -> candidates to escalate."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM reminders WHERE status = 'pending' AND dose_time <= ?",
        (cutoff_dose_time,),
    ).fetchall()
    conn.close()
    return rows


# ---------- guardian alerts ----------

def create_guardian_alert(guardian_id, patient_id, reminder_id, message):
    conn = get_db()
    conn.execute(
        """INSERT INTO guardian_alerts (guardian_id, patient_id, reminder_id, message)
           VALUES (?,?,?,?)""",
        (guardian_id, patient_id, reminder_id, message),
    )
    conn.commit()
    conn.close()


def get_alerts_for_guardian(guardian_id, unread_only=False):
    conn = get_db()
    q = """SELECT ga.*, u.name AS patient_name FROM guardian_alerts ga
           JOIN users u ON u.id = ga.patient_id
           WHERE ga.guardian_id = ?"""
    if unread_only:
        q += " AND ga.is_read = 0"
    q += " ORDER BY ga.created_at DESC"
    rows = conn.execute(q, (guardian_id,)).fetchall()
    conn.close()
    return rows


def mark_alert_read(alert_id, guardian_id):
    conn = get_db()
    conn.execute(
        "UPDATE guardian_alerts SET is_read = 1 WHERE id = ? AND guardian_id = ?",
        (alert_id, guardian_id),
    )
    conn.commit()
    conn.close()


def alert_already_sent_for_reminder(reminder_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM guardian_alerts WHERE reminder_id = ? LIMIT 1", (reminder_id,)
    ).fetchone()
    conn.close()
    return row is not None
