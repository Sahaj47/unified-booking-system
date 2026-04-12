USE unified_booking;

-- ============================================================
-- TRIGGER: Prevent double-booking (same resource+slot+date)
-- ============================================================
DELIMITER $$

CREATE TRIGGER prevent_double_booking
BEFORE INSERT ON bookings
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT;

    SELECT COUNT(*) INTO conflict_count
    FROM bookings
    WHERE resource_id  = NEW.resource_id
      AND slot_id      = NEW.slot_id
      AND booking_date = NEW.booking_date
      AND status       IN ('pending', 'approved');

    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Resource already booked for this slot and date.';
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- VIEW: Full booking schedule (used in dashboard & summary)
-- ============================================================
CREATE VIEW booking_schedule AS
SELECT
    b.booking_id,
    b.user_id,
    u.name           AS user_name,
    d.dept_name,
    r.resource_id,
    r.name           AS resource_name,
    rt.type_name     AS resource_type,
    ts.slot_id,
    ts.label         AS time_slot,
    ts.start_time,
    ts.end_time,
    b.booking_date,
    b.status,
    b.requires_approval,
    b.created_at
FROM bookings b
JOIN users         u  ON b.user_id      = u.user_id
JOIN departments   d  ON u.dept_id      = d.dept_id
JOIN resources     r  ON b.resource_id  = r.resource_id
JOIN resource_types rt ON r.type_id    = rt.type_id
JOIN time_slots    ts ON b.slot_id     = ts.slot_id;

-- ============================================================
-- STORED PROCEDURE: Get all bookings for a specific resource
-- ============================================================
DELIMITER $$

CREATE PROCEDURE GetBookingsByResource(IN p_resource_id INT)
BEGIN
    SELECT
        b.booking_id,
        u.name       AS user_name,
        r.name       AS resource_name,
        ts.label     AS slot,
        b.booking_date,
        b.status
    FROM bookings b
    JOIN users      u  ON b.user_id     = u.user_id
    JOIN resources  r  ON b.resource_id = r.resource_id
    JOIN time_slots ts ON b.slot_id     = ts.slot_id
    WHERE b.resource_id = p_resource_id
    ORDER BY b.booking_date, ts.start_time;
END$$

DELIMITER ;