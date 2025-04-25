import socket
import json
import sqlite3
import threading
from datetime import datetime
from server_auth import SessionManager

DATABASE = 'DATABASE-puzzles.db'

class PuzzleManager:
    def __init__(self, db_path='DATABASE-puzzles.db'):
        self.db_path = db_path

    def get_puzzle_list(self, sort_by='date', order='desc', tag=None):
        print(f"[DEBUG] Getting puzzle list parameters: sort_by={sort_by}, order={order}, tag={tag}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert sorting fields
            sort_mapping = {
                'date': 'p.date',
                'title': 'p.title',
                'solved_count': 'p.solved_count'
            }
            sort_field = sort_mapping.get(sort_by, 'p.date')
            
            if tag:
                query = """
                    SELECT p.id, p.title, p.grid, p.clues, p.tags, p.author_id, p.date, p.solved_count,
                           u.username as author_name
                    FROM puzzles p
                    LEFT JOIN users u ON p.author_id = u.id
                    WHERE p.tags LIKE ?
                    ORDER BY {} {}
                """.format(sort_field, order)
                cursor.execute(query, (f"%{tag}%",))
            else:
                query = """
                    SELECT p.id, p.title, p.grid, p.clues, p.tags, p.author_id, p.date, p.solved_count,
                           u.username as author_name
                    FROM puzzles p
                    LEFT JOIN users u ON p.author_id = u.id
                    ORDER BY {} {}
                """.format(sort_field, order)
                cursor.execute(query)
            
            puzzles = []
            for row in cursor.fetchall():
                puzzle = {
                    'id': row[0],
                    'title': row[1],
                    'grid': json.loads(row[2]),
                    'clues': json.loads(row[3]),
                    'tags': row[4].split(',') if row[4] else [],
                    'author_id': row[5],
                    'date': row[6],
                    'solved_count': row[7],
                    'author_name': row[8]
                }
                puzzles.append(puzzle)
            
            print(f"[DEBUG] Found {len(puzzles)} puzzles")
            return puzzles
            
        except Exception as e:
            print(f"[ERROR] Failed to get puzzle list: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()

    def get_puzzle(self, puzzle_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.title, p.grid, p.clues, p.tags, p.author_id, p.date, p.solved_count,
                       p.solution_key, u.username as author_name
                FROM puzzles p
                LEFT JOIN users u ON p.author_id = u.id
                WHERE p.id = ?
            """, (puzzle_id,))
            
            row = cursor.fetchone()
            if row:
                puzzle = {
                    'id': row[0],
                    'title': row[1],
                    'grid': json.loads(row[2]),
                    'clues': json.loads(row[3]),
                    'tags': row[4].split(',') if row[4] else [],
                    'author_id': row[5],
                    'date': row[6],
                    'solved_count': row[7],
                    'solution_key': json.loads(row[8]),
                    'author_name': row[9]
                }
                return puzzle
            return None
            
        except Exception as e:
            print(f"[ERROR] Failed to get puzzle details: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def create_puzzle(self, title, grid, clues, solution_key, tags, author_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO puzzles (title, grid, clues, solution_key, tags, author_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                title,
                json.dumps(grid),
                json.dumps(clues),
                json.dumps(solution_key),
                ','.join(tags),
                author_id
            ))
            
            puzzle_id = cursor.lastrowid
            conn.commit()
            return puzzle_id
            
        except Exception as e:
            print(f"[ERROR] Failed to create puzzle: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

class SubmissionManager:
    def __init__(self, db_path='DATABASE-puzzles.db'):
        self.db_path = db_path

    def submit_solution(self, puzzle_id, user_id, submitted_grid, time_taken):
        try:
            if not puzzle_id or not user_id or not submitted_grid:
                print("[ERROR] Submission parameters incomplete")
                return False, "Submission parameters incomplete"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the correct answer for the puzzle
            cursor.execute("SELECT solution_key FROM puzzles WHERE id = ?", (puzzle_id,))
            row = cursor.fetchone()
            if not row:
                print(f"[ERROR] Puzzle does not exist: {puzzle_id}")
                return False, "Puzzle does not exist"
            
            try:
                solution_key = json.loads(row[0])
                if isinstance(submitted_grid, str):
                    submitted_grid = json.loads(submitted_grid)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON parsing failed: {e}")
                return False, "Answer format error"
            
            # Validate grid size
            if (len(submitted_grid) != len(solution_key) or 
                any(len(row) != len(solution_key[0]) for row in submitted_grid)):
                print("[ERROR] Submitted answer grid size is incorrect")
                return False, "Answer format incorrect"
            
            # Check answer
            incorrect_cells = []
            is_correct = True
            for i, row in enumerate(submitted_grid):
                for j, cell in enumerate(row):
                    if solution_key[i][j] != '#' and cell.upper() != solution_key[i][j].upper():
                        incorrect_cells.append([i, j])
                        is_correct = False
            
            # Record submission
            cursor.execute("""
                INSERT INTO submissions (puzzle_id, user_id, grid_submitted, time_taken, result, incorrect_cells)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                puzzle_id, 
                user_id, 
                json.dumps(submitted_grid),
                time_taken,
                'correct' if is_correct else 'incorrect',
                json.dumps(incorrect_cells) if incorrect_cells else None
            ))
            
            # Update puzzle statistics
            if is_correct:
                cursor.execute("""
                    UPDATE puzzles 
                    SET solved_count = solved_count + 1,
                        last_solved = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (puzzle_id,))
                
                # Update user statistics
                cursor.execute("""
                    INSERT INTO user_stats (user_id, puzzles_solved, avg_time, last_login)
                    VALUES (?, 1, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        puzzles_solved = puzzles_solved + 1,
                        avg_time = (
                            (avg_time * puzzles_solved + ?) / (puzzles_solved + 1)
                        ),
                        last_login = CURRENT_TIMESTAMP
                """, (user_id, time_taken, time_taken))
            
            conn.commit()
            return is_correct, "Correct answer!" if is_correct else f"Incorrect answer, {len(incorrect_cells)} cells are wrong"
            
        except Exception as e:
            print(f"[ERROR] Failed to submit answer: {e}")
            return False, f"Submission failed: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()

    def handle_submit_answer(self, user_id, puzzle_id, answer, time_taken):
        conn = sqlite3.connect(DATABASE)
        try:
            cursor = conn.cursor()
            # Get correct answer
            cursor.execute("SELECT answer FROM puzzles WHERE id = ?", (puzzle_id,))
            row = cursor.fetchone()
            if not row:
                return {'status': 'error', 'message': 'Puzzle not found'}
            
            correct_answer = row[0]
            is_correct = answer.lower().strip() == correct_answer.lower().strip()
            result = 'correct' if is_correct else 'incorrect'
            
            # Record submission
            cursor.execute("""
                INSERT INTO submissions (user_id, puzzle_id, answer, time_taken, result, timestamp)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (user_id, puzzle_id, answer, time_taken, result))
            
            conn.commit()
            return {
                'status': 'success',
                'correct': is_correct,
                'message': 'Correct answer!' if is_correct else 'Incorrect answer, please try again'
            }
        except Exception as e:
            print(f"[ERROR] Failed to submit answer: {e}")
            return {'status': 'error', 'message': f'Failed to submit answer: {str(e)}'}
        finally:
            if 'conn' in locals():
                conn.close()

class StatisticsManager:
    def __init__(self, db_path='DATABASE-puzzles.db'):
        self.db_path = db_path

    def get_user_statistics(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user statistics
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN s.result = 'correct' THEN 1 END) as solved_count,
                    AVG(CASE WHEN s.result = 'correct' THEN s.time_taken END) as avg_time,
                    u.last_login
                FROM submissions s LEFT JOIN user_stats u ON s.user_id = u.user_id
                WHERE s.user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'puzzles_solved': row[0],
                    'avg_time': row[1],
                    'last_login': row[2]
                }
            return {'puzzles_solved': 0, 'avg_time': 0, 'last_login': None}
            
        except Exception as e:
            print(f"[ERROR] Failed to get user statistics: {e}")
            return {'puzzles_solved': 0, 'avg_time': 0, 'last_login': None}
        finally:
            if 'conn' in locals():
                conn.close()

    def get_leaderboard(self):
        conn = sqlite3.connect(DATABASE)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    u.username,
                    COUNT(CASE WHEN s.result = 'correct' THEN 1 END) as solved_count,
                    AVG(CASE WHEN s.result = 'correct' THEN s.time_taken END) as avg_time
                FROM users u
                LEFT JOIN submissions s ON u.id = s.user_id
                GROUP BY u.id, u.username
                ORDER BY solved_count DESC, avg_time ASC
                LIMIT 10
            """)
            
            leaderboard = []
            for row in cursor.fetchall():
                leaderboard.append({
                    'username': row[0],
                    'puzzles_solved': row[1],
                    'avg_time': row[2] if row[2] is not None else 0
                })
            
            return {'status': 'success', 'leaderboard': leaderboard}
            
        except Exception as e:
            print(f"[ERROR] Failed to get leaderboard: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if 'conn' in locals():
                conn.close()

    def get_recent_activity(self):
        conn = sqlite3.connect(DATABASE)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    u.username,
                    p.title,
                    s.result,
                    s.time_taken,
                    s.timestamp
                FROM submissions s
                JOIN users u ON s.user_id = u.id
                JOIN puzzles p ON s.puzzle_id = p.id
                ORDER BY s.timestamp DESC
                LIMIT 10
            """)
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'username': row[0],
                    'puzzle_title': row[1],
                    'result': row[2],
                    'time_taken': row[3],
                    'timestamp': row[4]
                })
            
            return {'status': 'success', 'activities': activities}
            
        except Exception as e:
            print(f"[ERROR] Failed to get recent activity: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if 'conn' in locals():
                conn.close()

def handle_client_request(client_socket, puzzle_manager, submission_manager, stats_manager, session_manager):
    try:
        data = client_socket.recv(4096).decode('utf-8')
        if not data:
            return
        
        print(f"[DEBUG] Received request: {data}")
        request = json.loads(data)
        
        action = request.get('action')
        payload = request.get('payload', {})
        auth_token = request.get('auth_token')
        
        response = {'status': 'error', 'message': 'Unknown error'}
        
        # Get user ID (if authenticated)
        user_id = None
        if auth_token:
            user_id = session_manager.get_user_id(auth_token)
            print(f"[DEBUG] Auth token: {auth_token}")
            print(f"[DEBUG] Current user ID: {user_id}")
        
        # Check if session is valid
        if action in ['submit_solution', 'get_stats', 'create_puzzle']:
            if not auth_token:
                print("[ERROR] Missing auth token")
                response = {'status': 'error', 'message': 'Login required'}
                client_socket.send(json.dumps(response).encode('utf-8'))
                return
            
            if not user_id:
                print(f"[ERROR] Invalid auth token: {auth_token}")
                response = {'status': 'error', 'message': 'Session expired, please log in again'}
                client_socket.send(json.dumps(response).encode('utf-8'))
                return
        
        if action == 'get_puzzles':
            puzzles = puzzle_manager.get_puzzle_list(
                sort_by=payload.get('sort_by', 'date'),
                order=payload.get('order', 'desc'),
                tag=payload.get('tag')
            )
            response = {'status': 'success', 'data': {'puzzles': puzzles}}
            
        elif action == 'get_puzzle':
            puzzle_id = payload.get('puzzle_id')
            puzzle = puzzle_manager.get_puzzle(puzzle_id)
            if puzzle:
                response = {'status': 'success', 'data': {'puzzle': puzzle}}
            else:
                response = {'status': 'error', 'message': 'Puzzle does not exist'}
                
        elif action == 'submit_solution':
            puzzle_id = payload.get('puzzle_id')
            submitted_grid = payload.get('grid')  # Use 'grid' instead of 'submitted_grid'
            time_taken = payload.get('time_taken', 0)
            
            if not puzzle_id or not submitted_grid:
                response = {'status': 'error', 'message': 'Missing required submission information'}
            else:
                try:
                    print(f"[DEBUG] Submitting answer - puzzle_id: {puzzle_id}, user_id: {user_id}")
                    is_correct, message = submission_manager.submit_solution(
                        puzzle_id, 
                        user_id, 
                        submitted_grid,
                        time_taken
                    )
                    response = {
                        'status': 'success', 
                        'data': {
                            'is_correct': is_correct, 
                            'message': message
                        }
                    }
                except Exception as e:
                    print(f"[ERROR] Error occurred while submitting answer: {e}")
                    response = {'status': 'error', 'message': f'Submission failed: {str(e)}'}
            
        elif action == 'get_stats':
            stats = stats_manager.get_user_statistics(user_id)
            response = {'status': 'success', 'data': stats}
            
        elif action == 'get_leaderboard':
            leaderboard = stats_manager.get_leaderboard()
            response = leaderboard
            
        elif action == 'get_recent_activity':
            activities = stats_manager.get_recent_activity()
            response = activities
            
        elif action == 'create_puzzle':
            title = payload.get('title')
            grid = payload.get('grid')
            clues = payload.get('clues')
            solution_key = payload.get('solution_key')
            tags = payload.get('tags', [])
            
            if not all([title, grid, clues, solution_key]):
                response = {'status': 'error', 'message': 'Missing required puzzle information'}
            else:
                puzzle_id = puzzle_manager.create_puzzle(title, grid, clues, solution_key, tags, user_id)
                if puzzle_id:
                    response = {'status': 'success', 'data': {'puzzle_id': puzzle_id}}
                else:
                    response = {'status': 'error', 'message': 'Failed to create puzzle'}
            
        else:
            response = {'status': 'error', 'message': 'Unknown action'}
        
        print(f"[DEBUG] Sending response: {response}")
        client_socket.send(json.dumps(response).encode('utf-8'))
        
    except json.JSONDecodeError:
        print("[ERROR] JSON parsing failed")
        response = {'status': 'error', 'message': 'JSON format error'}
        client_socket.send(json.dumps(response).encode('utf-8'))
    except Exception as e:
        print(f"[ERROR] Failed to handle request: {e}")
        response = {'status': 'error', 'message': str(e)}
        client_socket.send(json.dumps(response).encode('utf-8'))
    finally:
        client_socket.close()

def main():
    host = 'localhost'
    port = 5001
    
    puzzle_manager = PuzzleManager()
    submission_manager = SubmissionManager()
    stats_manager = StatisticsManager()
    
    # Create a new SessionManager instance and initialize database connection
    session_manager = SessionManager()
    
    # Ensure database tables are created
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Create sessions table (if not exists)
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expiry REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"[ERROR] Failed to initialize database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"Puzzle server is listening on {host}:{port}")
    
    while True:
        try:
            client_socket, address = server_socket.accept()
            print(f"Accepted connection from {address}")
            
            client_thread = threading.Thread(
                target=handle_client_request,
                args=(client_socket, puzzle_manager, submission_manager, stats_manager, session_manager)
            )
            client_thread.start()
            
        except KeyboardInterrupt:
            print("\nShutting down server...")
            break
        except Exception as e:
            print(f"[ERROR] Server error: {e}")
    
    server_socket.close()

if __name__ == "__main__":
    main() 