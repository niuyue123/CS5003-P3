import socket
import json
import hashlib
import os

class GameClient:
    TOKEN_FILE = "auth_token.txt"

    def __init__(self, server_address):
        self.server_address = server_address
        self.auth_token = self.load_token()

    def hash_password(self, password):
        """Hash password with SHA-256"""
        try:
            return hashlib.sha256(password.encode('utf-8')).hexdigest()
        except Exception as e:
            raise RuntimeError(f"Password hashing failed: {e}")

    def create_request(self, action, payload):
        """Construct a JSON request"""
        try:
            request = {
                "action": action,
                "auth_token": self.auth_token,
                "payload": payload or {}
            }
            return json.dumps(request) + '\n'
        except Exception as e:
            raise ValueError(f"Failed to create request: {e}")

    def send_request(self, action, payload):
        """Send a request to the server and receive response"""
        request = self.create_request(action, payload)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(self.server_address)
                s.sendall(request.encode('utf-8'))

                buffer = ""
                while True:
                    chunk = s.recv(4096).decode('utf-8')
                    if not chunk:
                        break
                    buffer += chunk
                    if '\n' in buffer:
                        break

                response_str = buffer.strip()
                return json.loads(response_str)
        except socket.error as e:
            raise ConnectionError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")

    def register(self, username, password):
        """Register a new user"""
        try:
            hashed = self.hash_password(password)
            payload = {"username": username, "password": hashed}
            response = self.send_request("register", payload)
            return response
        except Exception as e:
            print(f"[Register] Error: {e}")
            return None

    def login(self, username, password):
        """Login an existing user"""
        try:
            hashed = self.hash_password(password)
            payload = {"username": username, "password": hashed}
            response = self.send_request("login", payload)

            if response.get("status") == "success":
                token = response.get("data", {}).get("auth_token")
                if token:
                    self.auth_token = token
                    self.save_token(token)
            else:
                print(f"[Login] Failed: {response.get('message', 'Unknown error')}")
            return response
        except Exception as e:
            print(f"[Login] Error: {e}")
            return None

    def logout(self):
        """Logout and clear token"""
        try:
            response = self.send_request("logout", {})
            self.clear_token()
            return response
        except Exception as e:
            print(f"[Logout] Error: {e}")
            return None

    def handle_invalid_token(self, response):
        """Check and handle invalid token"""
        if response and response.get("status") == "error" and \
           response.get("message") == "Invalid or expired session token":
            print("[Token] Invalid or expired. Please log in again.")
            self.clear_token()
            return True
        return False

    def save_token(self, token):
        """Save auth token to file"""
        try:
            with open(self.TOKEN_FILE, "w") as f:
                f.write(token)
        except IOError as e:
            print(f"[Token] Save failed: {e}")

    def load_token(self):
        """Load auth token from file"""
        try:
            with open(self.TOKEN_FILE, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
        except IOError as e:
            print(f"[Token] Load failed: {e}")
            return None

    def clear_token(self):
        """Remove stored auth token"""
        try:
            os.remove(self.TOKEN_FILE)
        except FileNotFoundError:
            pass
        except IOError as e:
            print(f"[Token] Clear failed: {e}")

