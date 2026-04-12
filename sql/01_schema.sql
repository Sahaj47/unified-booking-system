-- ===========================================
-- Unified Resource Booking System — Schema
-- ===========================================

CREATE DATABASE IF NOT EXISTS unified_booking;
USE unified_booking;

-- ── Lookup / reference tables ──────────────

CREATE TABLE departments (
    dept_id   INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE roles (
    role_id   INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE   -- 'student', 'faculty', 'admin'
);

CREATE TABLE resource_types (
    type_id   INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE time_slots (
    slot_id    INT AUTO_INCREMENT PRIMARY KEY,
    label      VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time   TIME NOT NULL
);

-- ── Core entity tables ──────────────────────

CREATE TABLE users (
    user_id    INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(100) NOT NULL,        -- plain text for demo only
    dept_id    INT NOT NULL,
    role_id    INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE resources (
    resource_id       INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    type_id           INT NOT NULL,
    dept_id           INT NOT NULL,
    capacity          INT DEFAULT 1,
    requires_approval TINYINT(1) DEFAULT 0,  -- 1 = needs admin sign-off
    is_active         TINYINT(1) DEFAULT 1,
    FOREIGN KEY (type_id) REFERENCES resource_types(type_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- ── Transaction tables ──────────────────────

CREATE TABLE bookings (
    booking_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT NOT NULL,
    resource_id       INT NOT NULL,
    slot_id           INT NOT NULL,
    booking_date      DATE NOT NULL,
    status            ENUM('pending','approved','rejected','cancelled') DEFAULT 'pending',
    requires_approval TINYINT(1) DEFAULT 0,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(user_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
    FOREIGN KEY (slot_id)     REFERENCES time_slots(slot_id)
);

CREATE TABLE approvals (
    approval_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id  INT NOT NULL,
    approved_by INT NOT NULL,               -- FK to users (admin)
    action      ENUM('approved','rejected') NOT NULL,
    remarks     TEXT,
    actioned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id)  REFERENCES bookings(booking_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id)
);

CREATE TABLE usage_logs (
    log_id       INT AUTO_INCREMENT PRIMARY KEY,
    booking_id   INT NOT NULL UNIQUE,
    actual_start DATETIME,
    actual_end   DATETIME,
    logged_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);