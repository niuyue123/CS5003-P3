import socket
import json
import hashlib
import time
import re
import sqlite3

DATABASE = 'DATABASE-puzzles.db'

def init_db():
    """初始化数据库并创建users表"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to initialize database: {e}")
    finally:
        conn.close()

class SessionManager:
    def __init__(self):
        # 创建会话表
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                        token TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        expiry REAL NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id))''')
            conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] Failed to initialize sessions table: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def create_session(self, user_id):
        """创建新会话并返回令牌"""
        try:
            timestamp = int(time.time())
            token = hashlib.sha256(f"{user_id}-{timestamp}".encode()).hexdigest()
            expiry = time.time() + 1800  # 30分钟过期
            
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            
            # 删除该用户的旧会话
            c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            
            # 创建新会话
            c.execute("INSERT INTO sessions (token, user_id, expiry) VALUES (?, ?, ?)",
                     (token, user_id, expiry))
            conn.commit()
            return token
        except sqlite3.Error as e:
            print(f"[DB ERROR] Failed to create session: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def validate_session(self, token):
        """验证会话令牌是否有效且未过期"""
        if not isinstance(token, str) or len(token) != 64 or not token.isalnum():
            return False
            
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            
            # 清理过期会话
            c.execute("DELETE FROM sessions WHERE expiry < ?", (time.time(),))
            
            # 检查会话是否存在且未过期
            c.execute("SELECT COUNT(*) FROM sessions WHERE token = ? AND expiry > ?",
                     (token, time.time()))
            count = c.fetchone()[0]
            
            conn.commit()
            return count > 0
        except sqlite3.Error as e:
            print(f"[DB ERROR] Failed to validate session: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def get_user_id(self, token):
        """获取会话对应的用户ID"""
        if not isinstance(token, str) or len(token) != 64 or not token.isalnum():
            return None
            
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            
            # 清理过期会话
            c.execute("DELETE FROM sessions WHERE expiry < ?", (time.time(),))
            
            # 获取用户ID
            c.execute("SELECT user_id FROM sessions WHERE token = ? AND expiry > ?",
                     (token, time.time()))
            row = c.fetchone()
            
            conn.commit()
            return row[0] if row else None
        except sqlite3.Error as e:
            print(f"[DB ERROR] Failed to get user_id: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def destroy_session(self, token):
        """销毁会话"""
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] Failed to destroy session: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

def hash_password(password):
    """使用SHA-256哈希密码"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    return hashlib.sha256(password).hexdigest()

def make_response(status, message, data=None):
    """生成标准响应格式"""
    return json.dumps({
        "status": status,
        "message": message,
        "data": data or {}
    })

def is_valid_username(username):
    """验证用户名是否合法（字母数字，3-20字符）"""
    return bool(re.fullmatch(r"^[a-zA-Z0-9]{3,20}$", username))

def handle_login(username, password):
    """处理登录请求"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        # 对接收到的原始密码进行加密后再比较
        password_hash = hash_password(password)
        print(f"[DEBUG] Login attempt - Username: {username}, Hash: {password_hash}")  # 添加调试信息
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        if row:
            print(f"[DEBUG] Found user - ID: {row[0]}, Stored Hash: {row[1]}")  # 添加调试信息
        if row and row[1] == password_hash:  # 比较哈希值
            # 更新最后登录时间
            c.execute('''INSERT OR REPLACE INTO user_stats (user_id, last_login)
                        VALUES (?, CURRENT_TIMESTAMP)''', (row[0],))
            conn.commit()
            return row[0]  # 返回用户ID
        return None
    except sqlite3.Error as e:
        print(f"[DB ERROR] Login error: {e}")
        return None
    finally:
        conn.close()

def handle_client_request(data, session_manager):
    try:
        request = json.loads(data)
        action = request.get("action")
        payload = request.get("payload", {})
        token = request.get("auth_token")

        if action == "register":
            username = payload.get("username", "").strip()
            password = payload.get("password", "").strip()  # 接收原始密码

            if not username or not password:
                return make_response("error", "用户名和密码不能为空")

            if not is_valid_username(username):
                return make_response("error", "用户名必须是3-20个字母或数字")

            if len(password) < 3:
                return make_response("error", "密码至少需要3个字符")

            try:
                conn = sqlite3.connect(DATABASE)
                c = conn.cursor()
                # 在服务器端对密码进行加密
                password_hash = hash_password(password)
                c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                         (username, password_hash))
                user_id = c.lastrowid
                c.execute("INSERT INTO user_stats (user_id) VALUES (?)", (user_id,))
                conn.commit()
                return make_response("success", "注册成功")
            except sqlite3.IntegrityError:
                return make_response("error", "用户名已存在")
            except sqlite3.Error as e:
                return make_response("error", f"注册失败: {e}")
            finally:
                conn.close()

        elif action == "login":
            username = payload.get("username", "").strip()
            password = payload.get("password", "").strip()  # 接收原始密码

            if not username or not password:
                return make_response("error", "用户名和密码不能为空")

            user_id = handle_login(username, password)  # 传递原始密码
            if user_id:
                token = session_manager.create_session(user_id)
                return make_response("success", "登录成功", {
                    "auth_token": token,
                    "username": username
                })
            return make_response("error", "用户名或密码错误")

        elif action == "logout":
            if session_manager.validate_session(token):
                session_manager.destroy_session(token)
                return make_response("success", "注销成功")
            return make_response("error", "无效或过期的会话")

        else:
            return make_response("error", "未知操作")

    except json.JSONDecodeError:
        return make_response("error", "无效的请求格式")
    except Exception as e:
        return make_response("error", f"处理请求时出错: {str(e)}")

def recv_until_newline(sock):
    """从socket接收数据直到遇到换行符"""
    buffer = ''
    try:
        while True:
            chunk = sock.recv(4096).decode('utf-8')
            if not chunk:
                break
            buffer += chunk
            if '\n' in buffer:
                break
        return buffer.strip()
    except (ConnectionResetError, OSError) as e:
        print(f"[SOCKET ERROR] 接收数据时出错: {e}")
        return ''

def start_server(host, port):
    """启动服务器并处理客户端连接"""
    init_db()  # 初始化数据库
    session_manager = SessionManager()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"服务器正在监听 {host}:{port}...")

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                with client_socket:
                    print(f"来自 {client_address} 的连接")
                    data = recv_until_newline(client_socket)
                    if not data:
                        continue
                    print(f"收到请求: {data}")
                    response = handle_client_request(data, session_manager)
                    client_socket.sendall((response + '\n').encode('utf-8'))
            except Exception as e:
                print(f"[SERVER ERROR] 处理客户端请求时出错: {e}")

if __name__ == "__main__":
    start_server("localhost", 5000)
