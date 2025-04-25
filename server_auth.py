import socket
import json
import hashlib
import time
import re
import sqlite3

DATABASE = 'DATABASE-puzzles.db'

def init_db():
    """Initialize database and create users table"""
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
        # Create sessions table
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
        """Create new session and return token"""
        try:
            timestamp = int(time.time())
            token = hashlib.sha256(f"{user_id}-{timestamp}".encode()).hexdigest()
            expiry = time.time() + 1800  # 30 minutes expiry
            
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            
            # Delete old sessions for this user
            c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            
            # Create new session
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
        """Validate if session token is valid and not expired"""
        if not isinstance(token, str) or len(token) != 64 or not token.isalnum():
            return False
            
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            
            # Clean expired sessions
            c.execute("DELETE FROM sessions WHERE expiry < ?", (time.time(),))
            
            # Check if session exists and not expired
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
        """Get user ID associated with session"""
        if not isinstance(token, str) or len(token) != 64 or not token.isalnum():
            return None
            
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            
            # Clean expired sessions
            c.execute("DELETE FROM sessions WHERE expiry < ?", (time.time(),))
            
            # Get user ID
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
        """Destroy session"""
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
    """Hash password using SHA-256"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    return hashlib.sha256(password).hexdigest()

def make_response(status, message, data=None):
    """Generate standard response format"""
    return json.dumps({
        "status": status,
        "message": message,
        "data": data or {}
    })

def is_valid_username(username):
    """Validate username (alphanumeric, 3-20 characters)"""
    return bool(re.fullmatch(r"^[a-zA-Z0-9]{3,20}$", username))

def handle_login(username, password):
    """Handle login request"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        # Hash received raw password before comparison
        password_hash = hash_password(password)
        print(f"[DEBUG] Login attempt - Username: {username}, Hash: {password_hash}")
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        if row:
            print(f"[DEBUG] Found user - ID: {row[0]}, Stored Hash: {row[1]}")
        if row and row[1] == password_hash:  # Compare hash values
            # Update last login time
            c.execute('''INSERT OR REPLACE INTO user_stats (user_id, last_login)
                        VALUES (?, CURRENT_TIMESTAMP)''', (row[0],))
            conn.commit()
            return row[0]  # Return user ID
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
            password = payload.get("password", "").strip()  # Receive raw password

            if not username or not password:
                return make_response("error", "Username and password cannot be empty")

            if not is_valid_username(username):
                return make_response("error", "Username must be 3-20 alphanumeric characters")

            if len(password) < 3:
                return make_response("error", "Password must be at least 3 characters")

            try:
                conn = sqlite3.connect(DATABASE)
                c = conn.cursor()
                # Hash password on server side
                password_hash = hash_password(password)
                c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                         (username, password_hash))
                user_id = c.lastrowid
                c.execute("INSERT INTO user_stats (user_id) VALUES (?)", (user_id,))
                conn.commit()
                return make_response("success", "Registration successful")
            except sqlite3.IntegrityError:
                return make_response("error", "Username already exists")
            except sqlite3.Error as e:
                return make_response("error", f"Registration failed: {e}")
            finally:
                conn.close()

        elif action == "login":
            username = payload.get("username", "").strip()
            password = payload.get("password", "").strip()  # Receive raw password

            if not username or not password:
                return make_response("error", "Username and password cannot be empty")

            user_id = handle_login(username, password)  # Pass raw password
            if user_id:
                token = session_manager.create_session(user_id)
                return make_response("success", "Login successful", {
                    "auth_token": token,
                    "username": username
                })
            return make_response("error", "Invalid username or password")

        elif action == "logout":
            if session_manager.validate_session(token):
                session_manager.destroy_session(token)
                return make_response("success", "Logout successful")
            return make_response("error", "Invalid or expired session")

        else:
            return make_response("error", "Unknown operation")

    except json.JSONDecodeError:
        return make_response("error", "Invalid request format")
    except Exception as e:
        return make_response("error", f"Error processing request: {str(e)}")

def recv_until_newline(sock):
    """Receive data from socket until newline"""
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
        print(f"[SOCKET ERROR] Error receiving data: {e}")
        return ''

def start_server(host, port):
    """Start server and handle client connections"""
    init_db()  # Initialize database
    session_manager = SessionManager()

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
                    response = handle_client_request(data, session_manager)
                    client_socket.sendall((response + '\n').encode('utf-8'))
            except Exception as e:
                print(f"[SERVER ERROR] Error handling client request: {e}")

if __name__ == "__main__":
    start_server("localhost", 5000)
