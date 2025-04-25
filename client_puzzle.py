import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
from client_auth import GameClient
from puzzle_creator_ui import PuzzleCreatorWindow  # Import puzzle creator

class PuzzleClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Crossword Puzzle")
        self.root.geometry("1200x800")
        
        # Initialize two different clients
        self.auth_client = GameClient(("localhost", 5000))  # Authentication server
        self.puzzle_client = GameClient(("localhost", 5001))  # Puzzle server
        self.current_user = None
        self.start_time = None  # Will be set when puzzle is loaded
        
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
        
        # Add create puzzle button
        self.create_puzzle_button = ttk.Button(self.left_panel, 
                                             text="Create New Puzzle", 
                                             command=self.open_puzzle_creator)
        self.create_puzzle_button.grid(row=1, column=0, columnspan=2, pady=5)
        self.create_puzzle_button.grid_remove()  # Initially hide button
        
        # Statistics frame
        self.stats_frame = ttk.LabelFrame(self.right_panel, text="Your Statistics")
        self.stats_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        self.stats_labels = {}
        for stat in ['puzzles_solved', 'avg_time', 'last_login']:
            self.stats_labels[stat] = ttk.Label(self.stats_frame, text="")
            self.stats_labels[stat].pack(pady=5)
        
        # Leaderboard frame
        self.leaderboard_frame = ttk.LabelFrame(self.right_panel, text="Leaderboard")
        self.leaderboard_frame.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Leaderboard sort options
        sort_frame = ttk.Frame(self.leaderboard_frame)
        sort_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT, padx=5)
        self.leaderboard_sort = ttk.Combobox(sort_frame,
                                           values=['By Speed', 'By Accuracy'],
                                           state='readonly',
                                           width=10)
        self.leaderboard_sort.pack(side=tk.LEFT, padx=5)
        self.leaderboard_sort.set('By Speed')
        self.leaderboard_sort.bind('<<ComboboxSelected>>', lambda e: self.update_leaderboard())
        
        # Create leaderboard listbox with scrollbar
        list_frame = ttk.Frame(self.leaderboard_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.leaderboard_list = tk.Listbox(list_frame, height=12, width=50,
                                         yscrollcommand=scrollbar.set)
        self.leaderboard_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.leaderboard_list.yview)
        
        # Recent activity frame
        self.activity_frame = ttk.LabelFrame(self.right_panel, text="Recent Activity")
        self.activity_frame.grid(row=2, column=0, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create activity listbox with scrollbar
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
            print("[DEBUG] Getting leaderboard")
            sort_type = 'speed' if self.leaderboard_sort.get() == 'By Speed' else 'accuracy'
            response = self.puzzle_client.send_request("get_leaderboard", {
                "sort_by": sort_type
            })
            print(f"[DEBUG] Leaderboard response: {response}")
            
            if response and response.get("status") == "success":
                self.leaderboard_list.delete(0, tk.END)
                leaderboard = response.get("leaderboard", [])
                
                # Add header
                header = "Rank  Username        Avg Time   Puzzles" if sort_type == 'speed' else \
                        "Rank  Username        Accuracy   Attempts"
                self.leaderboard_list.insert(tk.END, header)
                self.leaderboard_list.insert(tk.END, "-" * 50)
                
                for i, entry in enumerate(leaderboard, 1):
                    if sort_type == 'speed':
                        text = f"{i:2d}.   {entry['username']:<15} {entry.get('avg_time', 0):>6.1f}s   {entry.get('puzzles_solved', 0):>4d}"
                    else:
                        text = f"{i:2d}.   {entry['username']:<15} {entry.get('accuracy', 0):>6.1f}%    {entry.get('total_attempts', 0):>4d}"
                    self.leaderboard_list.insert(tk.END, text)
            else:
                print(f"[ERROR] Failed to get leaderboard: {response.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"[ERROR] Error updating leaderboard: {str(e)}")
            messagebox.showerror("Error", f"Cannot update leaderboard: {str(e)}")
    
    def update_activity(self):
        if not self.current_user:
            return
            
        try:
            print("[DEBUG] Getting recent activity")
            response = self.puzzle_client.send_request("get_recent_activity", {"limit": 10})
            print(f"[DEBUG] Recent activity response: {response}")
            
            if response and response.get("status") == "success":
                self.activity_list.delete(0, tk.END)
                activities = response.get("activities", [])
                
                # Add header
                self.activity_list.insert(tk.END, "Time              Username        Puzzle          Result  Time")
                self.activity_list.insert(tk.END, "-" * 70)
                
                for activity in activities:
                    result = "✓" if activity['result'] == "correct" else "✗"
                    timestamp = activity.get('timestamp', '')[:16]  # Show only up to minutes
                    text = f"{timestamp}  {activity['username']:<15} {activity['puzzle_title']:<15} {result}  {activity['time_taken']:>5.1f}s"
                    self.activity_list.insert(tk.END, text)
            else:
                print(f"[ERROR] Failed to get recent activity: {response.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"[ERROR] Error updating recent activity: {str(e)}")
            messagebox.showerror("Error", f"Cannot update recent activity: {str(e)}")
    
    def update_ui_for_logged_in_user(self):
        print("[DEBUG] Updating UI for logged in state")
        self.auth_frame.grid_remove()
        
        # Show create puzzle button
        self.create_puzzle_button.grid()
        
        # Show statistics frame
        self.stats_frame.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        self.update_statistics()  # Update statistics immediately
        
        # Show leaderboard frame
        self.leaderboard_frame.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        self.update_leaderboard()  # Update leaderboard immediately
        
        # Show recent activity frame
        self.activity_frame.grid(row=2, column=0, padx=10, pady=10, sticky=(tk.N, tk.S, tk.W, tk.E))
        self.update_activity()  # Update recent activity immediately
        
        # Show filter frame
        self.filter_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Load puzzle list
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
            print("[DEBUG] Getting statistics")
            response = self.puzzle_client.send_request("get_stats", {})
            print(f"[DEBUG] Statistics response: {response}")
            
            if response and response.get("status") == "success":
                stats = response.get("data", {})  # Get data from stats field
                print(f"[DEBUG] Stats data: {stats}")  # Add debug log
                
                # Handle None values with defaults
                puzzles_solved = stats.get('puzzles_solved', 0)
                avg_time = stats.get('avg_time', 0)
                last_login = stats.get('last_login', 'Never')
                
                # Update labels with safe values
                self.stats_labels['puzzles_solved'].config(
                    text=f"Puzzles Solved: {puzzles_solved}")
                self.stats_labels['avg_time'].config(
                    text=f"Average Time: {avg_time:.1f}s" if avg_time is not None else "Average Time: 0.0s")
                self.stats_labels['last_login'].config(
                    text=f"Last Login: {last_login if last_login else 'Never'}")
            else:
                print(f"[ERROR] Failed to get statistics: {response.get('message', 'Unknown error')}")
                # Set default values if failed to get statistics
                self.stats_labels['puzzles_solved'].config(text="Puzzles Solved: 0")
                self.stats_labels['avg_time'].config(text="Average Time: 0.0s")
                self.stats_labels['last_login'].config(text="Last Login: Never")
        except Exception as e:
            print(f"[ERROR] Error updating statistics: {str(e)}")
            # Set default values on error
            self.stats_labels['puzzles_solved'].config(text="Puzzles Solved: 0")
            self.stats_labels['avg_time'].config(text="Average Time: 0.0s")
            self.stats_labels['last_login'].config(text="Last Login: Never")
    
    def load_puzzles(self):
        if not self.current_user:
            return
            
        try:
            print("[DEBUG] Sending get puzzle request, parameters: " + 
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
            # Get selected puzzle from stored puzzle list
            selected_index = self.puzzle_list.current()
            if selected_index < 0 or not hasattr(self, 'puzzles'):
                return
                
            selected_puzzle = self.puzzles[selected_index]
            puzzle_id = selected_puzzle['id']
            
            print(f"[DEBUG] Loading puzzle - ID: {puzzle_id}")
            response = self.puzzle_client.send_request("get_puzzle", {"puzzle_id": puzzle_id})
            
            if response and response.get("status") == "success":
                self.current_puzzle = response.get("data", {}).get("puzzle")
                if self.current_puzzle:
                    # Reset start time before displaying puzzle
                    self.start_time = None
                    self.display_puzzle()
                else:
                    messagebox.showerror("Error", "Could not load puzzle data")
            else:
                messagebox.showerror("Error", response.get("message", "Could not load puzzle"))
        except Exception as e:
            print(f"[ERROR] Failed to load puzzle: {str(e)}")
            messagebox.showerror("Error", f"Could not load puzzle: {str(e)}")
    
    def display_puzzle(self):
        # Clear existing grid
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.grid_entries = []
        
        # Start timing when puzzle is displayed
        self.start_time = time.time()
        print(f"[DEBUG] Starting puzzle timer at: {self.start_time}")
        
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
                    # Start timing when user first types in a cell
                    entry.bind('<Key>', lambda e, entry=entry: self.handle_first_input(e, entry))
                    # Bind key event for navigation
                    entry.bind('<KeyRelease>', lambda e, row=i, col=j: self.handle_key_event(e, row, col))
                    grid_row.append(entry)
            self.grid_entries.append(grid_row)
        
        # Display clues
        for widget in self.clues_frame.winfo_children():
            widget.destroy()
        
        # Create two frames for across and down clues
        across_frame = ttk.LabelFrame(self.clues_frame, text="Across Clues")
        across_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        
        down_frame = ttk.LabelFrame(self.clues_frame, text="Down Clues")
        down_frame.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # Get clue information
        clues = self.current_puzzle['clues']
        
        # Display across clues
        for i, clue in enumerate(clues['across']):
            # Remove possible duplicate numbers
            clue_text = clue.split('.')[-1].strip() if '.' in clue else clue
            ttk.Label(across_frame, 
                     text=f"{i+1}. {clue_text}", 
                     wraplength=200).grid(row=i, column=0, pady=2, sticky=tk.W)
        
        # Display down clues
        for i, clue in enumerate(clues['down']):
            # Remove possible duplicate numbers
            clue_text = clue.split('.')[-1].strip() if '.' in clue else clue
            ttk.Label(down_frame, 
                     text=f"{i+1}. {clue_text}", 
                     wraplength=200).grid(row=i, column=0, pady=2, sticky=tk.W)
        
        # Adjust frame size
        self.clues_frame.grid_columnconfigure(0, weight=1)
        self.clues_frame.grid_columnconfigure(1, weight=1)
    
    def handle_first_input(self, event, entry):
        """Start timing when user first types in any cell"""
        if self.start_time is None:
            self.start_time = time.time()
            print(f"[DEBUG] Starting puzzle timer on first input at: {self.start_time}")
        # Remove the binding after first input
        entry.unbind('<Key>')
    
    def handle_key_event(self, event, current_row, current_col):
        """Handle key events, automatically move to next available cell after input"""
        if len(event.widget.get()) == 1:  # If a character is input
            # Get grid dimensions
            rows = len(self.grid_entries)
            cols = len(self.grid_entries[0])
            
            # Try to move to next available cell
            next_row, next_col = current_row, current_col + 1  # Default move right
            
            # If reach end of row, move to start of next row
            if next_col >= cols:
                next_row = current_row + 1
                next_col = 0
            
            # If reach last row, go back to first row
            if next_row >= rows:
                next_row = 0
            
            # Find next available cell
            while (next_row < rows and 
                   self.grid_entries[next_row][next_col].cget('state') == 'disabled'):
                next_col += 1
                if next_col >= cols:
                    next_row += 1
                    next_col = 0
                if next_row >= rows:
                    next_row = 0
            
            # If found available cell, move focus there
            if next_row < rows and next_col < cols:
                self.grid_entries[next_row][next_col].focus()
    
    def submit_solution(self):
        if not self.current_puzzle or not self.grid_entries:
            return
            
        try:
            # Collect answers
            grid = []
            original_grid = self.current_puzzle['grid']
            
            for i, row in enumerate(self.grid_entries):
                grid_row = []
                for j, entry in enumerate(row):
                    if original_grid[i][j] == '#':
                        grid_row.append('#')
                    else:
                        value = entry.get().strip().upper()
                        if not value:  # If cell is empty
                            messagebox.showwarning("Warning", "Please fill in all squares before submitting")
                            return
                        grid_row.append(value)
                grid.append(grid_row)
            
            # Verify grid size
            if len(grid) != len(original_grid) or any(len(row) != len(original_grid[0]) for row in grid):
                messagebox.showerror("Error", "Invalid grid format")
                return
            
            # Calculate time taken
            if self.start_time is None:
                print("[ERROR] Start time not set")
                time_taken = 0
            else:
                current_time = time.time()
                time_taken = round(current_time - self.start_time, 2)
                print(f"[DEBUG] Time taken: {time_taken} seconds (start: {self.start_time}, end: {current_time})")
            
            print(f"[DEBUG] Submitting answer - Token: {self.auth_token}")
            print(f"[DEBUG] Submitted grid: {json.dumps(grid)}")
            print(f"[DEBUG] Time taken: {time_taken}")
            
            response = self.puzzle_client.send_request("submit_solution", {
                "puzzle_id": self.current_puzzle['id'],
                "grid": grid,
                "time_taken": time_taken
            })
            
            if response and response.get("status") == "success":
                result = response.get("data", {})
                if result.get("is_correct"):
                    messagebox.showinfo("Success", f"{result.get('message', 'Correct!')} Time: {time_taken}s")
                    self.start_time = None  # Reset start time after successful submission
                    self.update_statistics()
                    self.update_leaderboard()
                    self.update_activity()
                else:
                    messagebox.showwarning("Wrong", result.get("message", "Try again!"))
            else:
                messagebox.showerror("Error", response.get("message", "Could not submit solution"))
        except Exception as e:
            print(f"[ERROR] Failed to submit answer: {str(e)}")
            messagebox.showerror("Error", f"Could not submit answer: {str(e)}")

    def open_puzzle_creator(self):
        """Open puzzle creator window"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        try:
            creator_window = PuzzleCreatorWindow(self.root)
            creator_window.protocol("WM_DELETE_WINDOW", 
                                 lambda: self.handle_creator_close(creator_window))
            
            # Add puzzle submission callback
            def submit_puzzle_callback(puzzle_data):
                try:
                    print("[DEBUG] Submitting new puzzle:", puzzle_data)
                    response = self.puzzle_client.send_request("create_puzzle", puzzle_data)
                    
                    if response and response.get("status") == "success":
                        messagebox.showinfo("Success", "Puzzle created successfully!")
                        creator_window.destroy()
                        self.load_puzzles()  # Refresh puzzle list
                    else:
                        messagebox.showerror("Error", 
                                           response.get("message", "Failed to create puzzle"))
                except Exception as e:
                    print(f"[ERROR] Failed to create puzzle: {str(e)}")
                    messagebox.showerror("Error", f"Failed to create puzzle: {str(e)}")
            
            # Set callback function
            creator_window.submit_callback = submit_puzzle_callback
            
        except Exception as e:
            print(f"[ERROR] Failed to open puzzle creator: {str(e)}")
            messagebox.showerror("Error", f"Cannot open puzzle creator: {str(e)}")

    def handle_creator_close(self, creator_window):
        """Handle puzzle creator window close event"""
        try:
            creator_window.destroy()
        except:
            pass
        self.load_puzzles()  # Refresh puzzle list

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleClient(root)
    root.mainloop() 