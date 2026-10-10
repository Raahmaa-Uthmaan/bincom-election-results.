# Bincom Election Results Demo

A small web application built for the Bincom basic programming test using basic Python and the standard-library WSGI server (no web framework required). It uses the supplied `bincom_test.sql` sample data converted into a local SQLite database for easier setup and demonstration.

## Features

1. **Polling-unit results:** select a polling unit and view each party's recorded votes.
2. **LGA totals:** select a Local Government Area and sum party scores across its polling units. The calculation joins `announced_pu_results` to `polling_unit`; it does **not** read from `announced_lga_results`.
3. **Add polling unit:** create a polling unit, select its LGA and ward using a chained dropdown, and save a score for every party.

## Technology

- Python 3
- Python standard library (WSGI, SQLite, HTML escaping, form parsing)
- SQLite (a portable copy of the provided sample data)
- HTML, CSS and JavaScript

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create and activate a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\\Scripts\\Activate.ps1
   # macOS/Linux:
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt  # no third-party packages are required
   ```

5. Start the app:

   ```bash
   python app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

The included `election.db` is already populated from the supplied SQL dump, so you do not need to install MySQL to run this version.

## Database notes

The source dump has 25 LGA rows, 263 ward rows, 272 polling-unit rows, 9 party rows and 150 polling-unit result records. This app keeps the Delta State LGA records (`state_id = 25`).

The source schema uses `polling_unit.uniqueid` as the polling-unit record key. `announced_pu_results.polling_unit_uniqueid` is stored as text, so the app casts it to an integer when joining. LGA and ward links use the dataset's `uniqueid` values.

## Deploying

The project includes a `Procfile` with the start command `python app.py`. Choose a host that supports a custom Python start command and provides persistent storage for SQLite. If deploying to a platform with an ephemeral filesystem, configure a persistent disk for `election.db` or use a managed persistent database; otherwise newly entered records may be lost when the instance restarts.

This is a recruitment-test demo and does not implement authentication or production election-security controls.

## Suggested manual checks

- Open Polling unit and select ID 8; PDP should show 802 and the other recorded party scores should match the supplied dump.
- Choose an LGA and confirm its party totals are calculated from polling-unit rows.
- Add a test polling unit with zero scores, save it, and verify that it appears in the polling-unit selector.
- Check that the Ward dropdown changes when a different LGA is selected.
## Render deployment with persistent SQLite storage

1. Push this project folder to a GitHub repository. Include `app.py`, `election.db`, `static/style.css`, `static/app.js`, `requirements.txt`, and `Procfile`.
2. In Render, create a **Web Service** from that repository with runtime **Python**, build command `pip install -r requirements.txt`, and start command `python app.py`.
3. Add a persistent disk mounted at `/var/data` (Render requires a paid web service for persistent disks).
4. Add the environment variable `DATABASE_PATH=/var/data/election.db`.
5. Deploy, then open the `onrender.com` URL shown on the service page.

On first start, the app copies the included `election.db` into the persistent disk if the target file does not exist. Subsequent restarts use the stored database, preserving records added through the app.
