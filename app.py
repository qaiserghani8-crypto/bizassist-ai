from flask import Flask, render_template_string, request, redirect, url_for, flash
import sqlite3
from datetime import date, datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = "local-dev-key-change-before-deployment"
DB_PATH = Path(__file__).with_name("bizassist.db")

STATUSES = ["New", "Contacted", "Follow-up", "Booked", "Won", "Lost"]

def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT DEFAULT '',
                business_need TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'New',
                follow_up_date TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

init_db()

BASE_STYLE = """
<style>
:root { --ink:#172033; --muted:#687386; --line:#e4e8ef; --blue:#3157d5; --bg:#f5f7fb; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 Arial,sans-serif; }
header { background:#fff; border-bottom:1px solid var(--line); padding:16px 22px; }
nav { max-width:1050px; margin:auto; display:flex; align-items:center; justify-content:space-between; gap:12px; }
.brand { font-weight:800; font-size:20px; text-decoration:none; color:var(--ink); }
nav a { color:var(--muted); text-decoration:none; margin-left:14px; }
main { max-width:1050px; margin:28px auto; padding:0 16px 35px; }
h1 { margin:0 0 8px; font-size:29px; }
h2 { font-size:19px; margin:0 0 14px; }
.muted { color:var(--muted); }
.grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin:22px 0; }
.card, .panel { background:#fff; border:1px solid var(--line); border-radius:14px; padding:18px; }
.metric { font-size:28px; font-weight:800; margin-top:6px; }
.two { display:grid; grid-template-columns:1.1fr .9fr; gap:16px; }
label { display:block; font-weight:700; margin:12px 0 5px; }
input, textarea, select { width:100%; padding:11px; border:1px solid #cfd6e2; border-radius:8px; font:inherit; background:#fff; }
textarea { min-height:100px; resize:vertical; }
button, .button { display:inline-block; background:var(--blue); color:#fff; border:0; border-radius:8px; padding:10px 14px; cursor:pointer; text-decoration:none; font-weight:700; margin-top:12px; }
.button.secondary { background:#eef2ff; color:#243b95; }
table { width:100%; border-collapse:collapse; }
th, td { text-align:left; padding:11px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; padding:4px 8px; border-radius:999px; background:#eef2ff; font-size:12px; }
.alert { padding:11px 14px; background:#eef8ef; border:1px solid #c8e6ce; border-radius:8px; margin-bottom:14px; }
textarea.output { min-height:190px; }
@media(max-width:720px) { .grid,.two { grid-template-columns:1fr; } nav { align-items:flex-start; flex-wrap:wrap; } nav a { margin-left:0; margin-right:12px; } table { font-size:13px; } th,td { padding:8px 4px; } }
</style>
"""

