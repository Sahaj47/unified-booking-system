# models.py — SQLAlchemy ORM models.
# All relationships declared here so routes stay clean.

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Department(db.Model):
    __tablename__ = 'departments'
    dept_id   = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String(100), unique=True, nullable=False)


class Role(db.Model):
    __tablename__ = 'roles'
    role_id   = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)


class User(db.Model):
    __tablename__ = 'users'
    user_id    = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(100), unique=True, nullable=False)
    password   = db.Column(db.String(100), nullable=False)   # plain text — demo only
    dept_id    = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    role_id    = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship('Department', backref='users')
    role       = db.relationship('Role', backref='users')


class ResourceType(db.Model):
    __tablename__ = 'resource_types'
    type_id   = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(100), unique=True, nullable=False)


class Resource(db.Model):
    __tablename__ = 'resources'
    resource_id       = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(100), nullable=False)
    type_id           = db.Column(db.Integer, db.ForeignKey('resource_types.type_id'), nullable=False)
    dept_id           = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    capacity          = db.Column(db.Integer, default=1)
    requires_approval = db.Column(db.Boolean, default=False)
    is_active         = db.Column(db.Boolean, default=True)

    resource_type    = db.relationship('ResourceType', backref='resources')
    department       = db.relationship('Department', backref='resources')
    # uselist=False — each resource has at most one approval rule
    approval_rule    = db.relationship('ResourceApprovalRule', backref='resource', uselist=False)
    faculty_mappings = db.relationship('ResourceFacultyMapping', backref='resource',
                                       cascade='all, delete-orphan')


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    slot_id    = db.Column(db.Integer, primary_key=True)
    label      = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time   = db.Column(db.Time, nullable=False)


# ── New approval-system tables ─────────────────────────────────

class ResourceApprovalRule(db.Model):
    """Stores whether a resource needs ANY (OR) or ALL (AND) faculty approvals."""
    __tablename__ = 'resource_approval_rules'
    rule_id     = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer,
                            db.ForeignKey('resources.resource_id'),
                            unique=True, nullable=False)
    rule_type   = db.Column(db.Enum('ANY', 'ALL', name="booking_status_enum1"), nullable=False, default='ANY')


class ResourceFacultyMapping(db.Model):
    """Maps faculty users to resources they are responsible for approving."""
    __tablename__ = 'resource_faculty_mappings'
    mapping_id  = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer,
                            db.ForeignKey('resources.resource_id'), nullable=False)
    faculty_id  = db.Column(db.Integer,
                            db.ForeignKey('users.user_id'), nullable=False)

    faculty = db.relationship('User', backref='faculty_mappings')


# ── Modified core tables ───────────────────────────────────────

class Booking(db.Model):
    __tablename__ = 'bookings'
    booking_id        = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    resource_id       = db.Column(db.Integer, db.ForeignKey('resources.resource_id'), nullable=False)
    slot_id           = db.Column(db.Integer, db.ForeignKey('time_slots.slot_id'), nullable=False)
    booking_date      = db.Column(db.Date, nullable=False)
    status            = db.Column(
        db.Enum('pending', 'approved', 'rejected', 'cancelled', name="booking_status_enum2"),
        default='pending'
    )
    requires_approval = db.Column(db.Boolean, default=False)
    rejection_reason  = db.Column(db.Text, nullable=True)   # shown to the booking user
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    user      = db.relationship('User', backref='bookings')
    resource  = db.relationship('Resource', backref='bookings')
    slot      = db.relationship('TimeSlot', backref='bookings')
    approvals = db.relationship('Approval', backref='booking',
                                cascade='all, delete-orphan')


class Approval(db.Model):
    """One row per faculty per booking — tracks individual faculty decisions."""
    __tablename__ = 'approvals'
    approval_id = db.Column(db.Integer, primary_key=True)
    booking_id  = db.Column(db.Integer, db.ForeignKey('bookings.booking_id'), nullable=False)
    faculty_id  = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status      = db.Column(db.Enum('pending', 'approved', 'rejected', name="booking_status_enum3"), default='pending')
    reason      = db.Column(db.Text, nullable=True)
    actioned_at = db.Column(db.DateTime, nullable=True)

    faculty = db.relationship('User', backref='approval_actions')


class UsageLog(db.Model):
    __tablename__ = 'usage_logs'
    log_id       = db.Column(db.Integer, primary_key=True)
    booking_id   = db.Column(db.Integer,
                             db.ForeignKey('bookings.booking_id'),
                             unique=True, nullable=False)
    actual_start = db.Column(db.DateTime, nullable=True)
    actual_end   = db.Column(db.DateTime, nullable=True)
    logged_at    = db.Column(db.DateTime, default=datetime.utcnow)