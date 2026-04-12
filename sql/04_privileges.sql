-- ============================================================
-- DBA RIGHTS DEMONSTRATION (FIXED & MYSQL 8 SAFE)
-- ============================================================

USE unified_booking;

-- ── Clean existing users (avoids conflicts) ───────────────
DROP USER IF EXISTS 'booking_readonly'@'localhost';
DROP USER IF EXISTS 'booking_staff'@'localhost';

-- ── 1. Read-only user (SELECT only) ───────────────────────
CREATE USER 'booking_readonly'@'localhost'
IDENTIFIED BY 'ReadOnly@123';

GRANT SELECT
ON unified_booking.*
TO 'booking_readonly'@'localhost';

-- ── 2. Staff user (limited update access) ────────────────
CREATE USER 'booking_staff'@'localhost'
IDENTIFIED BY 'Staff@123';

-- Can read everything
GRANT SELECT
ON unified_booking.*
TO 'booking_staff'@'localhost';

-- Can ONLY update booking status
GRANT UPDATE (status)
ON unified_booking.bookings
TO 'booking_staff'@'localhost';

-- ── Apply changes ────────────────────────────────────────
FLUSH PRIVILEGES;

-- ── Verification (run manually if needed) ────────────────
-- SHOW GRANTS FOR 'booking_readonly'@'localhost';
-- SHOW GRANTS FOR 'booking_staff'@'localhost';