LAYOUT_START = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ title }} · BizAssist AI</title>""" + BASE_STYLE + """</head><body><header><nav><a class="brand" href="{{ url_for('dashboard') }}">✦ BizAssist AI</a><div><a href="{{ url_for('dashboard') }}">Dashboard</a><a href="{{ url_for('leads') }}">Customers</a><a href="{{ url_for('assistant') }}">Reply Assistant</a></div></nav></header><main>{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="alert">{{ message }}</div>{% endfor %}{% endwith %}"""

LAYOUT_END = """</main></body></html>"""

DASHBOARD = LAYOUT_START + """
<h1>Good business starts with good follow-up.</h1>
<p class="muted">Keep track of customer enquiries and prepare thoughtful replies in one place.</p>
<div class="grid">
 <div class="card"><div class="muted">Total customers</div><div class="metric">{{ total }}</div></div>
 <div class="card"><div class="muted">New enquiries</div><div class="metric">{{ new_count }}</div></div>
 <div class="card"><div class="muted">Follow-ups due</div><div class="metric">{{ due_count }}</div></div>
</div>
<div class="two">
 <section class="panel"><h2>Follow-ups to check</h2>
 {% if due %}
 <table><tr><th>Customer</th><th>Date</th><th>Status</th></tr>
 {% for lead in due %}<tr><td><a href="{{ url_for('edit_lead', lead_id=lead['id']) }}">{{ lead['name'] }}</a><br><span class="muted">{{ lead['business_need'] }}</span></td><td>{{ lead['follow_up_date'] }}</td><td><span class="pill">{{ lead['status'] }}</span></td></tr>{% endfor %}</table>
 {% else %}<p class="muted">No follow-ups due today or overdue. Add a customer and set a follow-up date.</p>{% endif %}
 <a class="button secondary" href="{{ url_for('leads') }}">View customers</a></section>
 <section class="panel"><h2>Reply Assistant</h2><p>Draft a polite customer reply, price response, booking confirmation, or follow-up message.</p><p class="muted">This starter version uses editable templates and does not send messages automatically.</p><a class="button" href="{{ url_for('assistant') }}">Create a reply</a><br><a class="button secondary" href="{{ url_for('new_lead') }}">+ Add customer</a></section>
</div>
""" + LAYOUT_END

LEADS_PAGE = LAYOUT_START + """
<h1>Customers and enquiries</h1><p class="muted">Use sample data while learning. Do not add sensitive customer information to a public demo.</p>
<p><a class="button" href="{{ url_for('new_lead') }}">+ Add customer</a></p>
<section class="panel"><table><tr><th>Name</th><th>Need</th><th>Status</th><th>Follow-up</th><th></th></tr>
{% for lead in leads %}<tr><td><strong>{{ lead['name'] }}</strong><br><span class="muted">{{ lead['contact'] }}</span></td><td>{{ lead['business_need'] }}</td><td><span class="pill">{{ lead['status'] }}</span></td><td>{{ lead['follow_up_date'] or 'Not set' }}</td><td><a href="{{ url_for('edit_lead', lead_id=lead['id']) }}">Edit</a></td></tr>{% else %}<tr><td colspan="5" class="muted">No customers yet. Add your first enquiry.</td></tr>{% endfor %}
</table></section>
""" + LAYOUT_END

LEAD_FORM = LAYOUT_START + """
<h1>{{ heading }}</h1><p class="muted">Fields marked required must be completed.</p>
<section class="panel"><form method="post">
<label for="name">Customer name *</label><input id="name" name="name" required maxlength="100" value="{{ lead['name'] if lead else '' }}">
<label for="contact">Contact (optional)</label><input id="contact" name="contact" maxlength="150" value="{{ lead['contact'] if lead else '' }}" placeholder="Email or phone">
<label for="business_need">What do they need?</label><input id="business_need" name="business_need" maxlength="200" value="{{ lead['business_need'] if lead else '' }}" placeholder="e.g. Asked about tutoring prices">
<label for="status">Status</label><select id="status" name="status">{% for status in statuses %}<option {% if lead and lead['status']==status %}selected{% elif not lead and status=='New' %}selected{% endif %}>{{ status }}</option>{% endfor %}</select>
<label for="follow_up_date">Follow-up date</label><input id="follow_up_date" name="follow_up_date" type="date" value="{{ lead['follow_up_date'] if lead else '' }}">
<label for="notes">Notes</label><textarea id="notes" name="notes" maxlength="2000">{{ lead['notes'] if lead else '' }}</textarea>
<button type="submit">Save customer</button> <a class="button secondary" href="{{ url_for('leads') }}">Cancel</a>
</form></section>
""" + LAYOUT_END

ASSISTANT = LAYOUT_START + """
<h1>Customer Reply Assistant</h1><p class="muted">Create a draft, review it, and copy it into your messaging app. Nothing is sent automatically.</p>
<div class="two">
<section class="panel"><h2>Tell us about the reply</h2><form method="post">
<label for="kind">Message type</label><select name="kind" id="kind">{% for value,label in kinds %}<option value="{{ value }}" {% if selected_kind==value %}selected{% endif %}>{{ label }}</option>{% endfor %}</select>
<label for="customer">Customer name</label><input name="customer" id="customer" maxlength="100" value="{{ customer }}" placeholder="e.g. Alex">
<label for="business">Business name</label><input name="business" id="business" maxlength="100" value="{{ business }}" placeholder="e.g. Bright Tutors">
<label for="details">Details to include</label><textarea name="details" id="details" maxlength="1000" placeholder="Price, service, date, next step...">{{ details }}</textarea>
<button type="submit">Generate draft</button>
</form></section>
<section class="panel"><h2>Your draft</h2><textarea class="output" id="output" readonly>{{ output }}</textarea><button type="button" onclick="copyDraft()">Copy draft</button><p class="muted" id="copy-status">Check all details before sending.</p></section>
</div>
<script>
function copyDraft() {
 const field = document.getElementById('output');
 field.select();
 field.setSelectionRange(0, 99999);
 if (navigator.clipboard && window.isSecureContext) {
   navigator.clipboard.writeText(field.value).then(() => document.getElementById('copy-status').textContent='Copied!').catch(() => document.getElementById('copy-status').textContent='Select the text and copy it manually.');
 } else {
   try { document.execCommand('copy'); document.getElementById('copy-status').textContent='Copied!'; }
   catch(e) { document.getElementById('copy-status').textContent='Select the text and copy it manually.'; }
 }
}
</script>
""" + LAYOUT_END

KINDS = [
    ("general", "Reply to a customer enquiry"),
    ("price", "Answer a pricing question"),
    ("booking", "Confirm a booking"),
    ("followup", "Follow up after an enquiry"),
    ("apology", "Apologize for a delay"),
]

def make_reply(kind, customer, business, details):
    """Create a careful, rule-based reply draft without inventing business facts."""
    import re

    customer = (customer or "").strip() or "there"
    business = (business or "").strip() or "our team"
    details = (details or "").strip()
    text = details.lower()

    greeting = f"Hi {customer},"
    signoff = f"\n\nBest regards,\n{business}"

    # Detect useful topics from the customer's question or the facts entered by the user.
    asks_price = kind == "price" or any(term in text for term in (
        "price", "how much", "cost", "rm ", "rm", "pricing", "cheap", "expensive"
    ))
    asks_booking = kind == "booking" or any(term in text for term in (
        "booking", "book", "reservation", "appointment", "date and time", "available slot"
    ))
    asks_product_options = any(term in text for term in (
        "size", "sizes", "colour", "color", "available", "availability", "stock", "in stock"
    ))
    asks_delivery = any(term in text for term in (
        "delivery", "shipping", "deliver", "postage", "when will it arrive"
    ))

    # A price is repeated only when the supplied details clearly include a currency amount.
    has_currency_amount = bool(re.search(r"\b(?:RM|MYR|USD|EUR|GBP|PKR)\s*\d+(?:[.,]\d{1,2})?\b|\b\d+(?:[.,]\d{1,2})?\s*(?:RM|MYR|USD|EUR|GBP|PKR)\b", details, re.I))

    if kind == "apology":
        message = details if details else "We are sorry for the inconvenience and appreciate your patience."
        body = f"I’m sorry for the inconvenience. {message} Please let us know if there is anything else we can do to help."

    elif kind == "followup":
        message = details if details else "I’m checking in about your recent enquiry. Would you like any more information or help with the next step?"
        body = f"I hope you’re doing well. I’m following up on your enquiry with {business}. {message} There’s no pressure—please reply whenever convenient."

    elif asks_price:
        if has_currency_amount:
            body = f"Thank you for your interest! Based on the details provided, the price information is: {details}. Please let us know if you’d like help with anything else."
        else:
            product = details if details else "the product or service you’re interested in"
            body = f"Thank you for asking about the price. I’d be happy to help with {product}. Could you confirm which product or service you mean? We’ll check the correct price for you."

    elif asks_booking:
        if details:
            body = f"Thank you for contacting {business} about your booking. Here are the details provided: {details}. Please note that the booking should be confirmed by our team before it is considered final."
        else:
            body = f"Thank you for your booking enquiry with {business}. Please share your preferred date, time, and the service you need so we can check availability."

    elif asks_product_options:
        if details and any(term in text for term in ("we have", "available in", "in stock", "sizes are", "colours are", "colors are")):
            body = f"Thank you for your interest! Here is the information currently provided: {details}. Let us know which option you prefer, and we’ll help with the next step."
        else:
            body = f"Thank you for your interest! We can help you check the available sizes, colours, or stock for the product you want. Please tell us the exact product and your preferred option so we can confirm it."

    elif asks_delivery:
        if details and any(term in text for term in ("delivery takes", "arrives in", "shipping fee", "delivery fee", "days")):
            body = f"Thank you for asking about delivery. Here is the information provided: {details}. Please contact us if you need help with your order."
        else:
            body = f"Thank you for asking about delivery. Please share your product and delivery location so our team can confirm the available delivery options, fees, and estimated time."

    elif kind == "booking":
        body = f"Thank you for contacting {business}. {details or 'Please share your preferred date and time so we can check availability.'}"

    else:
        if details:
            body = f"Thank you for contacting {business}. I understand your enquiry is about: {details}. We’ll be happy to help. If you have a specific question, please send it to us and we’ll guide you."
        else:
            body = f"Thank you for contacting {business}. We’re happy to help. Could you share a little more about what you need so we can guide you?"

    return f"{greeting} {body}\n\nPlease let us know if you have any other questions." + signoff

@app.route("/")
def dashboard():
    today = date.today().isoformat()
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        new_count = db.execute("SELECT COUNT(*) FROM leads WHERE status='New'").fetchone()[0]
        due_count = db.execute("""SELECT COUNT(*) FROM leads WHERE follow_up_date != '' AND follow_up_date <= ? AND status NOT IN ('Won','Lost')""", (today,)).fetchone()[0]
        due = db.execute("""SELECT * FROM leads WHERE follow_up_date != '' AND follow_up_date <= ? AND status NOT IN ('Won','Lost') ORDER BY follow_up_date ASC LIMIT 8""", (today,)).fetchall()
    return render_template_string(DASHBOARD, title="Dashboard", total=total, new_count=new_count, due_count=due_count, due=due)

@app.route("/leads")
def leads():
    with get_db() as db:
        rows = db.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    return render_template_string(LEADS_PAGE, title="Customers", leads=rows)

@app.route("/leads/new", methods=["GET", "POST"])
def new_lead():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Customer name is required.")
            return redirect(url_for("new_lead"))
        status = request.form.get("status", "New")
        if status not in STATUSES:
            status = "New"
        with get_db() as db:
            db.execute("""INSERT INTO leads (name,contact,business_need,status,follow_up_date,notes,created_at)
                          VALUES (?,?,?,?,?,?,?)""",
                       (name, request.form.get("contact", "").strip(),
                        request.form.get("business_need", "").strip(), status,
                        request.form.get("follow_up_date", "").strip(),
                        request.form.get("notes", "").strip(), datetime.now().isoformat(timespec="seconds")))
        flash("Customer saved.")
        return redirect(url_for("leads"))
    return render_template_string(LEAD_FORM, title="Add customer", heading="Add a customer", lead=None, statuses=STATUSES)

@app.route("/leads/<int:lead_id>/edit", methods=["GET", "POST"])
def edit_lead(lead_id):
    with get_db() as db:
        lead = db.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    if lead is None:
        flash("Customer not found.")
        return redirect(url_for("leads"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        status = request.form.get("status", "New")
        if not name or status not in STATUSES:
            flash("Please enter a customer name and valid status.")
            return redirect(url_for("edit_lead", lead_id=lead_id))
        with get_db() as db:
            db.execute("""UPDATE leads SET name=?,contact=?,business_need=?,status=?,follow_up_date=?,notes=? WHERE id=?""",
                       (name, request.form.get("contact", "").strip(),
                        request.form.get("business_need", "").strip(), status,
                        request.form.get("follow_up_date", "").strip(),
                        request.form.get("notes", "").strip(), lead_id))
        flash("Customer updated.")
        return redirect(url_for("leads"))
    return render_template_string(LEAD_FORM, title="Edit customer", heading="Edit customer", lead=lead, statuses=STATUSES)

@app.route("/assistant", methods=["GET", "POST"])
def assistant():
    values = {"kind": "general", "customer": "", "business": "", "details": ""}
    output = "Your message draft will appear here."
    if request.method == "POST":
        for key in values:
            values[key] = request.form.get(key, values[key]).strip()[:1000]
        if values["kind"] not in [item[0] for item in KINDS]:
            values["kind"] = "general"
        output = make_reply(values["kind"], values["customer"], values["business"], values["details"])
    return render_template_string(ASSISTANT, title="Reply Assistant", kinds=KINDS,
                                  selected_kind=values["kind"], customer=values["customer"],
                                  business=values["business"], details=values["details"], output=output)

if __name__ == "__main__":
    # Local development only. Do not use Flask's debug server for public production hosting.
    app.run(debug=True, host="127.0.0.1", port=5000)
