-- ============================================
-- LifeSync Dashboard - MySQL Database Setup
-- ============================================
-- Run these queries in MySQL Workbench
-- Execute in order from top to bottom
-- ============================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS lifesync_db;
USE lifesync_db;

-- ============================================
-- Step 2: Create Users Table
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    theme_preference ENUM('light', 'dark') DEFAULT 'dark',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- Step 3: Create Habits Table
-- ============================================
CREATE TABLE IF NOT EXISTS habits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#4CAF50',
    icon VARCHAR(50) DEFAULT '✓',
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- Step 4: Create Habit Logs Table (Sparse Storage)
-- Only stores completed habits - absence means not done
-- ============================================
CREATE TABLE IF NOT EXISTS habit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    habit_id INT NOT NULL,
    completed_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_habit_date (habit_id, completed_date),
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
);

-- ============================================
-- Step 5: Create Tasks Table
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    due_date DATE,
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    category VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- Step 6: Create Indexes for Performance
-- ============================================
CREATE INDEX idx_habit_logs_date ON habit_logs(completed_date);
CREATE INDEX idx_habit_logs_habit ON habit_logs(habit_id);
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_user_date ON tasks(user_id, due_date);
CREATE INDEX idx_habits_user ON habits(user_id);

-- ============================================
-- Step 7: Create View for Daily Statistics
-- ============================================
CREATE OR REPLACE VIEW daily_habit_stats AS
SELECT 
    h.user_id,
    hl.completed_date,
    COUNT(DISTINCT hl.habit_id) as completed_count,
    (SELECT COUNT(*) FROM habits WHERE user_id = h.user_id AND is_active = TRUE) as total_habits,
    ROUND(
        (COUNT(DISTINCT hl.habit_id) / 
        (SELECT COUNT(*) FROM habits WHERE user_id = h.user_id AND is_active = TRUE)) * 100, 
        2
    ) as completion_percentage
FROM habits h
LEFT JOIN habit_logs hl ON h.id = hl.habit_id
WHERE h.is_active = TRUE
GROUP BY h.user_id, hl.completed_date;

-- ============================================
-- Verification Queries (Optional - Run to test)
-- ============================================

-- Check all tables created
-- SHOW TABLES;

-- Describe each table structure
-- DESCRIBE users;
-- DESCRIBE habits;
-- DESCRIBE habit_logs;
-- DESCRIBE tasks;

-- ============================================
-- Sample Data (Optional - for testing)
-- ============================================

-- Insert a test user (password is 'test123' hashed)
-- INSERT INTO users (username, email, password_hash) VALUES 
-- ('testuser', 'test@example.com', 'pbkdf2:sha256:600000$...');

-- Insert sample habits
-- INSERT INTO habits (user_id, name, description, color) VALUES 
-- (1, 'Wake up before 7 AM', 'Start the day early', '#4CAF50'),
-- (1, 'Drink 2L of water', 'Stay hydrated', '#2196F3'),
-- (1, 'Exercise / Walk', '30 minutes minimum', '#FF9800'),
-- (1, 'Read 10 pages', 'Daily reading habit', '#9C27B0'),
-- (1, 'Study 2 hours', 'Focused learning', '#E91E63');
