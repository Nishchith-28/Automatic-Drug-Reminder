/* Dosely — patient reminder polling + guardian alert polling.
   No frameworks: plain fetch() against the Flask JSON endpoints in app.py. */

window.Dosely = (function () {

  function requestNotificationPermission() {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }

  function pushBrowserNotification(title, body) {
    if ("Notification" in window && Notification.permission === "granted") {
      try { new Notification(title, { body, icon: undefined }); } catch (e) { /* ignore */ }
    }
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : str;
    return div.innerHTML;
  }

  // ---------------- Patient: due reminders ----------------

  function initPatientReminders({ dueUrl, respondUrlTemplate }) {
    requestNotificationPermission();
    const stack = document.getElementById("reminder-stack");
    if (!stack) return;

    const shownIds = new Set();
    const POLL_MS = 15000;

    function respond(reminderId, action, cardEl) {
      const url = respondUrlTemplate.replace("/0/", `/${reminderId}/`);
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      })
        .then((r) => r.json())
        .then(() => {
          shownIds.delete(reminderId);
          if (cardEl) cardEl.remove();
          // Reload shortly after so the "today's schedule" timeline (server
          // rendered) reflects the new status too.
          setTimeout(() => window.location.reload(), 650);
        })
        .catch(() => { cardEl && cardEl.classList.add("rc-error"); });
    }

    function renderReminder(rem) {
      if (shownIds.has(rem.id)) return;
      shownIds.add(rem.id);

      const card = document.createElement("div");
      card.className = "reminder-card";
      card.dataset.id = rem.id;
      card.innerHTML = `
        <div class="rc-info">
          <span class="rc-med">${escapeHtml(rem.medicine_name)}${rem.dosage ? " — " + escapeHtml(rem.dosage) : ""}</span>
          <span class="rc-time">Due at ${escapeHtml(rem.dose_time)}</span>
        </div>
        <div class="reminder-actions">
          <button class="rc-btn taken">Taken</button>
          <button class="rc-btn snooze">Remind me later</button>
          <button class="rc-btn missed">Not taken</button>
        </div>`;

      card.querySelector(".taken").addEventListener("click", () => respond(rem.id, "taken", card));
      card.querySelector(".snooze").addEventListener("click", () => respond(rem.id, "snooze", card));
      card.querySelector(".missed").addEventListener("click", () => respond(rem.id, "missed", card));

      stack.appendChild(card);
      pushBrowserNotification("Time for your medicine", `${rem.medicine_name} is due now.`);
    }

    function poll() {
      fetch(dueUrl)
        .then((r) => r.json())
        .then((rows) => {
          const liveIds = new Set(rows.map((r) => r.id));
          // drop cards for reminders that are no longer due (e.g. snoozed by another tab)
          [...shownIds].forEach((id) => {
            if (!liveIds.has(id)) {
              shownIds.delete(id);
              const el = stack.querySelector(`[data-id="${id}"]`);
              if (el) el.remove();
            }
          });
          rows.forEach(renderReminder);
        })
        .catch(() => {});
    }

    poll();
    setInterval(poll, POLL_MS);
  }

  // ---------------- Guardian: unread alerts ----------------

  function initGuardianAlerts({ unreadUrl, readUrlTemplate }) {
    requestNotificationPermission();
    const stack = document.getElementById("alert-stack");
    if (!stack) return;

    const shownIds = new Set();
    const POLL_MS = 20000;

    function markRead(alertId, cardEl) {
      const url = readUrlTemplate.replace("/0/", `/${alertId}/`);
      fetch(url, { method: "POST" })
        .then((r) => r.json())
        .then(() => { shownIds.delete(alertId); if (cardEl) cardEl.remove(); })
        .catch(() => {});
    }

    function renderAlert(alert) {
      if (shownIds.has(alert.id)) return;
      shownIds.add(alert.id);

      const card = document.createElement("div");
      card.className = "alert-card";
      card.dataset.id = alert.id;
      card.innerHTML = `
        <div>
          <div class="ac-msg">${escapeHtml(alert.message)}</div>
          <div class="ac-time">${escapeHtml(alert.created_at)}</div>
        </div>
        <button class="rc-btn">Mark read</button>`;

      card.querySelector("button").addEventListener("click", () => markRead(alert.id, card));
      stack.appendChild(card);
      pushBrowserNotification("Dosely alert", alert.message);
    }

    function poll() {
      fetch(unreadUrl)
        .then((r) => r.json())
        .then((rows) => rows.forEach(renderAlert))
        .catch(() => {});
    }

    poll();
    setInterval(poll, POLL_MS);
  }

  return { initPatientReminders, initGuardianAlerts };
})();
