from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import hashlib
import time
import requests

app = Flask(__name__)
CORS(app)

class PuzzleManager:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def get_puzzle_list(self, sort_by='date', order='desc', tag=None):
        query = '''SELECT p.id, p.title, p.date, p.tags, p.solved_count, p.last_solved,
                         u.username as author
                  FROM puzzles p
                  LEFT JOIN users u ON p.author_id = u.id'''
        
        if tag:
            query += " WHERE p.tags LIKE ?"
            self.cursor.execute(query, (f'%{tag}%',))
        else:
            self.cursor.execute(query)
        
        puzzles = []
        for row in self.cursor.fetchall():
            puzzles.append({
                'id': row[0],
                'title': row[1],
                'date': row[2],
                'tags': json.loads(row[3]),
                'solved_count': row[4],
                'last_solved': row[5],
                'author': row[6]
            })
        
        return sorted(puzzles, 
                     key=lambda x: x[sort_by],
                     reverse=(order == 'desc'))
    
    def get_puzzle_by_id(self, puzzle_id):
        self.cursor.execute('''SELECT p.*, u.username as author
                             FROM puzzles p
                             LEFT JOIN users u ON p.author_id = u.id
                             WHERE p.id = ?''', (puzzle_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'date': row[2],
                'tags': json.loads(row[3]),
                'grid': json.loads(row[4]),
                'clues': json.loads(row[5]),
                'solution_key': json.loads(row[6]),
                'author_id': row[7],
                'author': row[8]
            }
        return None

class SubmissionManager:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def submit_solution(self, puzzle_id, user_id, grid, time_taken):
        # Get the correct solution
        self.cursor.execute('SELECT solution_key FROM puzzles WHERE id = ?', (puzzle_id,))
        solution_key = json.loads(self.cursor.fetchone()[0])
        
        # Compare solutions
        incorrect_cells = []
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if grid[i][j].upper() != solution_key[i][j]:
                    incorrect_cells.append((i, j))
        
        is_correct = len(incorrect_cells) == 0
        
        # Record submission
        self.cursor.execute('''INSERT INTO submissions 
                             (user_id, puzzle_id, grid_submitted, time_taken, 
                              result, incorrect_cells)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (user_id, puzzle_id, json.dumps(grid), time_taken,
                           'correct' if is_correct else 'incorrect',
                           json.dumps(incorrect_cells)))
        
        # Update puzzle stats
        if is_correct:
            self.cursor.execute('''UPDATE puzzles 
                                 SET solved_count = solved_count + 1,
                                     last_solved = CURRENT_TIMESTAMP
                                 WHERE id = ?''', (puzzle_id,))
        
        self.conn.commit()
        
        return {
            'submission_id': self.cursor.lastrowid,
            'result': 'correct' if is_correct else 'incorrect',
            'incorrect_cells': incorrect_cells
        }

class StatisticsManager:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def get_user_stats(self, user_id):
        # Get basic stats
        self.cursor.execute('''SELECT puzzles_solved, avg_time, last_login
                             FROM user_stats
                             WHERE user_id = ?''', (user_id,))
        row = self.cursor.fetchone()
        
        if not row:
            return {
                'puzzles_solved': 0,
                'avg_time': 0,
                'last_login': None
            }
        
        return {
            'puzzles_solved': row[0],
            'avg_time': row[1],
            'last_login': row[2]
        }
    
    def get_puzzle_stats(self, puzzle_id):
        self.cursor.execute('''SELECT solved_count, last_solved
                             FROM puzzles
                             WHERE id = ?''', (puzzle_id,))
        row = self.cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'solved_count': row[0],
            'last_solved': row[1]
        }

def init_db():
    conn = sqlite3.connect('crosswords.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # User stats table
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats
                 (user_id INTEGER PRIMARY KEY,
                  puzzles_solved INTEGER DEFAULT 0,
                  avg_time FLOAT DEFAULT 0,
                  last_login TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Puzzles table
    c.execute('''CREATE TABLE IF NOT EXISTS puzzles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  tags TEXT NOT NULL,
                  grid TEXT NOT NULL,
                  clues TEXT NOT NULL,
                  solution_key TEXT NOT NULL,
                  author_id INTEGER,
                  solved_count INTEGER DEFAULT 0,
                  last_solved TIMESTAMP,
                  FOREIGN KEY (author_id) REFERENCES users(id))''')
    
    # Submissions table
    c.execute('''CREATE TABLE IF NOT EXISTS submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  puzzle_id INTEGER,
                  grid_submitted TEXT NOT NULL,
                  time_taken FLOAT NOT NULL,
                  result TEXT NOT NULL,
                  incorrect_cells TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (puzzle_id) REFERENCES puzzles(id))''')
    
    conn.commit()
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize managers
conn = init_db()
puzzle_manager = PuzzleManager(conn)
submission_manager = SubmissionManager(conn)
stats_manager = StatisticsManager(conn)

@app.route('/api/register', methods=['POST'])
def register():
    # User registration logic

@app.route('/api/login', methods=['POST'])
def login():
    # User authentication logic

@app.route('/api/puzzles', methods=['GET'])
def get_puzzles():
    # Get all puzzles

@app.route('/api/puzzles/<int:puzzle_id>', methods=['GET'])
def get_puzzle(puzzle_id):
    puzzle = puzzle_manager.get_puzzle_by_id(puzzle_id)
    if puzzle:
        return jsonify(puzzle)
    return jsonify({'error': 'Puzzle not found'}), 404

@app.route('/api/puzzles/<int:puzzle_id>/validate', methods=['POST'])
def validate_answer(puzzle_id):
    # Validate puzzle answer

@app.route('/api/users/<int:user_id>/statistics', methods=['GET'])
def get_user_statistics(user_id):
    # Get user statistics

@app.route('/api/puzzles/<int:puzzle_id>/submit', methods=['POST'])
def submit_solution(puzzle_id):
    data = request.json
    user_id = data.get('user_id')
    grid = data.get('grid')
    time_taken = data.get('time_taken')
    
    result = submission_manager.submit_solution(puzzle_id, user_id, grid, time_taken)
    return jsonify(result)

@app.route('/api/users/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    stats = stats_manager.get_user_stats(user_id)
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 