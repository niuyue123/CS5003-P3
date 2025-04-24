import socket
import json
import hashlib
import time
import re
import sqlite3

DATABASE = "users.db"

# Initialize the database and create the 'users' table if it doesn't exist
def init_db():
    try:
        conn = sqlite3.connect(DATABASE)  # Connect to the SQLite database
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY, 
                        password_hash TEXT)''')  # Create table if not exists
        conn.commit()  # Commit the transaction
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to initialize database: {e}")
    finally:
        conn.close()  # Close the database connection

# Load all users from the database
def load_users():
    try:
        conn = sqlite3.connect(DATABASE)  # Connect to the SQLite database
        c = conn.cursor()
        c.execute("SELECT username, password_hash FROM users")  # Retrieve all users
        rows = c.fetchall()  # Fetch all results
        return {row[0]: row[1] for row in rows}  # Return users as a dictionary
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to load users: {e}")
        return {}  # Return empty dictionary in case of error
    finally:
        conn.close()  # Close the database connection

# Save users to the database, updating existing ones if necessary
def save_users(users):
    try:
        conn = sqlite3.connect(DATABASE)  # Connect to the SQLite database
        c = conn.cursor()
        for username, password_hash in users.items():
            c.execute("INSERT OR REPLACE INTO users (username, password_hash) VALUES (?, ?)",
                      (username, password_hash))  # Insert or replace the user
        conn.commit()  # Commit the transaction
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to save users: {e}")
    finally:
        conn.close()  # Close the database connection

# Class to manage user sessions (login state)
class SessionManager:
    def __init__(self):
        self.sessions = {}  # Store active sessions in a dictionary

    # Create a new session for the user and return a token
    def create_session(self, user_id):
        timestamp = int(time.time())  # Current timestamp
        token = hashlib.sha256(f"{user_id}-{timestamp}".encode()).hexdigest()  # Generate a unique token
        self.sessions[token] = {"user_id": user_id, "expiry": time.time() + 1800}  # Store session with expiry
        return token

    # Validate if the session token is valid and not expired
    def validate_session(self, token):
        if not isinstance(token, str) or len(token) != 64 or not token.isalnum():
            return False  # Token format check
        session = self.sessions.get(token)
        if not session or time.time() > session["expiry"]:  # Check if session expired
            self.sessions.pop(token, None)  # Remove expired session
            return False
        return True

    # Destroy a session by removing the token
    def destroy_session(self, token):
        self.sessions.pop(token, None)

# Hash a password using SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Generate a standard response format for API calls
def make_response(status, message, data=None):
    return json.dumps({
        "status": status,
        "message": message,
        "data": data or {}
    })

# Validate if the username is alphanumeric and 3-20 characters long
def is_valid_username(username):
    return bool(re.fullmatch(r"^[a-zA-Z0-9]{3,20}$", username))

# Handle the login request by checking the provided credentials
def handle_login(username, hashed_password):
    users = load_users()  # Load all users
    stored_hash = users.get(username)  # Retrieve stored password hash for the username
    return stored_hash and stored_hash == hashed_password  # Return True if credentials match

# Receive data from a socket until a newline is encountered
def recv_until_newline(sock):
    buffer = ''
    try:
        while True:
            chunk = sock.recv(4096).decode('utf-8')  # Receive data in chunks
            if not chunk:
                break
            buffer += chunk
            if '\n' in buffer:  # Stop when newline is found
                break
        return buffer.strip()
    except (ConnectionResetError, OSError) as e:
        print(f"[SOCKET ERROR] Error receiving data: {e}")
        return ''  # Return empty string on error

# Handle client requests such as register, login, and logout
def handle_client_request(data, session_manager):
    try:
        request = json.loads(data)  # Parse the incoming JSON request
        action = request.get("action")  # Get the action from the request
        payload = request.get("payload", {})  # Extract payload
        token = request.get("auth_token")  # Extract token for session validation

        if action == "register":
            username = payload.get("username", "")
            password = payload.get("password", "")

            # Validate the username and password
            if not is_valid_username(username):
                return make_response("error", "Registration failed", {"username": "Invalid username, should be 3-20 alphanumeric characters"})

            users = load_users()
            if username in users:
                return make_response("error", "Registration failed", {"username": "Username already exists"})

            if len(password) < 8:
                return make_response("error", "Registration failed", {"password": "Password must be at least 8 characters long"})

            users[username] = hash_password(password)  # Save the new user with hashed password
            save_users(users)
            token = session_manager.create_session(username)
            return make_response("success", "Registration successful", {"auth_token": token})


        elif action == "login":
            username = payload.get("username", "")
            password = payload.get("password", "")
            hashed_password = hash_password(password)  # Hash the password before checking

            if handle_login(username, hashed_password):
                token = session_manager.create_session(username)  # Create a session token
                return make_response("success", "Login successful", {"auth_token": token})
            else:
                return make_response("error", "Invalid username or password")

        elif action == "logout":
            if session_manager.validate_session(token):  # Validate the session token
                session_manager.destroy_session(token)  # Destroy the session
                return make_response("success", "Logout successful")
            else:
                return make_response("error", "Invalid or expired session")

        else:
            return make_response("error", "Unknown action")

    except json.JSONDecodeError:
        return make_response("error", "Invalid request format, expected JSON")
    except Exception as e:
        return make_response("error", f"Error processing request: {str(e)}")

# Start the server and handle client connections
def start_server(host, port):
    session_manager = SessionManager()  # Initialize session manager
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Set socket options
        server_socket.bind((host, port))  # Bind server to host and port
        server_socket.listen(5)  # Start listening for incoming connections
        print(f"Server listening on {host}:{port}...")

        while True:
            try:
                client_socket, client_address = server_socket.accept()  # Accept a new client connection
                with client_socket:
                    print(f"Connection from {client_address}")
                    data = recv_until_newline(client_socket)  # Receive client data
                    if not data:
                        continue
                    print(f"Received request: {data}")
                    response = handle_client_request(data, session_manager)  # Handle the request
                    client_socket.sendall((response + '\n').encode('utf-8'))  # Send response back to client
            except Exception as e:
                print(f"[SERVER ERROR] Error handling client request: {e}")
