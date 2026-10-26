# BizAssist AI — Improved Local Starter

A beginner-friendly Flask + SQLite prototype for managing customer enquiries and drafting replies.

## Features
- Dashboard with customer totals, new enquiries, and due follow-ups
- Add and edit customer records
- Track statuses and follow-up dates
- Rule-based reply drafts for pricing, bookings, follow-ups, apologies, product options, and delivery questions
- Copy a draft to your clipboard
- SQLite storage that persists between restarts
- No paid AI API required

## Requirements
- Python 3.10 or newer recommended
- Flask (installed from `requirements.txt`)

## Run in PyCharm / Windows
1. Extract this ZIP into a permanent folder, for example `Documents\\bizassist_ai_improved`.
2. Open that folder in PyCharm.
3. Open the PyCharm terminal in the project folder.
4. Run `python -m pip install -r requirements.txt`.
5. Run `python app.py`.
6. Open `http://127.0.0.1:5000` in your browser.

Stop the local server with `Ctrl+C` in the terminal.

## Existing customer database
The app stores records in `bizassist.db` beside `app.py`. To preserve your existing customers, copy your existing `bizassist.db` into the same folder as this new `app.py` **before the first run**. Keep a separate backup of that database first. If you do not have an existing database file, the app creates a new one.

## Important limitations
- The reply generator uses rules and templates; it is not a generative AI model.
- Review every draft before sending it. The app does not send messages automatically.
- This is a local learning prototype, not a production-ready multi-user service. It does not include login, cloud hosting, business data separation, or production security controls.
- Do not expose Flask's development server publicly or store sensitive customer information in a public demo.
