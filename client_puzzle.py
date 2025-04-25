import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
from client_auth import GameClient

class PuzzleClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Crossword Puzzle")
        self.root.geometry("1200x800")
        
        # Initialize two different clients
        self.auth_client = GameClient(("localhost", 5000))  # Authentication server
        self.puzzle_client = GameClient(("localhost", 5001))  # Puzzle server
        self.current_user = None
        self.start_time = None
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel for puzzle solving
        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Right panel for stats and activity
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Login/Register frame
        self.auth_frame = ttk.Frame(self.left_panel)
        self.auth_frame.grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(self.auth_frame, text="Username:").grid(row=0, column=0)
        self.username_entry = ttk.Entry(self.auth_frame)
        self.username_entry.grid(row=0, column=1)
        
        ttk.Label(self.auth_frame, text="Password:").grid(row=1, column=0)
        self.password_entry = ttk.Entry(self.auth_frame, show="*")
        self.password_entry.grid(row=1, column=1)
        
        ttk.Button(self.auth_frame, text="Login", 
                  command=self.login).grid(row=2, column=0, pady=5)
        ttk.Button(self.auth_frame, text="Register", 
                  command=self.register).grid(row=2, column=1, pady=5)
        
        # Statistics frame
        self.stats_frame = ttk.LabelFrame(self.right_panel, text="Your Statistics")
        self.stats_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        self.stats_labels = {}
        for stat in ['puzzles_solved', 'avg_time', 'last_login']:
            self.stats_labels[stat] = ttk.Label(self.stats_frame, text="")
            self.stats_labels[stat].pack(pady=5)
        
        # Leaderboard frame
        self.leaderboard_frame = ttk.LabelFrame(self.right_panel, text="排行榜")
        self.leaderboard_frame.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 排行榜排序选项
        sort_frame = ttk.Frame(self.leaderboard_frame)
        sort_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(sort_frame, text="排序方式:").pack(side=tk.LEFT, padx=5)
        self.leaderboard_sort = ttk.Combobox(sort_frame,
                                           values=['按速度', '按正确率'],
                                           state='readonly',
                                           width=10)
        self.leaderboard_sort.pack(side=tk.LEFT, padx=5)
        self.leaderboard_sort.set('按速度')
        self.leaderboard_sort.bind('<<ComboboxSelected>>', lambda e: self.update_leaderboard())
        
        # 创建带滚动条的排行榜列表框
        list_frame = ttk.Frame(self.leaderboard_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.leaderboard_list = tk.Listbox(list_frame, height=12, width=50,
                                         yscrollcommand=scrollbar.set)
        self.leaderboard_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.leaderboard_list.yview)
        
        # Recent activity frame
        self.activity_frame = ttk.LabelFrame(self.right_panel, text="最近活动")
        self.activity_frame.grid(row=2, column=0, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建带滚动条的活动列表框
        activity_list_frame = ttk.Frame(self.activity_frame)
        activity_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        activity_scrollbar = ttk.Scrollbar(activity_list_frame)
        activity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.activity_list = tk.Listbox(activity_list_frame, height=12, width=50,
                                      yscrollcommand=activity_scrollbar.set)
        self.activity_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        activity_scrollbar.config(command=self.activity_list.yview)
        
        # Puzzle filter frame
        self.filter_frame = ttk.Frame(self.left_panel)
        self.filter_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Label(self.filter_frame, text="Sort by:").grid(row=0, column=0)
        self.sort_by = ttk.Combobox(self.filter_frame, 
                                   values=['date', 'title', 'solved_count'],
                                   state='readonly')
        self.sort_by.grid(row=0, column=1)
        self.sort_by.set('date')
        
        ttk.Label(self.filter_frame, text="Order:").grid(row=0, column=2)
        self.order = ttk.Combobox(self.filter_frame,
                                 values=['asc', 'desc'],
                                 state='readonly')
        self.order.grid(row=0, column=3)
        self.order.set('desc')
        
        ttk.Label(self.filter_frame, text="Tag:").grid(row=0, column=4)
        self.tag = ttk.Entry(self.filter_frame)
        self.tag.grid(row=0, column=5)
        
        ttk.Button(self.filter_frame, text="Apply Filters",
                  command=self.load_puzzles).grid(row=0, column=6, padx=5)
        
        # Puzzle selection
        self.puzzle_list = ttk.Combobox(self.left_panel, state="readonly", width=50)
        self.puzzle_list.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        # Load puzzle button
        ttk.Button(self.left_panel, text="Load Puzzle", 
                  command=self.load_selected_puzzle).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Crossword grid
        self.grid_frame = ttk.Frame(self.left_panel)
        self.grid_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        
        # Clues frame
        self.clues_frame = ttk.Frame(self.left_panel)
        self.clues_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        # Submit button
        ttk.Button(self.left_panel, text="Submit Answer", 
                  command=self.submit_solution).grid(row=6, column=0, columnspan=2, pady=10)
        
        self.current_puzzle = None
        self.grid_entries = []
        
        # Start periodic updates
        self.root.after(30000, self.periodic_update)  # Update every 30 seconds
    
    def periodic_update(self):
        if self.current_user:
            self.update_leaderboard()
            self.update_activity()
        self.root.after(30000, self.periodic_update)
    
    def update_leaderboard(self):
        if not self.current_user:
            return
            
        try:
            print("[DEBUG] 正在获取排行榜")
            sort_type = 'speed' if self.leaderboard_sort.get() == '按速度' else 'accuracy'
            response = self.puzzle_client.send_request("get_leaderboard", {
                "sort_by": sort_type
            })
            print(f"[DEBUG] 排行榜响应: {response}")
            
            if response and response.get("status") == "success":
                self.leaderboard_list.delete(0, tk.END)
                leaderboard = response.get("leaderboard", [])
                
                # 添加表头
                header = "排名  用户名          平均用时    已解题数" if sort_type == 'speed' else \
                        "排名  用户名          正确率      总尝试数"
                self.leaderboard_list.insert(tk.END, header)
                self.leaderboard_list.insert(tk.END, "-" * 50)
                
                for i, entry in enumerate(leaderboard, 1):
                    if sort_type == 'speed':
                        text = f"{i:2d}.   {entry['username']:<15} {entry.get('avg_time', 0):>6.1f}秒   {entry.get('puzzles_solved', 0):>4d}题"
                    else:
                        text = f"{i:2d}.   {entry['username']:<15} {entry.get('accuracy', 0):>6.1f}%    {entry.get('total_attempts', 0):>4d}次"
                    self.leaderboard_list.insert(tk.END, text)
            else:
                print(f"[ERROR] 获取排行榜失败: {response.get('message', '未知错误')}")
        except Exception as e:
            print(f"[ERROR] 更新排行榜时出错: {str(e)}")
            messagebox.showerror("错误", f"无法更新排行榜: {str(e)}")
    
    def update_activity(self):
        if not self.current_user:
            return
            
        try:
            print("[DEBUG] 正在获取最近活动")
            response = self.puzzle_client.send_request("get_recent_activity", {"limit": 10})
            print(f"[DEBUG] 最近活动响应: {response}")
            
            if response and response.get("status") == "success":
                self.activity_list.delete(0, tk.END)
                activities = response.get("activities", [])
                
                # 添加表头
                self.activity_list.insert(tk.END, "时间              用户名          谜题            结果   用时")
                self.activity_list.insert(tk.END, "-" * 70)
                
                for activity in activities:
                    result = "✓" if activity['result'] == "correct" else "✗"
                    timestamp = activity.get('timestamp', '')[:16]  # 只显示到分钟
                    text = f"{timestamp}  {activity['username']:<15} {activity['puzzle_title']:<15} {result}  {activity['time_taken']:>5.1f}秒"
                    self.activity_list.insert(tk.END, text)
            else:
                print(f"[ERROR] 获取最近活动失败: {response.get('message', '未知错误')}")
        except Exception as e:
            print(f"[ERROR] 更新最近活动时出错: {str(e)}")
            messagebox.showerror("错误", f"无法更新最近活动: {str(e)}")
    
    def update_ui_for_logged_in_user(self):
        print("[DEBUG] 更新UI为已登录状态")  # 调试信息
        self.auth_frame.grid_remove()
        
        # 显示统计信息框架
        self.stats_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        self.update_statistics()  # 立即更新统计信息
        
        # 显示排行榜框架
        self.leaderboard_frame.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        self.update_leaderboard()  # 立即更新排行榜
        
        # 显示最近活动框架
        self.activity_frame.grid(row=2, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        self.update_activity()  # 立即更新最近活动
        
        # 显示过滤器框架
        self.filter_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 加载谜题列表
        self.load_puzzles()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            response = self.auth_client.login(username, password)
            if response and response.get("status") == "success":
                self.current_user = username
                self.auth_token = response.get("data", {}).get("auth_token")
                # 同步令牌到谜题客户端
                self.puzzle_client.auth_token = self.auth_token
                print(f"[DEBUG] 登录成功，令牌已同步: {self.auth_token}")
                self.update_ui_for_logged_in_user()
            else:
                messagebox.showerror("Error", response.get("message", "Login failed"))
        except Exception as e:
            messagebox.showerror("Error", f"Could not login: {str(e)}")
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            response = self.auth_client.register(username, password)
            if response and response.get("status") == "success":
                messagebox.showinfo("Success", "Registration successful! You can now login.")
            else:
                messagebox.showerror("Error", response.get("message", "Registration failed"))
        except Exception as e:
            messagebox.showerror("Error", f"Could not register: {str(e)}")
    
    def update_statistics(self):
        if not self.current_user:
            return
            
        try:
            print("[DEBUG] 正在获取统计信息")
            response = self.puzzle_client.send_request("get_stats", {})
            print(f"[DEBUG] 统计信息响应: {response}")
            
            if response and response.get("status") == "success":
                stats = response.get("data", {})  # 从stats字段获取数据
                self.stats_labels['puzzles_solved'].config(
                    text=f"已解决谜题数: {stats.get('puzzles_solved', 0)}")
                self.stats_labels['avg_time'].config(
                    text=f"平均用时: {stats.get('avg_time', 0):.1f}秒")
                self.stats_labels['last_login'].config(
                    text=f"上次登录: {stats.get('last_login', '从未登录')}")
            else:
                print(f"[ERROR] 获取统计信息失败: {response.get('message', '未知错误')}")
        except Exception as e:
            print(f"[ERROR] 更新统计信息时出错: {str(e)}")
            messagebox.showerror("错误", f"无法更新统计信息: {str(e)}")
    
    def load_puzzles(self):
        if not self.current_user:
            return
            
        try:
            print("[DEBUG] 发送获取谜题请求，参数：" + 
                  str({'sort_by': self.sort_by.get(),
                      'order': self.order.get(),
                      'tag': self.tag.get() or None}))
                      
            response = self.puzzle_client.send_request("get_puzzles", {
                "sort_by": self.sort_by.get(),
                "order": self.order.get(),
                "tag": self.tag.get() or None
            })
            
            if response and response.get("status") == "success":
                puzzles = response.get("data", {}).get("puzzles", [])
                self.puzzle_list["values"] = [f"{p['title']} (by {p['author_name']})" for p in puzzles]
                if puzzles:
                    self.puzzle_list.current(0)
                self.puzzles = puzzles
            else:
                messagebox.showerror("Error", response.get("message", "Could not load puzzles"))
        except Exception as e:
            messagebox.showerror("Error", f"Could not load puzzles: {str(e)}")
    
    def load_selected_puzzle(self):
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        selection = self.puzzle_list.get()
        if not selection:
            return
            
        try:
            # 从存储的谜题列表中找到选中的谜题
            selected_index = self.puzzle_list.current()
            if selected_index < 0 or not hasattr(self, 'puzzles'):
                return
                
            selected_puzzle = self.puzzles[selected_index]
            puzzle_id = selected_puzzle['id']
            
            print(f"[DEBUG] 加载谜题 - ID: {puzzle_id}")
            response = self.puzzle_client.send_request("get_puzzle", {"puzzle_id": puzzle_id})
            
            if response and response.get("status") == "success":
                self.current_puzzle = response.get("data", {}).get("puzzle")
                if self.current_puzzle:
                    self.display_puzzle()
                    self.start_time = time.time()
                else:
                    messagebox.showerror("Error", "Could not load puzzle data")
            else:
                messagebox.showerror("Error", response.get("message", "Could not load puzzle"))
        except Exception as e:
            print(f"[ERROR] 加载谜题失败: {str(e)}")
            messagebox.showerror("Error", f"Could not load puzzle: {str(e)}")
    
    def display_puzzle(self):
        # Clear existing grid
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.grid_entries = []
        
        # Create grid
        grid = self.current_puzzle['grid']
        for i, row in enumerate(grid):
            grid_row = []
            for j, cell in enumerate(row):
                if cell == '#':  # Black square
                    entry = ttk.Entry(self.grid_frame, width=3, justify='center')
                    entry.insert(0, '#')
                    entry.configure(state='disabled')
                    entry.grid(row=i, column=j, padx=1, pady=1)
                    grid_row.append(entry)
                else:  # White square
                    entry = ttk.Entry(self.grid_frame, width=3, justify='center')
                    entry.grid(row=i, column=j, padx=1, pady=1)
                    # 绑定按键事件
                    entry.bind('<KeyRelease>', lambda e, row=i, col=j: self.handle_key_event(e, row, col))
                    grid_row.append(entry)
            self.grid_entries.append(grid_row)
        
        # Display clues
        for widget in self.clues_frame.winfo_children():
            widget.destroy()
        
        # 创建两个Frame来分别显示横向和纵向提示
        across_frame = ttk.LabelFrame(self.clues_frame, text="横向提示")
        across_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        
        down_frame = ttk.LabelFrame(self.clues_frame, text="纵向提示")
        down_frame.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # 获取提示信息
        clues = self.current_puzzle['clues']
        
        # 显示横向提示
        for i, clue in enumerate(clues['across']):
            # 移除可能的重复编号
            clue_text = clue.split('.')[-1].strip() if '.' in clue else clue
            ttk.Label(across_frame, 
                     text=f"{i+1}. {clue_text}", 
                     wraplength=200).grid(row=i, column=0, pady=2, sticky=tk.W)
        
        # 显示纵向提示
        for i, clue in enumerate(clues['down']):
            # 移除可能的重复编号
            clue_text = clue.split('.')[-1].strip() if '.' in clue else clue
            ttk.Label(down_frame, 
                     text=f"{i+1}. {clue_text}", 
                     wraplength=200).grid(row=i, column=0, pady=2, sticky=tk.W)
        
        # 调整框架大小
        self.clues_frame.grid_columnconfigure(0, weight=1)
        self.clues_frame.grid_columnconfigure(1, weight=1)
    
    def handle_key_event(self, event, current_row, current_col):
        """处理按键事件，在输入字符后自动移动到下一个可用的格子"""
        if len(event.widget.get()) == 1:  # 如果输入了一个字符
            # 获取网格尺寸
            rows = len(self.grid_entries)
            cols = len(self.grid_entries[0])
            
            # 尝试移动到下一个可用的格子
            next_row, next_col = current_row, current_col + 1  # 默认向右移动
            
            # 如果到达行尾，移动到下一行开头
            if next_col >= cols:
                next_row = current_row + 1
                next_col = 0
            
            # 如果到达最后一行，回到第一行
            if next_row >= rows:
                next_row = 0
            
            # 寻找下一个可用的格子
            while (next_row < rows and 
                   self.grid_entries[next_row][next_col].cget('state') == 'disabled'):
                next_col += 1
                if next_col >= cols:
                    next_row += 1
                    next_col = 0
                if next_row >= rows:
                    next_row = 0
            
            # 如果找到了可用的格子，将焦点移动到那里
            if next_row < rows and next_col < cols:
                self.grid_entries[next_row][next_col].focus()
    
    def submit_solution(self):
        if not self.current_puzzle or not self.grid_entries:
            return
            
        try:
            # 收集答案
            grid = []
            original_grid = self.current_puzzle['grid']
            
            for i, row in enumerate(self.grid_entries):
                grid_row = []
                for j, entry in enumerate(row):
                    if original_grid[i][j] == '#':
                        grid_row.append('#')
                    else:
                        value = entry.get().strip().upper()
                        if not value:  # 如果格子是空的
                            messagebox.showwarning("Warning", "Please fill in all squares before submitting")
                            return
                        grid_row.append(value)
                grid.append(grid_row)
            
            # 验证网格大小
            if len(grid) != len(original_grid) or any(len(row) != len(original_grid[0]) for row in grid):
                messagebox.showerror("Error", "Invalid grid format")
                return
            
            # 计算用时
            time_taken = time.time() - self.start_time if self.start_time else 0
            
            print(f"[DEBUG] 提交答案 - 令牌: {self.auth_token}")
            print(f"[DEBUG] 提交的网格: {json.dumps(grid)}")  # 添加调试信息
            
            response = self.puzzle_client.send_request("submit_solution", {
                "puzzle_id": self.current_puzzle['id'],
                "grid": grid,
                "time_taken": time_taken
            })
            
            if response and response.get("status") == "success":
                result = response.get("data", {})
                if result.get("is_correct"):
                    messagebox.showinfo("Success", result.get("message", "Correct!"))
                    self.update_statistics()
                    self.update_leaderboard()
                    self.update_activity()
                else:
                    messagebox.showwarning("Wrong", result.get("message", "Try again!"))
            else:
                messagebox.showerror("Error", response.get("message", "Could not submit solution"))
        except Exception as e:
            print(f"[ERROR] 提交答案失败: {str(e)}")  # 添加调试信息
            messagebox.showerror("Error", f"Could not submit solution: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleClient(root)
    root.mainloop() 