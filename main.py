import tkinter as tk
from tkinter import ttk
from views.login import LoginView
from views.puzzle_list import PuzzleListView
from views.puzzle_solver import PuzzleSolverView
from views.puzzle_creator import PuzzleCreatorView
from views.statistics import StatisticsView
from views.social import SocialView

class CrosswordApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Crossword Puzzle Platform")
        self.root.geometry("1024x768")
        
        self.token = None
        self.user_id = None
        self.current_view = None
        
        # Add menu bar
        self.create_menu()
        
        self.show_login()
    
    def create_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        self.game_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Menu", menu=self.game_menu)
        
        self.game_menu.add_command(label="Puzzle List", command=self.show_puzzle_list, state="disabled")
        self.game_menu.add_command(label="Statistics", command=self.show_statistics, state="disabled")
        self.game_menu.add_separator()
        self.game_menu.add_command(label="Logout", command=self.logout, state="disabled")

    def show_login(self):
        self.clear_current_view()
        self.current_view = LoginView(self.root, self.on_login_success)
        
    def show_puzzle_list(self):
        self.clear_current_view()
        self.current_view = PuzzleListView(
            self.root, 
            self.token,
            self.show_puzzle_solver,
            self.show_puzzle_creator
        )
        
    def show_puzzle_solver(self, puzzle_id):
        self.clear_current_view()
        self.current_view = PuzzleSolverView(
            self.root,
            self.token,
            puzzle_id,
            self.show_puzzle_list
        )
        
    def show_puzzle_creator(self):
        self.clear_current_view()
        self.current_view = PuzzleCreatorView(
            self.root,
            self.token,
            self.show_puzzle_list
        )
        
    def show_statistics(self):
        self.clear_current_view()
        self.current_view = StatisticsView(
            self.root,
            self.token,
            self.user_id
        )
        self.current_view.pack(fill="both", expand=True)

    def clear_current_view(self):
        if self.current_view:
            self.current_view.destroy()
            
    def on_login_success(self, token, user_id):
        self.token = token
        self.user_id = user_id
        # Enable menu items after login
        self.game_menu.entryconfigure("Puzzle List", state="normal")
        self.game_menu.entryconfigure("Statistics", state="normal")
        self.game_menu.entryconfigure("Logout", state="normal")
        self.show_puzzle_list()

    def logout(self):
        self.token = None
        self.user_id = None
        # Disable menu items
        self.game_menu.entryconfigure("Puzzle List", state="disabled")
        self.game_menu.entryconfigure("Statistics", state="disabled")
        self.game_menu.entryconfigure("Logout", state="disabled")
        self.show_login()
        
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = CrosswordApp()
    app.run()