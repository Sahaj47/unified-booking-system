# seed.py — run ONCE to create tables and insert demo data.
# Usage: python seed.py

from datetime import time
from app import app
from models import (db, Department, Role, User, ResourceType, Resource,
                    TimeSlot, ResourceApprovalRule, ResourceFacultyMapping)

with app.app_context():
    db.create_all()

    if Role.query.first():
        print('Already seeded — skipping.')
        raise SystemExit(0)

    # ── Roles ──────────────────────────────────────────────────
    student = Role(role_name='student')
    faculty = Role(role_name='faculty')
    augsd   = Role(role_name='augsd')
    db.session.add_all([student, faculty, augsd])
    db.session.commit()

    # ── Departments ────────────────────────────────────────────
    cs   = Department(dept_name='Computer Science')
    ece  = Department(dept_name='Electronics')
    mech = Department(dept_name='Mechanical')
    db.session.add_all([cs, ece, mech])
    db.session.commit()

    # ── Resource types ─────────────────────────────────────────
    lab   = ResourceType(type_name='Laboratory')
    hall  = ResourceType(type_name='Hall')
    equip = ResourceType(type_name='Equipment')
    db.session.add_all([lab, hall, equip])
    db.session.commit()

    # ── Time slots ─────────────────────────────────────────────
    db.session.add_all([
        TimeSlot(label='Slot 1 (8–9 AM)',   start_time=time(8, 0),  end_time=time(9, 0)),
        TimeSlot(label='Slot 2 (9–10 AM)',  start_time=time(9, 0),  end_time=time(10, 0)),
        TimeSlot(label='Slot 3 (10–11 AM)', start_time=time(10, 0), end_time=time(11, 0)),
        TimeSlot(label='Slot 4 (12–1 PM)',  start_time=time(12, 0), end_time=time(13, 0)),
        TimeSlot(label='Slot 5 (2–3 PM)',   start_time=time(14, 0), end_time=time(15, 0)),
        TimeSlot(label='Slot 6 (3–4 PM)',   start_time=time(15, 0), end_time=time(16, 0)),
    ])
    db.session.commit()

    # ── Users ──────────────────────────────────────────────────
    alice  = User(name='Alice Sharma', email='alice@college.edu',  password='pass123', dept_id=cs.dept_id,   role_id=student.role_id)
    bob    = User(name='Bob Verma',    email='bob@college.edu',    password='pass123', dept_id=cs.dept_id,   role_id=faculty.role_id)
    carol  = User(name='Carol Nair',   email='carol@college.edu',  password='pass123', dept_id=ece.dept_id,  role_id=student.role_id)
    david  = User(name='David Raj',    email='david@college.edu',  password='pass123', dept_id=ece.dept_id,  role_id=faculty.role_id)
    eve    = User(name='Eve Patel',    email='eve@college.edu',    password='pass123', dept_id=mech.dept_id, role_id=student.role_id)
    augsd_user = User(name='AUGSD Admin', email='augsd@college.edu', password='augsd123', dept_id=cs.dept_id, role_id=augsd.role_id)
    db.session.add_all([alice, bob, carol, david, eve, augsd_user])
    db.session.commit()

    # ── Resources ──────────────────────────────────────────────
    cs_lab_a    = Resource(name='CS Lab A',        type_id=lab.type_id,   dept_id=cs.dept_id,   capacity=30,  requires_approval=False)
    conf_hall   = Resource(name='Conference Hall', type_id=hall.type_id,  dept_id=cs.dept_id,   capacity=100, requires_approval=True)
    ece_lab_b   = Resource(name='ECE Lab B',       type_id=lab.type_id,   dept_id=ece.dept_id,  capacity=25,  requires_approval=False)
    oscillo     = Resource(name='Oscilloscope Set',type_id=equip.type_id, dept_id=ece.dept_id,  capacity=5,   requires_approval=False)
    mech_ws     = Resource(name='Mech Workshop',   type_id=lab.type_id,   dept_id=mech.dept_id, capacity=20,  requires_approval=True)
    db.session.add_all([cs_lab_a, conf_hall, ece_lab_b, oscillo, mech_ws])
    db.session.commit()

    # ── Approval rules ─────────────────────────────────────────
    # Conference Hall: ANY one faculty approval is enough (OR logic)
    # Mech Workshop:   ALL assigned faculty must approve (AND logic)
    db.session.add_all([
        ResourceApprovalRule(resource_id=conf_hall.resource_id, rule_type='ANY'),
        ResourceApprovalRule(resource_id=mech_ws.resource_id,   rule_type='ALL'),
    ])
    db.session.commit()

    # ── Faculty mappings ───────────────────────────────────────
    # Bob and David both review Conference Hall (ANY → either one is enough)
    # Bob and David both must review Mech Workshop (ALL → both required)
    db.session.add_all([
        ResourceFacultyMapping(resource_id=conf_hall.resource_id, faculty_id=bob.user_id),
        ResourceFacultyMapping(resource_id=conf_hall.resource_id, faculty_id=david.user_id),
        ResourceFacultyMapping(resource_id=mech_ws.resource_id,   faculty_id=bob.user_id),
        ResourceFacultyMapping(resource_id=mech_ws.resource_id,   faculty_id=david.user_id),
    ])
    db.session.commit()

    print('Seeded successfully.')
    print()
    print('  augsd@college.edu / augsd123   → Super Admin')
    print('  bob@college.edu   / pass123    → Faculty')
    print('  david@college.edu / pass123    → Faculty')
    print('  alice@college.edu / pass123    → Student')