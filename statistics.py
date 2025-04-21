import tkinter as tk
from tkinter import ttk
import requests
from datetime import datetime

class StatisticsView(tk.Frame):
    def __init__(self, parent, token, user_id):
        super().__init__(parent)
        self.token = token
        self.user_id = user_id
        self.setup_ui()
        self.load_statistics()

    def setup_ui(self):
        # Personal Stats Section
        personal_frame = ttk.LabelFrame(self, text="Your Statistics")
        personal_frame.pack(fill="x", padx=10, pady=5)
        
        self.puzzles_solved_label = ttk.Label(personal_frame, text="Puzzles Solved: ")
        self.puzzles_solved_label.pack(anchor="w", padx=5)
        
        self.avg_time_label = ttk.Label(personal_frame, text="Average Solve Time: ")
        self.avg_time_label.pack(anchor="w", padx=5)
        
        self.last_solved_label = ttk.Label(personal_frame, text="Last Solved: ")
        self.last_solved_label.pack(anchor="w", padx=5)
        
        # Puzzle Stats Section
        puzzle_frame = ttk.LabelFrame(self, text="Puzzle Statistics")
        puzzle_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add filter options
        filter_frame = ttk.Frame(puzzle_frame)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Sort by:").pack(side="left", padx=5)
        self.sort_var = tk.StringVar(value="solved_count")
        sort_options = ttk.OptionMenu(
            filter_frame, 
            self.sort_var, 
            "solved_count",
            "solved_count", "avg_time", "date",
            command=self.refresh_stats
        )
        sort_options.pack(side="left", padx=5)
        
        # Create treeview for puzzle stats
        columns = ("Title", "Times Solved", "Avg Time", "Last Solved", "Tags")
        self.puzzle_tree = ttk.Treeview(puzzle_frame, columns=columns, show="headings")
        
        for col in columns:
            self.puzzle_tree.heading(col, text=col, command=lambda c=col: self.sort_by(c))
            self.puzzle_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(puzzle_frame, orient="vertical", command=self.puzzle_tree.yview)
        self.puzzle_tree.configure(yscrollcommand=scrollbar.set)
        
        self.puzzle_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_statistics(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Get user stats
            response = requests.get(
                f"http://localhost:5000/stats/user/{self.user_id}",
                headers=headers
            )
            if response.ok:
                stats = response.json()
                self.puzzles_solved_label.config(
                    text=f"Puzzles Solved: {stats['puzzles_solved']}"
                )
                avg_time = stats['average_solve_time'] or 0
                self.avg_time_label.config(
                    text=f"Average Solve Time: {avg_time:.1f} seconds"
                )
                if stats.get('last_solved'):
                    last_solved = datetime.fromisoformat(stats['last_solved'])
                    self.last_solved_label.config(
                        text=f"Last Solved: {last_solved.strftime('%Y-%m-%d %H:%M')}"
                    )
            
            # Get puzzle stats with sorting
            sort_by = self.sort_var.get()
            response = requests.get(
                f"http://localhost:5000/stats/puzzles?sort_by={sort_by}",
                headers=headers
            )
            if response.ok:
                puzzles = response.json()
                self.update_puzzle_tree(puzzles)
                
        except requests.RequestException as e:
            ttk.Label(self, text=f"Error loading statistics: {str(e)}").pack()

    def update_puzzle_tree(self, puzzles):
        # Clear existing items
        for item in self.puzzle_tree.get_children():
            self.puzzle_tree.delete(item)
        
        # Add new items
        for puzzle in puzzles:
            last_solved = "Never"
            if puzzle.get('last_solved'):
                last_solved = datetime.fromisoformat(puzzle['last_solved']).strftime('%Y-%m-%d')
                
            tags = puzzle.get('tags', [])
            if isinstance(tags, list):
                tags = ", ".join(tags)
                
            self.puzzle_tree.insert("", "end", values=(
                puzzle['title'],
                puzzle['times_solved'],
                f"{puzzle['avg_time']:.1f}s" if puzzle.get('avg_time') else "N/A",
                last_solved,
                tags
            ))

    def refresh_stats(self, *args):
        self.load_statistics()

    def sort_by(self, column):
        self.sort_var.set(column.lower().replace(" ", "_"))
        self.refresh_stats()