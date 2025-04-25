import subprocess
import sys
import time
import os

def start_auth_server():
    try:
        auth_process = subprocess.Popen([sys.executable, "server_auth.py"])
        print("认证服务器已启动")
        return auth_process
    except Exception as e:
        print(f"启动认证服务器失败: {e}")
        return None

def start_puzzle_server():
    try:
        puzzle_process = subprocess.Popen([sys.executable, "server_puzzle.py"])
        print("谜题服务器已启动")
        return puzzle_process
    except Exception as e:
        print(f"启动谜题服务器失败: {e}")
        return None

def start_client():
    try:
        client_process = subprocess.Popen([sys.executable, "client_puzzle.py"])
        print("客户端已启动")
        return client_process
    except Exception as e:
        print(f"启动客户端失败: {e}")
        return None

def main():
    processes = []
    
    # 启动认证服务器
    auth_process = start_auth_server()
    if auth_process:
        processes.append(auth_process)
        time.sleep(1)  # 等待认证服务器启动
    
    # 启动谜题服务器
    puzzle_process = start_puzzle_server()
    if puzzle_process:
        processes.append(puzzle_process)
        time.sleep(1)  # 等待谜题服务器启动
    
    # 启动客户端
    client_process = start_client()
    if client_process:
        processes.append(client_process)
    
    try:
        # 等待任意子进程结束
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\n正在关闭所有进程...")
        for process in processes:
            process.terminate()

if __name__ == "__main__":
    main() 