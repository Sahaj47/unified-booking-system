# ── app.py ────────────────────────────────────────────────────
# All Flask routes for the Unified Resource Booking System.
# Uses raw SQL only — no ORM.

import json
from functools import wraps

import requests
from flask import (Flask, flash, redirect, render_template,
                   request, session, url_for)

import db
from config import ANTHROPIC_API_KEY, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ── Auth decorators ───────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role_id') != 3:
            return render_template('base.html',
                                   error="Access denied: Admins only."), 403
        return f(*args, **kwargs)
    return decorated


# ── Auth routes ───────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        conn   = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, name, role_id FROM users "
            "WHERE email = %s AND password = %s",
            (email, password)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['name']    = user['name']
            session['role_id'] = user['role_id']
            return redirect(url_for('dashboard'))
        error = 'Invalid email or password.'

    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    conn   = db.get_connection()
    cursor = conn.cursor(dictionary=True)

    # Load departments and roles for the form dropdowns
    # Roles: only student (1) and faculty (2) — admins are created manually
    cursor.execute("SELECT dept_id, dept_name FROM departments ORDER BY dept_name")
    departments = cursor.fetchall()

    cursor.execute(
        "SELECT role_id, role_name FROM roles WHERE role_name != 'admin'"
    )
    roles = cursor.fetchall()

    error = message = None

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        dept_id  = request.form.get('dept_id')
        role_id  = request.form.get('role_id')

        # Server-side validation
        if not all([name, email, password, dept_id, role_id]):
            error = "All fields are required."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            # Check if email is already registered
            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s", (email,)
            )
            if cursor.fetchone():
                error = "An account with this email already exists."
            else:
                try:
                    cursor.execute(
                        "INSERT INTO users (name, email, password, dept_id, role_id) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (name, email, password, dept_id, role_id)
                    )
                    conn.commit()
                    message = "Account created! You can now log in."
                except Exception as exc:
                    conn.rollback()
                    error = f"Registration failed: {exc}"

    cursor.close()
    conn.close()
    return render_template('signup.html',
                           departments=departments,
                           roles=roles,
                           error=error,
                           message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Dashboard ─────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    conn   = db.get_connection()
    cursor = conn.cursor(dictionary=True)

    if session['role_id'] == 3:          # admin sees everything
        cursor.execute(
            "SELECT * FROM booking_schedule "
            "ORDER BY booking_date DESC, start_time"
        )
    else:                                # users see their own bookings
        cursor.execute(
            "SELECT * FROM booking_schedule "
            "WHERE user_id = %s "
            "ORDER BY booking_date DESC, start_time",
            (session['user_id'],)
        )

    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', bookings=bookings)


# ── Booking form ──────────────────────────────────────────────

@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    conn   = db.get_connection()
    cursor = conn.cursor(dictionary=True)

    # Always load form options
    cursor.execute(
        "SELECT resource_id, name, capacity, requires_approval "
        "FROM resources WHERE is_active = 1"
    )
    resources = cursor.fetchall()

    cursor.execute(
        "SELECT slot_id, label, start_time, end_time "
        "FROM time_slots ORDER BY start_time"
    )
    slots = cursor.fetchall()

    message = error = None

    if request.method == 'POST':
        resource_id  = request.form.get('resource_id')
        slot_id      = request.form.get('slot_id')
        booking_date = request.form.get('booking_date')

        # Determine initial status from resource flag
        cursor.execute(
            "SELECT requires_approval FROM resources "
            "WHERE resource_id = %s", (resource_id,)
        )
        resource = cursor.fetchone()
        req_approval = resource['requires_approval']
        status       = 'pending' if req_approval else 'approved'

        try:
            cursor.execute(
                "INSERT INTO bookings "
                "(user_id, resource_id, slot_id, booking_date, "
                " status, requires_approval) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (session['user_id'], resource_id, slot_id,
                 booking_date, status, req_approval)
            )
            conn.commit()

            # Auto-log usage for instantly approved bookings
            if status == 'approved':
                booking_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO usage_logs (booking_id) VALUES (%s)",
                    (booking_id,)
                )
                conn.commit()

            message = ("Booking confirmed!" if status == 'approved'
                       else "Booking submitted — awaiting admin approval.")

        except Exception as exc:
            conn.rollback()
            msg = str(exc)
            error = ("Conflict: that resource is already booked for this "
                     "slot and date." if "already booked" in msg else msg)

    cursor.close()
    conn.close()
    return render_template('book.html',
                           resources=resources, slots=slots,
                           message=message, error=error)


# ── Admin / approval page ─────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin():
    conn   = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT b.booking_id, u.name AS user_name, "
        "       r.name AS resource_name, "
        "       ts.label AS time_slot, b.booking_date, b.status "
        "FROM bookings b "
        "JOIN users      u  ON b.user_id     = u.user_id "
        "JOIN resources  r  ON b.resource_id = r.resource_id "
        "JOIN time_slots ts ON b.slot_id     = ts.slot_id "
        "WHERE b.requires_approval = 1 AND b.status = 'pending' "
        "ORDER BY b.created_at"
    )
    pending = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin.html', pending=pending)


@app.route('/approve/<int:booking_id>', methods=['POST'])
@login_required
@admin_required
def approve(booking_id):
    action  = request.form.get('action')   # 'approved' or 'rejected'
    remarks = request.form.get('remarks', '')

    conn   = db.get_connection()
    cursor = conn.cursor()

    # Update booking status
    cursor.execute(
        "UPDATE bookings SET status = %s WHERE booking_id = %s",
        (action, booking_id)
    )

    # Record in approvals table
    cursor.execute(
        "INSERT INTO approvals (booking_id, approved_by, action, remarks) "
        "VALUES (%s, %s, %s, %s)",
        (booking_id, session['user_id'], action, remarks)
    )

    # Log usage when approved
    if action == 'approved':
        cursor.execute(
            "INSERT INTO usage_logs (booking_id) VALUES (%s)",
            (booking_id,)
        )

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))


