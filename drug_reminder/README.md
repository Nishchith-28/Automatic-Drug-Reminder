# Dosely — Automatic Drug Reminder

A doctor writes a prescription once. Dosely reminds the patient at every
dose, right in the browser, and if a dose is skipped it automatically
alerts a linked guardian — no one has to chase anyone.

Built with **Python (Flask) + SQLite only** — nothing else to install,
nothing to sign up for, and no API keys. It runs entirely on your own
machine.

---

## 1. Setup

```bash
cd drug_reminder
pip install -r requirements.txt      # installs Flask only
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The first run creates `drugreminder.db` (SQLite) automatically — nothing
to configure.

> Tested on Python 3.12. Any Python 3.9+ should work.

## 2. Try it in under two minutes

1. **Register as a doctor** (e.g. `doc@example.com`).
2. **Register as a patient** in a second browser tab / private window
   (e.g. `patient@example.com`).
3. **Register as a guardian** in a third tab (e.g. `guardian@example.com`).
4. As the doctor, go to **New prescription**, enter the patient's email,
   a medicine name, and a dose time set to a minute or two from now
   (24-hour clock, e.g. `14:32`). Save it.
5. As the patient, open the **Guardians** page and link the guardian's
   email — this is what makes escalation possible.
6. Wait for the dose time. Within ~15 seconds of it arriving, a reminder
   card pops up on the patient dashboard (and, if you allow the browser
   permission prompt, a real desktop notification too) with three
   buttons: **Taken**, **Remind me later**, **Not taken**.
7. Click **Not taken** — switch to the guardian tab and within ~20
   seconds an alert appears there automatically.

If a reminder is left completely unanswered for 20 minutes, the engine
escalates it to the guardian on its own — you don't need to click
anything to see that path, it just needs 20 real minutes to pass (see
"Tuning" below if you want to test that faster).

## 3. How the three roles work

**Doctor**
- Dashboard listing patients and prescriptions written.
- "New prescription" form: patient's email, medicine, dosage, one or
  more dose times, start date, course length in days, optional
  instructions, and an optional scanned copy (PDF/PNG/JPG).
- Can stop a prescription early (stops future reminders for it).

**Patient**
- Dashboard with a visual timeline of today's doses (taken / due /
  missed / upcoming) and live reminder cards as doses come due.
- "My prescriptions" — full history with dosage, schedule, instructions
  and the attached file if the doctor uploaded one.
- "Guardians" — link the email of whoever should be alerted if a dose
  is missed.

**Guardian**
- Dashboard showing linked patients and a live feed of alerts, triggered
  either by the patient explicitly tapping "Not taken," or by a
  reminder timing out unanswered.

## 4. How the "automatic" part works

A background thread (`reminder_engine.py`) wakes up every 15 seconds and:

1. Looks at every active prescription and, for each dose time that has
   arrived today, creates a reminder if one doesn't already exist.
2. Looks at reminders that have been pending for more than 20 minutes
   with no response, marks them **missed**, and files an alert for
   every guardian linked to that patient.

The patient's browser polls `/api/reminders/due` every 15 seconds and
the guardian's browser polls `/api/alerts/unread` every 20 seconds —
that's what makes the reminder/alert cards appear without refreshing
the page. Both also trigger a real browser `Notification` if the user
has granted permission.

**Tuning** (top of `reminder_engine.py`):
```python
TICK_SECONDS = 15          # how often the engine checks the clock
ESCALATION_MINUTES = 20    # unanswered-too-long -> alert guardian
SNOOZE_MINUTES = 10        # "remind me later" delay
```

## 5. Project layout

```
drug_reminder/
  app.py                 # Flask routes (auth, doctor, patient, guardian, JSON API)
  db.py                  # SQLite schema + all queries (plain sqlite3, no ORM)
  reminder_engine.py      # background thread: generates + escalates reminders
  requirements.txt
  templates/              # Jinja2 pages
  static/css/style.css    # design system
  static/js/main.js       # polling + notification + reminder/alert cards
  static/uploads/prescriptions/  # uploaded prescription files land here
```

## 6. Known limitations (by design, so it runs with zero setup)

- **Browser notifications only fire while a dashboard tab is open.**
  There's no push-when-the-app-is-closed and no real SMS — that needs a
  paid provider (e.g. Twilio for SMS, or a service-worker + VAPID setup
  for background push) and API keys nobody can hand you for free. The
  in-app + browser-notification approach here needs neither.
- **Single-process dev server.** `app.run(...)` is Flask's built-in
  server — fine for a demo or a class project, not for production.
  For real deployment, run it behind something like gunicorn + nginx.
- **No email verification / password reset** — kept out to keep the
  scope focused on the reminder flow itself.
- The demo `secret_key` in `app.py` is not secure — change it before
  putting this anywhere public.

## 7. If you want to add real SMS later

Swap the `_alert_guardians()` and reminder-creation points in
`reminder_engine.py` / `app.py` for a call to an SMS API (Twilio,
MSG91, etc.) using the `phone` field already stored on every user. The
data model doesn't need to change — you're just adding a network call
alongside the existing in-app alert.
