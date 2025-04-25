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
        print(f"[DEBUG] 获取谜题列表参数: sort_by={sort_by}, order={order}, tag={tag}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 转换排序字段
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
            
            print(f"[DEBUG] 找到 {len(puzzles)} 个谜题")
            return puzzles
            
        except Exception as e:
            print(f"[ERROR] 获取谜题列表失败: {e}")
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
            print(f"[ERROR] 获取谜题详情失败: {e}")
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
            print(f"[ERROR] 创建谜题失败: {e}")
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
                print("[ERROR] 提交参数不完整")
                return False, "提交参数不完整"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取谜题的正确答案
            cursor.execute("SELECT solution_key FROM puzzles WHERE id = ?", (puzzle_id,))
            row = cursor.fetchone()
            if not row:
                print(f"[ERROR] 谜题不存在: {puzzle_id}")
                return False, "谜题不存在"
            
            try:
                solution_key = json.loads(row[0])
                if isinstance(submitted_grid, str):
                    submitted_grid = json.loads(submitted_grid)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON解析失败: {e}")
                return False, "答案格式错误"
            
            # 验证网格大小
            if (len(submitted_grid) != len(solution_key) or 
                any(len(row) != len(solution_key[0]) for row in submitted_grid)):
                print("[ERROR] 提交的答案网格大小不正确")
                return False, "答案格式不正确"
            
            # 检查答案
            incorrect_cells = []
            is_correct = True
            for i, row in enumerate(submitted_grid):
                for j, cell in enumerate(row):
                    if solution_key[i][j] != '#' and cell.upper() != solution_key[i][j].upper():
                        incorrect_cells.append([i, j])
                        is_correct = False
            
            # 记录提交
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
            
            # 更新谜题统计
            if is_correct:
                cursor.execute("""
                    UPDATE puzzles 
                    SET solved_count = solved_count + 1,
                        last_solved = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (puzzle_id,))
                
                # 更新用户统计
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
            return is_correct, "答案正确！" if is_correct else f"答案错误，有 {len(incorrect_cells)} 个单元格不正确"
            
        except Exception as e:
            print(f"[ERROR] 提交答案失败: {e}")
            return False, f"提交失败: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()

    def handle_submit_answer(self, user_id, puzzle_id, answer, time_taken):
        conn = sqlite3.connect(DATABASE)
        try:
            cursor = conn.cursor()
            # 获取正确答案
            cursor.execute("SELECT answer FROM puzzles WHERE id = ?", (puzzle_id,))
            row = cursor.fetchone()
            if not row:
                return {'status': 'error', 'message': '找不到该谜题'}
            
            correct_answer = row[0]
            is_correct = answer.lower().strip() == correct_answer.lower().strip()
            result = 'correct' if is_correct else 'incorrect'
            
            # 记录提交
            cursor.execute("""
                INSERT INTO submissions (user_id, puzzle_id, answer, time_taken, result, timestamp)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (user_id, puzzle_id, answer, time_taken, result))
            
            conn.commit()
            return {
                'status': 'success',
                'correct': is_correct,
                'message': '答案正确！' if is_correct else '答案错误，请重试'
            }
        except Exception as e:
            print(f"[ERROR] 提交答案失败: {e}")
            return {'status': 'error', 'message': f'提交答案失败: {str(e)}'}
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
            
            # 获取用户统计信息
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
            print(f"[ERROR] 获取用户统计信息失败: {e}")
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
            print(f"[ERROR] 获取排行榜失败: {e}")
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
            print(f"[ERROR] 获取最近活动失败: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if 'conn' in locals():
                conn.close()

def handle_client_request(client_socket, puzzle_manager, submission_manager, stats_manager, session_manager):
    try:
        data = client_socket.recv(4096).decode('utf-8')
        if not data:
            return
        
        print(f"[DEBUG] 收到请求: {data}")
        request = json.loads(data)
        
        action = request.get('action')
        payload = request.get('payload', {})
        auth_token = request.get('auth_token')
        
        response = {'status': 'error', 'message': '未知错误'}
        
        # 获取用户ID（如果有认证令牌）
        user_id = None
        if auth_token:
            user_id = session_manager.get_user_id(auth_token)
            print(f"[DEBUG] 认证令牌: {auth_token}")
            print(f"[DEBUG] 当前用户ID: {user_id}")
        
        # 检查会话是否有效
        if action in ['submit_solution', 'get_stats', 'create_puzzle']:
            if not auth_token:
                print("[ERROR] 缺少认证令牌")
                response = {'status': 'error', 'message': '需要登录'}
                client_socket.send(json.dumps(response).encode('utf-8'))
                return
            
            if not user_id:
                print(f"[ERROR] 无效的认证令牌: {auth_token}")
                response = {'status': 'error', 'message': '会话已过期，请重新登录'}
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
                response = {'status': 'error', 'message': '谜题不存在'}
                
        elif action == 'submit_solution':
            puzzle_id = payload.get('puzzle_id')
            submitted_grid = payload.get('grid')  # 使用 'grid' 而不是 'submitted_grid'
            time_taken = payload.get('time_taken', 0)
            
            if not puzzle_id or not submitted_grid:
                response = {'status': 'error', 'message': '缺少必要的提交信息'}
            else:
                try:
                    print(f"[DEBUG] 提交答案 - puzzle_id: {puzzle_id}, user_id: {user_id}")
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
                    print(f"[ERROR] 提交答案时发生错误: {e}")
                    response = {'status': 'error', 'message': f'提交答案失败: {str(e)}'}
            
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
                response = {'status': 'error', 'message': '缺少必要的谜题信息'}
            else:
                puzzle_id = puzzle_manager.create_puzzle(title, grid, clues, solution_key, tags, user_id)
                if puzzle_id:
                    response = {'status': 'success', 'data': {'puzzle_id': puzzle_id}}
                else:
                    response = {'status': 'error', 'message': '创建谜题失败'}
            
        else:
            response = {'status': 'error', 'message': '未知操作'}
        
        print(f"[DEBUG] 发送响应: {response}")
        client_socket.send(json.dumps(response).encode('utf-8'))
        
    except json.JSONDecodeError:
        print("[ERROR] JSON解析失败")
        response = {'status': 'error', 'message': 'JSON格式错误'}
        client_socket.send(json.dumps(response).encode('utf-8'))
    except Exception as e:
        print(f"[ERROR] 处理请求失败: {e}")
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
    
    # 创建一个新的 SessionManager 实例并初始化数据库连接
    session_manager = SessionManager()
    
    # 确保数据库表已创建
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 创建 sessions 表（如果不存在）
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expiry REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"[ERROR] 初始化数据库失败: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"谜题服务器正在监听 {host}:{port}")
    
    while True:
        try:
            client_socket, address = server_socket.accept()
            print(f"接受来自 {address} 的连接")
            
            client_thread = threading.Thread(
                target=handle_client_request,
                args=(client_socket, puzzle_manager, submission_manager, stats_manager, session_manager)
            )
            client_thread.start()
            
        except KeyboardInterrupt:
            print("\n关闭服务器...")
            break
        except Exception as e:
            print(f"[ERROR] 服务器错误: {e}")
    
    server_socket.close()

if __name__ == "__main__":
    main() 