# ── Summary page (uses VIEW + stored procedure) ───────────────

@app.route('/summary')
@login_required
def summary():
    conn    = db.get_connection()
    cursor1 = conn.cursor(dictionary=True)

    # Use the booking_schedule VIEW
    cursor1.execute(
        "SELECT * FROM booking_schedule "
        "ORDER BY booking_date DESC, start_time LIMIT 50"
    )
    bookings = cursor1.fetchall()
    cursor1.close()

    # Call stored procedure for resource_id = 1 (CS Lab A)
    cursor2 = conn.cursor()
    cursor2.callproc('GetBookingsByResource', [1])
    proc_cols   = ['booking_id', 'user_name', 'resource_name',
                   'slot', 'booking_date', 'status']
    proc_results = []
    for result in cursor2.stored_results():
        for row in result.fetchall():
            proc_results.append(dict(zip(proc_cols, row)))
    cursor2.close()

    conn.close()
    return render_template('summary.html',
                           bookings=bookings,
                           proc_results=proc_results)


# ── AI Insights (auxiliary feature) ──────────────────────────

@app.route('/ai-insights')
@login_required
def ai_insights():
    conn   = db.get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM bookings")
    total = cursor.fetchone()['total']

    cursor.execute(
        "SELECT status, COUNT(*) AS count FROM bookings GROUP BY status"
    )
    status_counts = cursor.fetchall()

    cursor.execute(
        "SELECT r.name, COUNT(*) AS bookings "
        "FROM bookings b JOIN resources r ON b.resource_id = r.resource_id "
        "GROUP BY r.resource_id ORDER BY bookings DESC LIMIT 3"
    )
    top_resources = cursor.fetchall()

    cursor.close()
    conn.close()

    stats      = {'total': total,
                  'by_status': status_counts,
                  'top_resources': top_resources}
    ai_summary = _generate_summary(stats)

    return render_template('ai_insights.html',
                           stats=stats, ai_summary=ai_summary)


# def _generate_summary(stats):
#     """Call Anthropic API; fall back to rule-based summary if no key."""
#     if not ANTHROPIC_API_KEY:
#         return _local_summary(stats)

#     prompt = (
#         "You are an assistant for a college campus resource booking system.\n"
#         f"Total bookings: {stats['total']}\n"
#         f"Status breakdown: {json.dumps(stats['by_status'], default=str)}\n"
#         f"Top 3 booked resources: {json.dumps(stats['top_resources'], default=str)}\n\n"
#         "Write a concise 3–4 sentence admin dashboard summary highlighting "
#         "usage trends, pending items, and any notable patterns."
#     )

#     try:
#         resp = requests.post(
#             'https://api.anthropic.com/v1/messages',
#             headers={
#                 'x-api-key':          ANTHROPIC_API_KEY,
#                 'anthropic-version':  '2023-06-01',
#                 'content-type':       'application/json'
#             },
#             json={
#                 'model':      'claude-sonnet-4-20250514',
#                 'max_tokens': 300,
#                 'messages':   [{'role': 'user', 'content': prompt}]
#             },
#             timeout=15
#         )
#         return resp.json()['content'][0]['text']
#     except Exception:
#         return _local_summary(stats)


def _generate_summary(stats):
    """Call Anthropic API; fall back to rule-based summary if no key set."""
    if not ANTHROPIC_API_KEY:
        return _local_summary(stats)

    prompt = (
        "You are an assistant for a college campus resource booking system.\n"
        f"Total bookings: {stats['total']}\n"
        f"Status breakdown: {json.dumps(stats['by_status'], default=str)}\n"
        f"Top 3 booked resources: {json.dumps(stats['top_resources'], default=str)}\n\n"
        "Write a concise 3–4 sentence admin dashboard summary highlighting "
        "usage trends, pending items, and any notable patterns."
    )

    try:
        resp = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key':         ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type':      'application/json'
            },
            json={
                'model':     'claude-sonnet-4-6',   # ← fixed model name
                'max_tokens': 300,
                'messages':  [{'role': 'user', 'content': prompt}]
            },
            timeout=15
        )

        resp.raise_for_status()   # raises on 4xx/5xx so you see the real error
        data = resp.json()

        # Surface any API-level error (e.g. invalid key, rate limit)
        if 'error' in data:
            return f"[API error] {data['error'].get('message', data['error'])}"

        return data['content'][0]['text']

    except requests.exceptions.HTTPError as e:
        return f"[HTTP error {e.response.status_code}] {e.response.text[:200]}"
    except requests.exceptions.ConnectionError:
        return "[Connection error] Could not reach the Anthropic API. Check your internet connection."
    except requests.exceptions.Timeout:
        return "[Timeout] The Anthropic API took too long to respond."
    except Exception as e:
        return f"[Unexpected error] {str(e)}"

def _local_summary(stats):
    """Rule-based fallback — no external API needed."""
    pending  = next((s['count'] for s in stats['by_status']
                     if s['status'] == 'pending'), 0)
    approved = next((s['count'] for s in stats['by_status']
                     if s['status'] == 'approved'), 0)
    top = stats['top_resources'][0]['name'] if stats['top_resources'] else 'N/A'
    return (
        f"The system has {stats['total']} total bookings recorded. "
        f"{approved} bookings are confirmed and {pending} are awaiting approval. "
        f"The most frequently booked resource is '{top}'. "
        "Overall resource utilization appears steady across departments."
    )

if __name__ == '__main__':
    app.run(debug=True)
