USE unified_booking;

-- ── Lookup data ─────────────────────────────

INSERT INTO departments (dept_name) VALUES
    ('Computer Science'),
    ('Electronics'),
    ('Mechanical');

INSERT INTO roles (role_name) VALUES
    ('student'),    -- role_id = 1
    ('faculty'),    -- role_id = 2
    ('admin');      -- role_id = 3

INSERT INTO resource_types (type_name) VALUES
    ('Laboratory'),
    ('Hall'),
    ('Equipment');

INSERT INTO time_slots (label, start_time, end_time) VALUES
    ('Slot 1 (8–9 AM)',    '08:00:00', '09:00:00'),
    ('Slot 2 (9–10 AM)',   '09:00:00', '10:00:00'),
    ('Slot 3 (10–11 AM)',  '10:00:00', '11:00:00'),
    ('Slot 4 (12–1 PM)',   '12:00:00', '13:00:00'),
    ('Slot 5 (2–3 PM)',    '14:00:00', '15:00:00'),
    ('Slot 6 (3–4 PM)',    '15:00:00', '16:00:00');

-- ── Users (password = 'pass123' for all — demo only) ──

INSERT INTO users (name, email, password, dept_id, role_id) VALUES
    ('Alice Sharma',  'alice@college.edu',  'pass123', 1, 1),  -- CS student
    ('Bob Verma',     'bob@college.edu',    'pass123', 1, 2),  -- CS faculty
    ('Carol Nair',    'carol@college.edu',  'pass123', 2, 1),  -- ECE student
    ('David Raj',     'david@college.edu',  'pass123', 2, 2),  -- ECE faculty
    ('Eve Patel',     'eve@college.edu',    'pass123', 3, 1),  -- Mech student
    ('Frank Admin',   'admin@college.edu',  'pass123', 1, 3);  -- Admin

-- ── Resources ───────────────────────────────

INSERT INTO resources (name, type_id, dept_id, capacity, requires_approval, is_active) VALUES
    ('CS Lab A',          1, 1, 30,  0, 1),  -- no approval needed
    ('Conference Hall',   2, 1, 100, 1, 1),  -- requires approval
    ('ECE Lab B',         1, 2, 25,  0, 1),
    ('Oscilloscope Set',  3, 2, 5,   0, 1),
    ('Mech Workshop',     1, 3, 20,  1, 1);  -- requires approval

-- ── Sample Bookings ──────────────────────────

-- Alice books CS Lab A (auto-approved, no approval needed)
INSERT INTO bookings (user_id, resource_id, slot_id, booking_date, status, requires_approval)
    VALUES (1, 1, 1, '2026-04-07', 'approved', 0);

-- Bob books Conference Hall (pending admin approval)
INSERT INTO bookings (user_id, resource_id, slot_id, booking_date, status, requires_approval)
    VALUES (2, 2, 3, '2026-04-08', 'pending', 1);

-- Carol books ECE Lab B (auto-approved)
INSERT INTO bookings (user_id, resource_id, slot_id, booking_date, status, requires_approval)
    VALUES (3, 3, 2, '2026-04-07', 'approved', 0);

-- David books Mech Workshop (pending approval)
INSERT INTO bookings (user_id, resource_id, slot_id, booking_date, status, requires_approval)
    VALUES (4, 5, 4, '2026-04-09', 'pending', 1);

-- Eve books CS Lab A — different slot, no conflict
INSERT INTO bookings (user_id, resource_id, slot_id, booking_date, status, requires_approval)
    VALUES (5, 1, 5, '2026-04-07', 'approved', 0);

-- Usage logs for approved bookings
INSERT INTO usage_logs (booking_id) VALUES (1), (3), (5);