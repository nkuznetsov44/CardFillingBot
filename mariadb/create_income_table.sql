-- Migration script to create income table
-- Run this script to add income tracking functionality to your database

CREATE TABLE IF NOT EXISTS income (
    income_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    income_date DATETIME NOT NULL,
    amount FLOAT NOT NULL,
    description VARCHAR(255),
    fill_scope INT NOT NULL,
    currency VARCHAR(10),
    original_amount FLOAT,
    original_currency VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES telegram_user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (fill_scope) REFERENCES fill_scope(scope_id) ON DELETE CASCADE,
    
    INDEX idx_income_user_date (user_id, income_date),
    INDEX idx_income_scope_date (fill_scope, income_date),
    INDEX idx_income_date (income_date)
);

-- Add income relationship to telegram_user table if not exists
-- This is handled by SQLAlchemy relationships, but you may need to verify the table structure 