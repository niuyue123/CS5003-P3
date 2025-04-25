-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 谜题表
CREATE TABLE IF NOT EXISTS puzzles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT NOT NULL,
    grid TEXT NOT NULL,
    clues TEXT NOT NULL,
    solution_key TEXT NOT NULL,
    author_id INTEGER,
    solved_count INTEGER DEFAULT 0,
    last_solved TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id)
);

-- 提交记录表
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    puzzle_id INTEGER,
    grid_submitted TEXT NOT NULL,
    time_taken REAL NOT NULL,
    result TEXT NOT NULL,
    incorrect_cells TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (puzzle_id) REFERENCES puzzles(id)
);

-- 用户统计表
CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY,
    puzzles_solved INTEGER DEFAULT 0,
    avg_time REAL DEFAULT 0,
    last_login TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_submissions_user ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_puzzle ON submissions(puzzle_id);
CREATE INDEX IF NOT EXISTS idx_puzzles_author ON puzzles(author_id); 