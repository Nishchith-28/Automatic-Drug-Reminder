"""
reminder_engine.py — the "automatic" part of the automatic drug reminder.

A daemon thread wakes up every TICK_SECONDS and:
  1. Looks at every active prescription and creates a reminder row for any
     dose whose time has arrived today (generate_due_reminders).
  2. Looks at reminders that have been sitting un-answered for longer than
     ESCALATION_MINUTES and escalates them: marks them 'missed' and files
     an alert for every guardian linked to that patient (escalate_stale).

Nothing here talks to the network — it only touches the local SQLite file,
so it needs no API keys and works completely offline.
"""
import threading
import time
import json
from datetime import datetime, timedelta

import db

TICK_SECONDS = 15          # how often the engine checks the clock
ESCALATION_MINUTES = 20    # no response this long after dose time -> alert guardian
SNOOZE_MINUTES = 10        # "remind me later" delay


def generate_due_reminders():
    today = datetime.now().strftime("%Y-%m-%d")
    now_hm = datetime.now().strftime("%H:%M")

    for presc in db.get_active_prescriptions():
        start_date = presc["start_date"]
        try:
            duration = int(presc["duration_days"])
            end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=duration - 1)).strftime("%Y-%m-%d")
        except Exception:
            end_date = today

        if not (start_date <= today <= end_date):
            continue

        try:
            times = json.loads(presc["times"])
        except Exception:
            times = []

        for t in times:
            if t <= now_hm:
                dose_time = f"{today} {t}"
                if not db.reminder_exists(presc["id"], dose_time):
                    db.create_reminder(
                        presc["id"], presc["patient_id"], presc["medicine_name"],
                        presc["dosage"], dose_time,
                    )


def escalate_stale_reminders():
    cutoff = (datetime.now() - timedelta(minutes=ESCALATION_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    for rem in db.get_stale_pending_reminders(cutoff):
        db.set_reminder_status(rem["id"], "missed")
        if not db.alert_already_sent_for_reminder(rem["id"]):
            _alert_guardians(rem, reason="no_response")


def _alert_guardians(reminder_row, reason):
    guardians = db.get_guardians_for_patient(reminder_row["patient_id"])
    patient = db.get_user_by_id(reminder_row["patient_id"])
    patient_name = patient["name"] if patient else "Patient"
    if reason == "no_response":
        message = (f"{patient_name} did not respond about {reminder_row['medicine_name']} "
                   f"(scheduled {reminder_row['dose_time']}). It has been marked missed.")
    else:
        message = (f"{patient_name} marked {reminder_row['medicine_name']} "
                   f"(scheduled {reminder_row['dose_time']}) as NOT TAKEN.")
    for g in guardians:
        db.create_guardian_alert(g["id"], reminder_row["patient_id"], reminder_row["id"], message)


def alert_guardians_not_taken(reminder_row):
    """Called immediately when a patient explicitly taps 'Not taken'."""
    _alert_guardians(reminder_row, reason="not_taken")


def _loop():
    while True:
        try:
            generate_due_reminders()
            escalate_stale_reminders()
        except Exception as e:
            print(f"[reminder_engine] error: {e}")
        time.sleep(TICK_SECONDS)


def start():
    db.init_db()
    t = threading.Thread(target=_loop, daemon=True, name="reminder-engine")
    t.start()
    return t
