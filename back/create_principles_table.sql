-- Create principles table
CREATE TABLE IF NOT EXISTS principles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    principle_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_principles_user_id ON principles(user_id);

-- Grant permissions to goniadmin user
GRANT SELECT, INSERT, UPDATE, DELETE ON principles TO goniadmin;
GRANT USAGE, SELECT ON SEQUENCE principles_id_seq TO goniadmin;
