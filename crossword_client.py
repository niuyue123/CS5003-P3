import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import time
from datetime import datetime

class CrosswordClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Crossword Puzzle")
        self.root.geometry("1000x800")
        
        # API endpoint
        self.base_url = "http://localhost:5000/api"
        self.current_user = None
        self.start_time = None
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Login/Register frame
        self.auth_frame = ttk.Frame(self.main_frame)
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
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="Statistics")
        self.stats_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=10)
        
        self.stats_labels = {}
        for stat in ['puzzles_solved', 'avg_time', 'last_login']:
            self.stats_labels[stat] = ttk.Label(self.stats_frame, text="")
            self.stats_labels[stat].pack(pady=5)
        
        # Puzzle filter frame
        self.filter_frame = ttk.Frame(self.main_frame)
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
        self.puzzle_list = ttk.Combobox(self.main_frame, state="readonly", width=50)
        self.puzzle_list.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        # Load puzzle button
        ttk.Button(self.main_frame, text="Load Puzzle", 
                  command=self.load_selected_puzzle).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Crossword grid
        self.grid_frame = ttk.Frame(self.main_frame)
        self.grid_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        
        # Clues frame
        self.clues_frame = ttk.Frame(self.main_frame)
        self.clues_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        # Submit button
        ttk.Button(self.main_frame, text="Submit Answer", 
                  command=self.submit_solution).grid(row=6, column=0, columnspan=2, pady=10)
        
        self.current_puzzle = None
        self.grid_entries = []
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            response = requests.post(f"{self.base_url}/login",
                                  json={'username': username, 'password': password})
            if response.status_code == 200:
                self.current_user = response.json()['user_id']
                self.update_ui_for_logged_in_user()
                self.load_puzzles()
                self.update_statistics()
            else:
                messagebox.showerror("Error", "Invalid credentials")
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            response = requests.post(f"{self.base_url}/register",
                                  json={'username': username, 'password': password})
            if response.status_code == 201:
                messagebox.showinfo("Success", "Registration successful")
            else:
                messagebox.showerror("Error", response.json()['error'])
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")
    
    def update_ui_for_logged_in_user(self):
        self.auth_frame.grid_remove()
        self.stats_frame.grid()
        self.filter_frame.grid()
    
    def update_statistics(self):
        if not self.current_user:
            return
            
        try:
            response = requests.get(f"{self.base_url}/users/{self.current_user}/stats")
            if response.status_code == 200:
                stats = response.json()
                self.stats_labels['puzzles_solved'].config(
                    text=f"Puzzles Solved: {stats['puzzles_solved']}")
                self.stats_labels['avg_time'].config(
                    text=f"Average Time: {stats['avg_time']:.2f}s")
                self.stats_labels['last_login'].config(
                    text=f"Last Login: {stats['last_login']}")
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not fetch statistics")
    
    def load_puzzles(self):
        try:
            params = {
                'sort_by': self.sort_by.get(),
                'order': self.order.get(),
                'tag': self.tag.get() if self.tag.get() else None
            }
            response = requests.get(f"{self.base_url}/puzzles", params=params)
            if response.status_code == 200:
                puzzles = response.json()
                self.puzzle_list['values'] = [
                    (p['id'], p['title'], 
                     f"Author: {p['author']}, "
                     f"Solved: {p['solved_count']} times, "
                     f"Tags: {', '.join(p['tags'])}")
                    for p in puzzles
                ]
                if puzzles:
                    self.puzzle_list.current(0)
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")
    
    def load_selected_puzzle(self):
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        selection = self.puzzle_list.get()
        if not selection:
            return
            
        puzzle_id = selection.split(',')[0].strip('(')
        try:
            response = requests.get(f"{self.base_url}/puzzles/{puzzle_id}")
            if response.status_code == 200:
                self.current_puzzle = response.json()
                self.display_puzzle()
                self.start_time = time.time()
            else:
                messagebox.showerror("Error", "Could not load puzzle")
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")
    
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
            response = requests.post(
                f"{self.base_url}/puzzles/{self.current_puzzle['id']}/submit",
                json={
                    'user_id': self.current_user,
                    'grid': user_answer,
                    'time_taken': time_taken
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['result'] == 'correct':
                    messagebox.showinfo("Success", "Correct! Well done!")
                    self.update_statistics()
                else:
                    # Highlight incorrect cells
                    for row, col in result['incorrect_cells']:
                        self.grid_entries[row][col].config(background='red')
                    messagebox.showinfo("Result", "Incorrect. Try again!")
            else:
                messagebox.showerror("Error", "Could not submit solution")
        except requests.exceptions.RequestException:
            messagebox.showerror("Error", "Could not connect to server")

if __name__ == "__main__":
    root = tk.Tk()
    app = CrosswordClient(root)
    root.mainloop() 