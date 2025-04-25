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
        
        # Initialize game client
        self.client = GameClient(("localhost", 5000))
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
        self.leaderboard_frame = ttk.LabelFrame(self.right_panel, text="Leaderboard")
        self.leaderboard_frame.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        self.leaderboard_sort = ttk.Combobox(self.leaderboard_frame,
                                           values=['speed', 'accuracy'],
                                           state='readonly')
        self.leaderboard_sort.pack(pady=5)
        self.leaderboard_sort.set('speed')
        
        self.leaderboard_list = tk.Listbox(self.leaderboard_frame, height=10)
        self.leaderboard_list.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(self.leaderboard_frame, text="Refresh",
                  command=self.update_leaderboard).pack(pady=5)
        
        # Recent activity frame
        self.activity_frame = ttk.LabelFrame(self.right_panel, text="Recent Activity")
        self.activity_frame.grid(row=2, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        self.activity_list = tk.Listbox(self.activity_frame, height=10)
        self.activity_list.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(self.activity_frame, text="Refresh",
                  command=self.update_activity).pack(pady=5)
        
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
            response = self.client.send_request("get_leaderboard", {
                "sort_by": self.leaderboard_sort.get()
            })
            if response and response.get("status") == "success":
                self.leaderboard_list.delete(0, tk.END)
                leaderboard = response.get("data", {}).get("leaderboard", [])
                
                if self.leaderboard_sort.get() == "speed":
                    for entry in leaderboard:
                        self.leaderboard_list.insert(tk.END,
                            f"{entry['username']}: {entry['avg_time']:.2f}s "
                            f"({entry['solved_count']} solved)")
                else:
                    for entry in leaderboard:
                        self.leaderboard_list.insert(tk.END,
                            f"{entry['username']}: {entry['accuracy']:.1f}% "
                            f"({entry['total_attempts']} attempts)")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update leaderboard: {str(e)}")
    
    def update_activity(self):
        if not self.current_user:
            return
            
        try:
            response = self.client.send_request("get_recent_activity", {"limit": 10})
            if response and response.get("status") == "success":
                self.activity_list.delete(0, tk.END)
                activities = response.get("data", {}).get("activities", [])
                
                for activity in activities:
                    result = "✓" if activity['result'] == "correct" else "✗"
                    self.activity_list.insert(tk.END,
                        f"{activity['username']} {result} {activity['puzzle_title']} "
                        f"({activity['time_taken']:.1f}s)")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update activity feed: {str(e)}")
    
    def update_ui_for_logged_in_user(self):
        self.auth_frame.grid_remove()
        self.stats_frame.grid()
        self.filter_frame.grid()
        self.update_leaderboard()
        self.update_activity()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            response = self.client.login(username, password)
            if response and response.get("status") == "success":
                self.current_user = username
                self.update_ui_for_logged_in_user()
                self.load_puzzles()
                self.update_statistics()
            else:
                messagebox.showerror("Error", "Invalid credentials")
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect to server: {str(e)}")
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            response = self.client.register(username, password)
            if response and response.get("status") == "success":
                messagebox.showinfo("Success", "Registration successful")
            else:
                messagebox.showerror("Error", response.get("message", "Registration failed"))
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect to server: {str(e)}")
    
    def update_statistics(self):
        if not self.current_user:
            return
            
        try:
            response = self.client.send_request("get_stats", {"user_id": self.current_user})
            if response and response.get("status") == "success":
                stats = response.get("data", {})
                self.stats_labels['puzzles_solved'].config(
                    text=f"Puzzles Solved: {stats.get('puzzles_solved', 0)}")
                self.stats_labels['avg_time'].config(
                    text=f"Average Time: {stats.get('avg_time', 0):.2f}s")
                self.stats_labels['last_login'].config(
                    text=f"Last Login: {stats.get('last_login', 'Never')}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch statistics: {str(e)}")
    
    def load_puzzles(self):
        try:
            params = {
                'sort_by': self.sort_by.get(),
                'order': self.order.get(),
                'tag': self.tag.get() if self.tag.get() else None
            }
            response = self.client.send_request("get_puzzles", params)
            if response and response.get("status") == "success":
                puzzles = response.get("data", {}).get("puzzles", [])
                self.puzzle_list['values'] = [
                    (p['id'], p['title'], 
                     f"Author: {p['author']}, "
                     f"Solved: {p['solved_count']} times, "
                     f"Tags: {', '.join(p['tags'])}")
                    for p in puzzles
                ]
                if puzzles:
                    self.puzzle_list.current(0)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load puzzles: {str(e)}")
    
    def load_selected_puzzle(self):
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        selection = self.puzzle_list.get()
        if not selection:
            return
            
        puzzle_id = selection.split(',')[0].strip('(')
        try:
            response = self.client.send_request("get_puzzle", {"puzzle_id": puzzle_id})
            if response and response.get("status") == "success":
                self.current_puzzle = response.get("data", {}).get("puzzle")
                self.display_puzzle()
                self.start_time = time.time()
            else:
                messagebox.showerror("Error", "Could not load puzzle")
        except Exception as e:
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
                    ttk.Label(self.grid_frame, text="", width=3, 
                            background="black").grid(row=i, column=j, padx=1, pady=1)
                else:  # White square
                    entry = ttk.Entry(self.grid_frame, width=3, justify='center')
                    entry.grid(row=i, column=j, padx=1, pady=1)
                    grid_row.append(entry)
            self.grid_entries.append(grid_row)
        
        # Display clues
        for widget in self.clues_frame.winfo_children():
            widget.destroy()
        
        clues = self.current_puzzle['clues']
        ttk.Label(self.clues_frame, text="Across:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(self.clues_frame, text="Down:").grid(row=0, column=1, sticky=tk.W)
        
        for i, clue in enumerate(clues['across'], 1):
            ttk.Label(self.clues_frame, text=f"{i}. {clue}").grid(row=i, column=0, sticky=tk.W)
        
        for i, clue in enumerate(clues['down'], 1):
            ttk.Label(self.clues_frame, text=f"{i}. {clue}").grid(row=i, column=1, sticky=tk.W)
    
    def submit_solution(self):
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        if not self.current_puzzle:
            return
            
        # Get user's answer
        user_answer = []
        for row in self.grid_entries:
            answer_row = []
            for entry in row:
                answer_row.append(entry.get().upper() if entry.get() else ' ')
            user_answer.append(answer_row)
        
        # Calculate time taken
        time_taken = time.time() - self.start_time if self.start_time else 0
        
        try:
            response = self.client.send_request("submit_solution", {
                'puzzle_id': self.current_puzzle['id'],
                'user_id': self.current_user,
                'grid': user_answer,
                'time_taken': time_taken
            })
            
            if response and response.get("status") == "success":
                result = response.get("data", {})
                if result.get("result") == "correct":
                    messagebox.showinfo("Success", "Correct! Well done!")
                    self.update_statistics()
                    self.update_leaderboard()
                    self.update_activity()
                else:
                    # Highlight incorrect cells
                    for row, col in result.get("incorrect_cells", []):
                        self.grid_entries[row][col].config(background='red')
                    messagebox.showinfo("Result", "Incorrect. Try again!")
            else:
                messagebox.showerror("Error", "Could not submit solution")
        except Exception as e:
            messagebox.showerror("Error", f"Could not submit solution: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleClient(root)
    root.mainloop() 