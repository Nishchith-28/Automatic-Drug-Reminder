💊 Automatic Drug Reminder System

A web-based medication management and reminder system designed to help patients follow their prescribed medication schedules, improve medication adherence, and keep guardians informed about missed doses.

📌 Project Overview

The Automatic Drug Reminder System is a software-based web application that simplifies medication management for doctors and patients. Doctors can upload prescriptions and create medication schedules, while patients can view their prescribed medicines and receive timely reminders to take them.

The system allows patients to update their medication status as Taken, Remind Me Later, or Not Taken. When a scheduled dose is missed or marked as not taken, the system can notify the patient's guardian to help ensure better medication follow-up.

🎯 Objectives

Develop a secure, web-based medication management system.

Allow doctors to upload prescriptions and create medication schedules.

Provide timely medication reminders to patients.

Enable patients to update their medication status.

Notify guardians when scheduled medication is missed or not taken.

Maintain medication history and support better medication adherence.

✨ Key Features

👨‍⚕️ Doctor Module

Secure doctor login and authentication.

View and select registered patients.

Upload and manage patient prescriptions.

Enter medicine names, dosages, timings, and duration.

Create and manage medication schedules.

Review patient medication history, where enabled.

🧑‍🦽 Patient Module

Secure patient login.

View prescriptions uploaded by the doctor.

Access medicine details and scheduled timings.

Receive reminders when medication is due.

Update medication status:

Taken – Confirms that the medicine has been taken.

Remind Me Later – Defers the reminder.

Not Taken – Records that the medicine was not taken.

View previous medication records.

🔔 Reminder and Guardian Notification Module

Send reminders according to the medication schedule.

Allow patients to postpone reminders.

Track missed or unconfirmed doses.

Notify registered guardians about missed medication according to the configured rules.

Maintain medication status and notification history.

🔄 System Workflow

Doctor Login: The doctor logs in to the website.

Patient Selection: The doctor selects the required patient.

Prescription Upload: The doctor enters or uploads the prescription details.

Schedule Creation: The system stores the medication schedule.

Patient Login: The patient logs in and views the prescribed medicines.

Medication Reminder: The system sends a reminder when a dose is due.

Patient Response: The patient selects Taken, Remind Me Later, or Not Taken.

Guardian Notification: If a dose is missed or marked as not taken, the configured notification workflow alerts the guardian.

History Tracking: Medication status and related records are stored for future reference.

🛠️ Technologies Used

The following is a suggested technology stack; update it to match the technologies actually used in your implementation.

Component

Suggested Technology

Frontend

HTML, CSS, JavaScript

Backend

Python with Flask or FastAPI

Database

MySQL, PostgreSQL, or SQLite

Authentication

Role-based login and password hashing

Notifications

Browser notifications, email, or SMS API

Version Control

Git and GitHub

🏗️ System Architecture

The application follows a basic three-layer architecture:

Presentation Layer: Provides the doctor and patient interfaces.

Application Layer: Handles authentication, prescriptions, medication schedules, reminder logic, and guardian notifications.

Database Layer: Stores user details, prescriptions, schedules, medication status, and history.

📂 Project Structure

Example project structure:

automatic-drug-reminder/
│
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── doctor.html
│   ├── patient.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── backend/
│   ├── app.py
│   ├── routes/
│   ├── models/
│   └── services/
│
├── database/
│   └── schema.sql
│
├── screenshots/
│
├── .gitignore
├── requirements.txt
└── README.md

Note: This is an example structure. Modify the folders and filenames according to your actual repository.
