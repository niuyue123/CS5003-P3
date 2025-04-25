import subprocess
import sys
import time
import os

def start_auth_server():
    try:
        auth_process = subprocess.Popen([sys.executable, "server_auth.py"])
        print("Authentication server started")
        return auth_process
    except Exception as e:
        print(f"Failed to start authentication server: {e}")
        return None

def start_puzzle_server():
    try:
        puzzle_process = subprocess.Popen([sys.executable, "server_puzzle.py"])
        print("Puzzle server started")
        return puzzle_process
    except Exception as e:
        print(f"Failed to start puzzle server: {e}")
        return None

def start_client():
    try:
        client_process = subprocess.Popen([sys.executable, "client_puzzle.py"])
        print("Client started")
        return client_process
    except Exception as e:
        print(f"Failed to start client: {e}")
        return None

def main():
    processes = []
    
    # Start authentication server
    auth_process = start_auth_server()
    if auth_process:
        processes.append(auth_process)
        time.sleep(1)  # Wait for authentication server to start
    
    # Start puzzle server
    puzzle_process = start_puzzle_server()
    if puzzle_process:
        processes.append(puzzle_process)
        time.sleep(1)  # Wait for puzzle server to start
    
    # Start client
    client_process = start_client()
    if client_process:
        processes.append(client_process)
    
    try:
        # Wait for any child process to end
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\nClosing all processes...")
        for process in processes:
            process.terminate()

if __name__ == "__main__":
    main() 