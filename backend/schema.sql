-- Create database
CREATE DATABASE IF NOT EXISTS quiz_system_3;
USE quiz_system_3;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    question_text TEXT NOT NULL,
    points INT DEFAULT 1,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Options table
CREATE TABLE IF NOT EXISTS options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- Quiz attempts table
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    score INT NOT NULL,
    total_time INT NOT NULL,
    correct_answers INT NOT NULL,
    total_questions INT NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- User progress table
CREATE TABLE IF NOT EXISTS user_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    last_question_id INT,
    current_score INT DEFAULT 0,
    time_spent INT DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (last_question_id) REFERENCES questions(id)
);

-- Sample data for categories
INSERT INTO categories (name, description) VALUES
('General Knowledge', 'Test your knowledge on various general topics'),
('Science', 'Questions about physics, chemistry, and biology'),
('Mathematics', 'Mathematical problems and concepts'),
('Computer Science', 'Programming, algorithms, and computer concepts'),
('History', 'Historical events and figures');

-- Create admin user (password: admin123)
INSERT INTO users (username, email, password, role) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewFX.gtkv4K1v2qO', 'admin'); 