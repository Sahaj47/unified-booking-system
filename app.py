# app.py — only the app factory section changes.
# All routes, decorators, and helpers are UNCHANGED.

import json
import requests
from datetime import datetime
from functools import wraps

from flask import (Flask, flash, redirect, render_template,
                   request, session, url_for)
from sqlalchemy import func

# WhiteNoise serves /static/ directly from gunicorn — no Nginx needed on Render
from whitenoise import WhiteNoise

from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY, ANTHROPIC_API_KEY
from models import (db, Department, Role, User, ResourceType, Resource,
                    TimeSlot, ResourceApprovalRule, ResourceFacultyMapping,
                    Booking, Approval, UsageLog)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI']        = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Serve static files via WhiteNoise (works without a reverse proxy on Render)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static')

# ── Database initialisation ───────────────────────────────────
# db.create_all() is safe to call on every startup:
# SQLAlchemy checks IF NOT EXISTS before creating any table.
# This replaces the manual `python seed.py` step for table creation.
# Seeding (inserting rows) still requires running seed.py once manually.

with app.app_context():
    db.create_all()

# ═══════════════════════════════════════════════════════════════
# DECORATORS
# ═══════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def faculty_required(f):
    """Allows faculty (role 2) and augsd (role 3)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role_id') not in [2, 3]:
            flash('Faculty access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def augsd_required(f):
    """Allows only the augsd superuser (role 3)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role_id') != 3:
            flash('Admin (augsd) access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.user_id
            session['name']    = user.name
            session['role_id'] = user.role_id
            return redirect(url_for('dashboard'))
        error = 'Invalid email or password.'
    return render_template('login.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # augsd role cannot be self-registered
    departments = Department.query.order_by(Department.dept_name).all()
    roles       = Role.query.filter(Role.role_name != 'augsd').all()
    error = message = None

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        dept_id  = request.form.get('dept_id')
        role_id  = request.form.get('role_id')

        if not all([name, email, password, dept_id, role_id]):
            error = 'All fields are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.query.filter_by(email=email).first():
            error = 'An account with this email already exists.'
        else:
            try:
                db.session.add(User(name=name, email=email, password=password,
                                    dept_id=dept_id, role_id=role_id))
                db.session.commit()
                message = 'Account created! You can now sign in.'
            except Exception as e:
                db.session.rollback()
                error = f'Registration failed: {e}'

    return render_template('signup.html', departments=departments, roles=roles,
                           error=error, message=message)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    if session['role_id'] == 3:   # augsd sees everything
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    else:
        bookings = (Booking.query
                    .filter_by(user_id=session['user_id'])
                    .order_by(Booking.created_at.desc())
                    .all())
    return render_template('dashboard.html', bookings=bookings)


# ═══════════════════════════════════════════════════════════════
# BOOKING
# ═══════════════════════════════════════════════════════════════

@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    resources = Resource.query.filter_by(is_active=True).all()
    slots     = TimeSlot.query.order_by(TimeSlot.start_time).all()

    # Build approval-info dict passed to JS for dynamic hints
    approval_info = {}
    for r in resources:
        if r.requires_approval:
            rule = r.approval_rule
            approval_info[r.resource_id] = {
                'rule_type':    rule.rule_type if rule else 'ANY',
                'faculty_count': len(r.faculty_mappings)
            }

    error = message = None

    if request.method == 'POST':
        resource_id  = int(request.form['resource_id'])
        slot_id      = int(request.form['slot_id'])
        booking_date = request.form['booking_date']
        resource     = Resource.query.get_or_404(resource_id)

        # Conflict check (replaces the old DB trigger)
        conflict = (Booking.query
                    .filter_by(resource_id=resource_id,
                               slot_id=slot_id,
                               booking_date=booking_date)
                    .filter(Booking.status.in_(['pending', 'approved']))
                    .first())
        if conflict:
            error = 'Conflict: this resource is already booked for that slot and date.'
        else:
            req_approval = resource.requires_approval
            status       = 'pending' if req_approval else 'approved'
            try:
                booking = Booking(
                    user_id=session['user_id'],
                    resource_id=resource_id,
                    slot_id=slot_id,
                    booking_date=booking_date,
                    status=status,
                    requires_approval=req_approval
                )
                db.session.add(booking)
                db.session.flush()   # get booking_id before commit

                # Create one Approval row per mapped faculty
                if req_approval:
                    for mapping in resource.faculty_mappings:
                        db.session.add(Approval(
                            booking_id=booking.booking_id,
                            faculty_id=mapping.faculty_id,
                            status='pending'
                        ))

                # Auto-log immediately approved bookings
                if status == 'approved':
                    db.session.add(UsageLog(booking_id=booking.booking_id))

                db.session.commit()
                message = ('Booking confirmed!' if status == 'approved'
                           else 'Booking submitted — awaiting faculty approval.')
            except Exception as e:
                db.session.rollback()
                error = f'Booking failed: {e}'

    return render_template('book.html', resources=resources, slots=slots,
                           approval_info=approval_info,
                           error=error, message=message)


# ═══════════════════════════════════════════════════════════════
# FACULTY DASHBOARD
# ═══════════════════════════════════════════════════════════════

@app.route('/faculty')
@faculty_required
def faculty_dashboard():
    fid = session['user_id']

    # Pending approvals where this faculty has not yet acted
    pending = (Approval.query
               .filter_by(faculty_id=fid, status='pending')
               .join(Booking)
               .filter(Booking.status == 'pending')
               .all())

    # Action history (last 20)
    history = (Approval.query
               .filter(Approval.faculty_id == fid,
                       Approval.status != 'pending')
               .order_by(Approval.actioned_at.desc())
               .limit(20)
               .all())

    # Resources this faculty is mapped to
    assigned = ResourceFacultyMapping.query.filter_by(faculty_id=fid).all()

    return render_template('faculty_dashboard.html',
                           pending=pending, history=history, assigned=assigned)


@app.route('/faculty/action/<int:approval_id>', methods=['POST'])
@faculty_required
def faculty_action(approval_id):
    action = request.form.get('action')   # 'approved' or 'rejected'
    reason = request.form.get('reason', '').strip()

    approval = Approval.query.get_or_404(approval_id)
    if approval.faculty_id != session['user_id']:
        flash('Unauthorised action.', 'danger')
        return redirect(url_for('faculty_dashboard'))

    approval.status      = action
    approval.reason      = reason or None
    approval.actioned_at = datetime.utcnow()
    db.session.commit()

    _process_approval_outcome(approval.booking_id)

    flash(f'Booking #{approval.booking_id} marked as {action}.', 'success')
    return redirect(url_for('faculty_dashboard'))


# ═══════════════════════════════════════════════════════════════
# APPROVAL LOGIC HELPER
# ═══════════════════════════════════════════════════════════════

def _process_approval_outcome(booking_id):
    """
    Re-evaluate booking status after any faculty action.

    Rules:
      ANY  → one 'approved' row is sufficient to approve the booking.
      ALL  → every row must be 'approved' before the booking is approved.
      Any single 'rejected' row → booking is immediately rejected.
    """
    booking       = Booking.query.get(booking_id)
    rule          = ResourceApprovalRule.query.filter_by(
                        resource_id=booking.resource_id).first()
    all_approvals = Approval.query.filter_by(booking_id=booking_id).all()

    if not all_approvals:
        return

    rejected_list = [a for a in all_approvals if a.status == 'rejected']
    approved_list = [a for a in all_approvals if a.status == 'approved']

    if rejected_list:
        booking.status           = 'rejected'
        booking.rejection_reason = rejected_list[0].reason or 'No reason provided.'
    elif not rule:
        # No rule set — default ANY behaviour
        if approved_list:
            booking.status = 'approved'
    elif rule.rule_type == 'ANY' and approved_list:
        booking.status = 'approved'
    elif rule.rule_type == 'ALL' and len(approved_list) == len(all_approvals):
        booking.status = 'approved'

    if booking.status == 'approved':
        if not UsageLog.query.filter_by(booking_id=booking_id).first():
            db.session.add(UsageLog(booking_id=booking_id))

    db.session.commit()


# ═══════════════════════════════════════════════════════════════
# ADMIN PANEL (augsd only)
# ═══════════════════════════════════════════════════════════════

@app.route('/admin')
@augsd_required
def admin():
    all_bookings   = Booking.query.order_by(Booking.created_at.desc()).all()
    all_resources  = Resource.query.all()
    all_faculty    = User.query.filter_by(role_id=2).all()
    resource_types = ResourceType.query.all()
    departments    = Department.query.all()

    # Dicts for quick template lookup
    rules        = {r.resource_id: r for r in ResourceApprovalRule.query.all()}
    faculty_maps = {}
    for m in ResourceFacultyMapping.query.all():
        faculty_maps.setdefault(m.resource_id, []).append(m)

    return render_template('admin.html',
                           all_bookings=all_bookings,
                           all_resources=all_resources,
                           all_faculty=all_faculty,
                           resource_types=resource_types,
                           departments=departments,
                           rules=rules,
                           faculty_maps=faculty_maps)


@app.route('/admin/resource/add', methods=['POST'])
@augsd_required
def admin_add_resource():
    name         = request.form['name'].strip()
    type_id      = request.form['type_id']
    dept_id      = request.form['dept_id']
    capacity     = request.form.get('capacity', 1)
    req_approval = bool(request.form.get('requires_approval'))

    db.session.add(Resource(name=name, type_id=type_id, dept_id=dept_id,
                            capacity=capacity, requires_approval=req_approval))
    db.session.commit()
    flash(f'Resource "{name}" added.', 'success')
    return redirect(url_for('admin') + '#tab-resources')


@app.route('/admin/resource/toggle/<int:resource_id>', methods=['POST'])
@augsd_required
def admin_toggle_resource(resource_id):
    r = Resource.query.get_or_404(resource_id)
    r.is_active = not r.is_active
    db.session.commit()
    flash(f'Resource "{r.name}" {"activated" if r.is_active else "deactivated"}.', 'info')
    return redirect(url_for('admin') + '#tab-resources')


@app.route('/admin/rule/set', methods=['POST'])
@augsd_required
def admin_set_rule():
    resource_id = int(request.form['resource_id'])
    rule_type   = request.form['rule_type']

    rule = ResourceApprovalRule.query.filter_by(resource_id=resource_id).first()
    if rule:
        rule.rule_type = rule_type
    else:
        db.session.add(ResourceApprovalRule(resource_id=resource_id, rule_type=rule_type))
    db.session.commit()
    flash('Approval rule updated.', 'success')
    return redirect(url_for('admin') + '#tab-rules')


@app.route('/admin/rule/faculty/add', methods=['POST'])
@augsd_required
def admin_add_faculty():
    resource_id = int(request.form['resource_id'])
    faculty_id  = int(request.form['faculty_id'])

    exists = ResourceFacultyMapping.query.filter_by(
        resource_id=resource_id, faculty_id=faculty_id).first()
    if not exists:
        db.session.add(ResourceFacultyMapping(resource_id=resource_id,
                                              faculty_id=faculty_id))
        db.session.commit()
        flash('Faculty assigned to resource.', 'success')
    else:
        flash('Already assigned.', 'warning')
    return redirect(url_for('admin') + '#tab-rules')


@app.route('/admin/rule/faculty/remove/<int:mapping_id>', methods=['POST'])
@augsd_required
def admin_remove_faculty(mapping_id):
    m = ResourceFacultyMapping.query.get_or_404(mapping_id)
    db.session.delete(m)
    db.session.commit()
    flash('Faculty removed from resource.', 'info')
    return redirect(url_for('admin') + '#tab-rules')


@app.route('/admin/override/<int:booking_id>', methods=['POST'])
@augsd_required
def admin_override(booking_id):
    action = request.form['action']   # 'approved' or 'rejected'
    reason = request.form.get('reason', 'Override by augsd.').strip()

    booking = Booking.query.get_or_404(booking_id)
    booking.status = action
    if action == 'rejected':
        booking.rejection_reason = reason

    # Stamp all pending approvals so the audit trail is consistent
    for a in booking.approvals:
        if a.status == 'pending':
            a.status      = action
            a.reason      = f'Override by augsd: {reason}'
            a.actioned_at = datetime.utcnow()

    if action == 'approved':
        if not UsageLog.query.filter_by(booking_id=booking_id).first():
            db.session.add(UsageLog(booking_id=booking_id))

    db.session.commit()
    flash(f'Booking #{booking_id} overridden to {action}.', 'success')
    return redirect(url_for('admin'))


# ═══════════════════════════════════════════════════════════════
# SUMMARY (augsd only)
# ═══════════════════════════════════════════════════════════════

@app.route('/summary')
@augsd_required
def summary():
    total       = Booking.query.count()
    by_status   = (db.session.query(Booking.status,
                                    func.count(Booking.booking_id))
                   .group_by(Booking.status).all())
    top_resources = (db.session.query(Resource.name,
                                      func.count(Booking.booking_id))
                     .join(Booking)
                     .group_by(Resource.resource_id)
                     .order_by(func.count(Booking.booking_id).desc())
                     .limit(5).all())
    recent = Booking.query.order_by(Booking.created_at.desc()).limit(50).all()

    return render_template('summary.html',
                           total=total, by_status=by_status,
                           top_resources=top_resources, recent=recent)


# ═══════════════════════════════════════════════════════════════
# AI INSIGHTS
# ═══════════════════════════════════════════════════════════════

@app.route('/ai-insights')
@login_required
def ai_insights():
    total     = Booking.query.count()
    by_status = (db.session.query(Booking.status,
                                  func.count(Booking.booking_id))
                 .group_by(Booking.status).all())
    top_resources = (db.session.query(Resource.name,
                                      func.count(Booking.booking_id))
                     .join(Booking)
                     .group_by(Resource.resource_id)
                     .order_by(func.count(Booking.booking_id).desc())
                     .limit(3).all())

    stats = {
        'total':         total,
        'by_status':     [{'status': s, 'count': c} for s, c in by_status],
        'top_resources': [{'name': n, 'bookings': c} for n, c in top_resources],
    }
    return render_template('ai_insights.html',
                           stats=stats, ai_summary=_generate_summary(stats))


def _generate_summary(stats):
    if not ANTHROPIC_API_KEY:
        return _local_summary(stats)
    prompt = (
        "You are an assistant for a college campus resource booking system.\n"
        f"Total bookings: {stats['total']}\n"
        f"Status breakdown: {json.dumps(stats['by_status'])}\n"
        f"Top resources: {json.dumps(stats['top_resources'])}\n\n"
        "Write a concise 3–4 sentence admin dashboard summary highlighting "
        "usage trends, pending items, and any notable patterns."
    )
    try:
        resp = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={'x-api-key': ANTHROPIC_API_KEY,
                     'anthropic-version': '2023-06-01',
                     'content-type': 'application/json'},
            json={'model': 'claude-sonnet-4-6', 'max_tokens': 300,
                  'messages': [{'role': 'user', 'content': prompt}]},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        if 'error' in data:
            return f"[API error] {data['error'].get('message', data['error'])}"
        return data['content'][0]['text']
    except requests.exceptions.HTTPError as e:
        return f"[HTTP {e.response.status_code}] {e.response.text[:200]}"
    except Exception as e:
        return f"[Error] {e}"


def _local_summary(stats):
    pending  = next((s['count'] for s in stats['by_status'] if s['status'] == 'pending'), 0)
    approved = next((s['count'] for s in stats['by_status'] if s['status'] == 'approved'), 0)
    top      = stats['top_resources'][0]['name'] if stats['top_resources'] else 'N/A'
    return (f"The system has {stats['total']} total bookings recorded. "
            f"{approved} are confirmed and {pending} are awaiting approval. "
            f"The most frequently booked resource is '{top}'. "
            "Overall resource utilisation appears steady across departments.")
            