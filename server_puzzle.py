import re
import socket
import json
import sqlite3
from datetime import datetime
from server_auth import SessionManager, hash_password, make_response, recv_until_newline, load_users, save_users, \
    DATABASE


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
    
    def get_leaderboard(self, sort_by='speed'):
        if sort_by == 'speed':
            self.cursor.execute('''SELECT u.username, AVG(s.time_taken) as avg_time,
                                 COUNT(CASE WHEN s.result = 'correct' THEN 1 END) as correct_count
                                 FROM submissions s
                                 JOIN users u ON s.user_id = u.id
                                 WHERE s.result = 'correct'
                                 GROUP BY u.id
                                 HAVING correct_count >= 3
                                 ORDER BY avg_time ASC
                                 LIMIT 10''')
        else:  # accuracy
            self.cursor.execute('''SELECT u.username, 
                                 COUNT(CASE WHEN s.result = 'correct' THEN 1 END) * 100.0 / 
                                 COUNT(*) as accuracy,
                                 COUNT(*) as total_attempts
                                 FROM submissions s
                                 JOIN users u ON s.user_id = u.id
                                 GROUP BY u.id
                                 HAVING total_attempts >= 3
                                 ORDER BY accuracy DESC
                                 LIMIT 10''')
        
        leaderboard = []
        for row in self.cursor.fetchall():
            if sort_by == 'speed':
                leaderboard.append({
                    'username': row[0],
                    'avg_time': row[1],
                    'solved_count': row[2]
                })
            else:
                leaderboard.append({
                    'username': row[0],
                    'accuracy': row[1],
                    'total_attempts': row[2]
                })
        return leaderboard
    
    def get_recent_activity(self, limit=10):
        self.cursor.execute('''SELECT u.username, p.title, s.result, s.timestamp,
                             s.time_taken
                             FROM submissions s
                             JOIN users u ON s.user_id = u.id
                             JOIN puzzles p ON s.puzzle_id = p.id
                             ORDER BY s.timestamp DESC
                             LIMIT ?''', (limit,))
        
        activities = []
        for row in self.cursor.fetchall():
            activities.append({
                'username': row[0],
                'puzzle_title': row[1],
                'result': row[2],
                'timestamp': row[3],
                'time_taken': row[4]
            })
        return activities

def handle_client_request(data, session_manager, puzzle_manager, submission_manager, stats_manager):
    try:
        request = json.loads(data)
        action = request.get("action")
        payload = request.get("payload", {})
        token = request.get("auth_token")

        # Authentication required actions
        if action in ["get_puzzles", "get_puzzle", "submit_solution", "get_stats", 
                     "get_leaderboard", "get_recent_activity"]:
            if not session_manager.validate_session(token):
                return make_response("error", "Invalid or expired session")

        # Add registration handling
        if action == "register":
            username = payload.get("username", "").strip()
            password = payload.get("password", "").strip()

            # Validate that both username and password are not emptyq
            if not username or not password:
                return make_response("error", "Username and password cannot be empty")

            # Validate username
            if not re.match(r'^[a-zA-Z0-9_]{2,20}$', username):
                return make_response("error", "Username must be 2-20 characters of letters or digits")

            # Validate password strength (at least 3 characters)
            if len(password) < 3:
                return make_response("error", "Password must be at least 3 characters long", {"field": "password"})

            # Check if user already exists
            users = load_users()
            if username in users:
                return make_response("error", "Username already exists")

            # Only save if all validations pass
            users[username] = password
            save_users(users)
            return make_response("success", "Registration successful")

        elif action == "login":
            username = payload.get("username", "").strip()
            password = payload.get("password", "").strip()

            # Input validation
            if not username or not password:
                return make_response("error", "Username and password cannot be empty")

            # Load user database
            users = load_users()

            # Check if user exists
            if username not in users:
                return make_response("error", "Username does not exist", {"field": "username"})

            # Password verification (note: client has already done SHA256 hashing)
            if users[username] != password:
                return make_response("error", "Incorrect password", {"field": "password"})

            # Create session
            token = session_manager.create_session(username)

            # Update last login time
            update_last_login(username)

            return make_response("success", "Login successful", {
                "auth_token": token,
                "username": username
            })

        elif action == "get_puzzles":
            sort_by = payload.get("sort_by", "date")
            order = payload.get("order", "desc")
            tag = payload.get("tag")
            puzzles = puzzle_manager.get_puzzle_list(sort_by, order, tag)
            return make_response("success", "Puzzles retrieved", {"puzzles": puzzles})

        elif action == "get_puzzle":
            puzzle_id = payload.get("puzzle_id")
            puzzle = puzzle_manager.get_puzzle_by_id(puzzle_id)
            if puzzle:
                return make_response("success", "Puzzle retrieved", {"puzzle": puzzle})
            return make_response("error", "Puzzle not found")

        elif action == "submit_solution":
            puzzle_id = payload.get("puzzle_id")
            user_id = payload.get("user_id")
            grid = payload.get("grid")
            time_taken = payload.get("time_taken")
            
            result = submission_manager.submit_solution(puzzle_id, user_id, grid, time_taken)
            return make_response("success", "Solution submitted", result)

        elif action == "get_stats":
            user_id = payload.get("user_id")
            stats = stats_manager.get_user_stats(user_id)
            return make_response("success", "Stats retrieved", stats)
            
        elif action == "get_leaderboard":
            sort_by = payload.get("sort_by", "speed")
            leaderboard = stats_manager.get_leaderboard(sort_by)
            return make_response("success", "Leaderboard retrieved", {"leaderboard": leaderboard})
            
        elif action == "get_recent_activity":
            limit = payload.get("limit", 10)
            activities = stats_manager.get_recent_activity(limit)
            return make_response("success", "Recent activity retrieved", {"activities": activities})

        else:
            return make_response("error", "Unknown action")

    except json.JSONDecodeError:
        return make_response("error", "Invalid request format")
    except Exception as e:
        return make_response("error", f"Error processing request: {str(e)}")


def update_last_login(username):
    """Update the user's last login time"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("UPDATE user_stats SET last_login=CURRENT_TIMESTAMP WHERE user_id=?",
                 (username,))
        conn.commit()
    except Exception as e:
        print(f"Failed to update last login time: {e}")
    finally:
        conn.close()

def start_server(host, port):
    # Initialize database connection
    conn = sqlite3.connect('DATABASE-puzzles.db')
    
    # Initialize managers
    session_manager = SessionManager()
    puzzle_manager = PuzzleManager(conn)
    submission_manager = SubmissionManager(conn)
    stats_manager = StatisticsManager(conn)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server listening on {host}:{port}...")

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                with client_socket:
                    print(f"Connection from {client_address}")
                    data = recv_until_newline(client_socket)
                    if not data:
                        continue
                    print(f"Received request: {data}")
                    response = handle_client_request(
                        data, session_manager, puzzle_manager, 
                        submission_manager, stats_manager
                    )
                    client_socket.sendall((response + '\n').encode('utf-8'))
            except Exception as e:
                print(f"[SERVER ERROR] Error handling client request: {e}")

if __name__ == "__main__":
    start_server("localhost", 5000) 