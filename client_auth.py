import socket
import json
import os

class GameClient:
    TOKEN_FILE = "auth_token.txt"

    def __init__(self, server_address):
        self.server_address = server_address
        self._auth_token = None
        self.load_token()

    @property
    def auth_token(self):
        return self._auth_token

    @auth_token.setter
    def auth_token(self, value):
        self._auth_token = value
        if value:
            self.save_token(value)
        else:
            self.clear_token()

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
        try:
            request = {
                "action": action,
                "auth_token": self.auth_token,
                "payload": payload or {}
            }
            request_str = json.dumps(request) + '\n'
            print(f"[DEBUG] 发送请求：{request_str}")  # 调试信息
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(self.server_address)
                s.sendall(request_str.encode('utf-8'))
                
                buffer = ""
                while True:
                    chunk = s.recv(4096).decode('utf-8')
                    if not chunk:
                        break
                    buffer += chunk
                    if '\n' in buffer:
                        break
                
                response_str = buffer.strip()
                print(f"[DEBUG] 收到响应：{response_str}")  # 调试信息
                
                try:
                    response = json.loads(response_str)
                    if self.handle_invalid_token(response):
                        return {"status": "error", "message": "会话已过期，请重新登录"}
                    return response
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSON解析错误：{e}, 原始响应：{response_str}")  # 调试信息
                    return None
                
        except socket.error as e:
            print(f"[DEBUG] 网络错误：{e}")  # 调试信息
            raise ConnectionError(f"Network error: {e}")
        except Exception as e:
            print(f"[DEBUG] 未知错误：{e}")  # 调试信息
            raise RuntimeError(f"Unexpected error: {e}")

    def register(self, username, password):
        """Register a new user"""
        try:
            payload = {"username": username, "password": password}
            response = self.send_request("register", payload)
            return response
        except Exception as e:
            print(f"[Register] Error: {e}")
            return None

    def login(self, username, password):
        """Login an existing user"""
        try:
            payload = {"username": username, "password": password}
            response = self.send_request("login", payload)

            if response.get("status") == "success":
                token = response.get("data", {}).get("auth_token")
                if token:
                    self.auth_token = token
                    print(f"[DEBUG] 登录成功，令牌已更新: {token}")
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
            self.auth_token = None
            return response
        except Exception as e:
            print(f"[Logout] Error: {e}")
            return None

    def handle_invalid_token(self, response):
        """Check and handle invalid token"""
        if response and response.get("status") == "error" and \
           ("Invalid" in response.get("message", "") or 
            "expired" in response.get("message", "") or
            "需要登录" in response.get("message", "")):
            print("[Token] Invalid or expired. Please log in again.")
            self.auth_token = None
            return True
        return False

    def save_token(self, token):
        """Save auth token to file"""
        try:
            with open(self.TOKEN_FILE, "w") as f:
                f.write(token)
            print(f"[DEBUG] 令牌已保存到文件: {token}")
        except IOError as e:
            print(f"[Token] Save failed: {e}")

    def load_token(self):
        """Load auth token from file"""
        try:
            with open(self.TOKEN_FILE, "r") as f:
                token = f.read().strip()
                if token:
                    self._auth_token = token
                    print(f"[DEBUG] 从文件加载令牌: {token}")
                return token
        except FileNotFoundError:
            return None
        except IOError as e:
            print(f"[Token] Load failed: {e}")
            return None

    def clear_token(self):
        """Remove stored auth token"""
        try:
            if os.path.exists(self.TOKEN_FILE):
                os.remove(self.TOKEN_FILE)
                print("[DEBUG] 令牌文件已删除")
        except IOError as e:
            print(f"[Token] Clear failed: {e}")
        self._auth_token = None

