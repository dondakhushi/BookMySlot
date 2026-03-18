-- ============================================================
--  BookMySlot - University Hall Booking System
--  Complete MySQL Schema + Sample Data
-- ============================================================

CREATE DATABASE IF NOT EXISTS bookmyslot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bookmyslot;

-- ─────────────────────────────────────────────
--  TABLE: users
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(120)  NOT NULL,
    email       VARCHAR(180)  NOT NULL UNIQUE,
    password    VARCHAR(255)  NOT NULL,          -- bcrypt hash
    role        ENUM('admin','faculty') NOT NULL DEFAULT 'faculty',
    department  VARCHAR(120)  DEFAULT NULL,
    phone       VARCHAR(20)   DEFAULT NULL,
    is_active   TINYINT(1)    NOT NULL DEFAULT 1,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role  (role)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  TABLE: halls
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS halls (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    hall_name   VARCHAR(150)  NOT NULL,
    capacity    INT           NOT NULL,
    location    VARCHAR(200)  NOT NULL,
    description TEXT          DEFAULT NULL,
    facilities  VARCHAR(500)  DEFAULT NULL,      -- comma-separated list
    is_active   TINYINT(1)    NOT NULL DEFAULT 1,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  TABLE: bookings
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bookings (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT          NOT NULL,
    hall_id      INT          NOT NULL,
    date         DATE         NOT NULL,
    start_time   TIME         NOT NULL,
    end_time     TIME         NOT NULL,
    event_title  VARCHAR(255) NOT NULL,
    description  TEXT         DEFAULT NULL,
    attendees    INT          DEFAULT 0,
    status       ENUM('pending','approved','rejected','cancelled') NOT NULL DEFAULT 'pending',
    admin_note   VARCHAR(500) DEFAULT NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)  ON DELETE CASCADE,
    FOREIGN KEY (hall_id) REFERENCES halls(id)  ON DELETE CASCADE,
    INDEX idx_hall_date (hall_id, date),
    INDEX idx_user      (user_id),
    INDEX idx_status    (status),
    -- Prevent exact duplicate submissions
    UNIQUE KEY uq_booking (hall_id, date, start_time, end_time, status)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  TABLE: notifications
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    message    TEXT         NOT NULL,
    is_read    TINYINT(1)   NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_read (user_id, is_read)
) ENGINE=InnoDB;

-- ============================================================
--  SAMPLE DATA
-- ============================================================

-- ── Users ──────────────────────────────────────────────────
-- Passwords are bcrypt-hashed versions of the plaintext shown in comments.
-- Admin  password : Admin@123
-- Faculty password: Faculty@123

INSERT INTO users (name, email, password, role, department, phone) VALUES
(
  'Dr. Admin User',
  'admin@university.edu',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMqJqhpfY2MxQmU3T5bC9DzfI2',
  'admin', 'Administration', '9000000001'
),
(
  'Prof. Ramesh Patel',
  'ramesh.patel@university.edu',
  '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
  'faculty', 'Computer Science', '9000000002'
),
(
  'Dr. Priya Mehta',
  'priya.mehta@university.edu',
  '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
  'faculty', 'Electronics', '9000000003'
),
(
  'Prof. Suresh Shah',
  'suresh.shah@university.edu',
  '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
  'faculty', 'Mechanical', '9000000004'
);

-- ── Halls ──────────────────────────────────────────────────
INSERT INTO halls (hall_name, capacity, location, description, facilities) VALUES
('Main Seminar Hall A', 200, 'Block A, Ground Floor', 'Large auditorium-style hall with tiered seating, ideal for conferences and expert talks.', 'Projector,Sound System,Air Conditioning,Wi-Fi,Whiteboard,Video Conferencing'),
('Webinar Studio 1', 30, 'Block B, 2nd Floor', 'Dedicated webinar studio with green screen and broadcast equipment.', 'HD Camera,Green Screen,Sound Proof,Air Conditioning,Wi-Fi,Recording Setup'),
('Conference Room C', 50, 'Admin Block, 1st Floor', 'Mid-size conference room suitable for department meetings and workshops.', 'Smart TV,Air Conditioning,Wi-Fi,Whiteboard,Video Conferencing'),
('Innovation Lab Hall', 80, 'Tech Block, Ground Floor', 'Modern hall with movable seating for interactive workshops and hackathons.', 'Projector,Air Conditioning,Wi-Fi,Multiple Power Outlets,Whiteboard'),
('Heritage Auditorium', 500, 'Main Campus, Central', 'Large heritage auditorium for university-wide events and convocations.', 'Projector,Sound System,Air Conditioning,Stage Lighting,Recording Equipment,Wi-Fi');

-- ── Bookings (sample – dates relative to today) ────────────
INSERT INTO bookings (user_id, hall_id, date, start_time, end_time, event_title, description, attendees, status) VALUES
(2, 1, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '10:00:00', '12:00:00', 'AI & ML Expert Talk', 'Guest lecture by Dr. Arjun from IIT Bombay on recent advances in ML.', 150, 'approved'),
(3, 2, DATE_ADD(CURDATE(), INTERVAL 3 DAY), '14:00:00', '15:30:00', 'Webinar: IoT Basics', 'Introductory webinar on Internet of Things for 2nd-year students.', 25, 'pending'),
(4, 3, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '09:00:00', '11:00:00', 'Dept. Staff Meeting', 'Monthly staff coordination meeting for Mechanical dept.', 40, 'approved'),
(2, 4, DATE_ADD(CURDATE(), INTERVAL 5 DAY), '13:00:00', '17:00:00', 'Hackathon Kickoff', 'Opening ceremony and team formation for annual university hackathon.', 70, 'pending'),
(3, 1, DATE_ADD(CURDATE(), INTERVAL -3 DAY), '11:00:00', '13:00:00', 'Electronics Symposium', 'Annual student project symposium for Electronics branch.', 180, 'approved'),
(2, 3, DATE_ADD(CURDATE(), INTERVAL -7 DAY), '14:00:00', '16:00:00', 'Research Methodology Workshop', 'Workshop for PhD scholars on research writing and tools.', 30, 'rejected');

-- ── Notifications ──────────────────────────────────────────
INSERT INTO notifications (user_id, message) VALUES
(2, CONCAT('Your booking for "AI & ML Expert Talk" on ', DATE_FORMAT(DATE_ADD(CURDATE(), INTERVAL 2 DAY), '%d-%m-%Y'), ' has been APPROVED.')),
(3, 'Your booking for "Electronics Symposium" has been APPROVED.'),
(2, 'Your booking for "Research Methodology Workshop" has been REJECTED. Reason: Hall unavailable due to maintenance.'),
(1, 'New booking request received from Prof. Ramesh Patel for Hackathon Kickoff.'),
(1, 'New booking request received from Dr. Priya Mehta for Webinar: IoT Basics.');
