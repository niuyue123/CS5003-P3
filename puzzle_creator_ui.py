import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class PuzzleCreatorWindow(tk.Toplevel):
    """
    Main window for creating a new crossword puzzle with a graphical editor.
    Launched from the main application window.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent # Store parent for potential communication
        self.title("Create New Crossword Puzzle")
        # self.grab_set() # Make modal
        # self.transient(parent)

        # --- Configuration ---
        # Make dimensions configurable at start?
        self.grid_rows = 15
        self.grid_cols = 15
        self.cell_size = 30
        self.number_font = ('Arial', 8)
        self.selected_outline_color = 'blue'
        self.selected_outline_width = 2

        # --- Internal Data Structures ---
        self.grid_state = self._initialize_grid_state()
        # clues_data format: { number: {'coords': (r,c), 'A': {'clue':'', 'answer':''}, 'D':{...} }, ...}
        self.clues_data = {}
        self.current_clue_number = 1
        self.selected_clue_num = None
        self.selected_clue_dir = None # 'A' or 'D'

        # --- UI Frames ---
        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(pady=5, padx=10, fill=tk.X)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(pady=5, padx=10, expand=True, fill=tk.BOTH)

        self.grid_frame = ttk.LabelFrame(self.main_frame, text="Grid Editor")
        self.grid_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.clue_entry_frame = ttk.LabelFrame(self.main_frame, text="Clue Editor")
        self.clue_entry_frame.pack(side=tk.RIGHT, padx=5, fill=tk.Y, ipadx=5)

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(pady=10, padx=10, fill=tk.X)

        # --- Populate Frames ---
        self._create_info_widgets()
        self._create_grid_canvas()
        self._create_clue_entry_widgets()
        self._create_button_widgets()

        # --- Initial Setup ---
        self._update_clue_numbers() # Calculate initial numbers
        self._draw_grid()           # Draw initial grid and numbers

        # Center the window (optional)
        # self.center_window()

    def center_window(self):
        """Centers the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _initialize_grid_state(self):
        """Initializes the internal grid data structure."""
        return [[{'is_black': False, 'number': 0, 'tags': f'cell_{r}_{c}'}
                 for c in range(self.grid_cols)]
                for r in range(self.grid_rows)]

    def _create_info_widgets(self):
        """Creates widgets for puzzle title, dimensions, etc."""
        ttk.Label(self.info_frame, text="Title:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.title_entry = ttk.Entry(self.info_frame, width=40)
        self.title_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)

        size_button = ttk.Button(self.info_frame, text=f"Size: {self.grid_rows}x{self.grid_cols}", command=self._change_grid_size)
        size_button.grid(row=0, column=2, padx=10, pady=2)

        self.info_frame.columnconfigure(1, weight=1)

    def _create_grid_canvas(self):
        """Creates the Canvas widget for the grid."""
        canvas_width = self.grid_cols * self.cell_size
        canvas_height = self.grid_rows * self.cell_size
        self.grid_canvas = tk.Canvas(self.grid_frame, width=canvas_width, height=canvas_height, bg='white', borderwidth=0, highlightthickness=0)
        self.grid_canvas.pack(pady=5, padx=5)
        self.grid_canvas.bind("<Button-1>", self._handle_grid_click)

    def _create_clue_entry_widgets(self):
        """Creates widgets for selecting, entering, and updating clues."""
        # Clue Selection Listbox
        ttk.Label(self.clue_entry_frame, text="Available Clues:").pack(pady=(5,0), anchor=tk.W)
        self.clue_list_frame = ttk.Frame(self.clue_entry_frame)
        self.clue_list_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self.clue_scrollbar = ttk.Scrollbar(self.clue_list_frame, orient=tk.VERTICAL)
        self.clue_listbox = tk.Listbox(self.clue_list_frame, yscrollcommand=self.clue_scrollbar.set, height=15)
        self.clue_scrollbar.config(command=self.clue_listbox.yview)
        self.clue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.clue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.clue_listbox.bind('<<ListboxSelect>>', self._on_clue_select)

        # Selected Clue Display
        self.selected_clue_label = ttk.Label(self.clue_entry_frame, text="Selected: None")
        self.selected_clue_label.pack(pady=5, anchor=tk.W)

        # Entry Fields Frame
        entry_frame = ttk.Frame(self.clue_entry_frame)
        entry_frame.pack(fill=tk.X, pady=5)

        ttk.Label(entry_frame, text="Clue:").grid(row=0, column=0, sticky=tk.W, padx=2)
        self.clue_text_entry = ttk.Entry(entry_frame, width=30)
        self.clue_text_entry.grid(row=0, column=1, sticky=tk.EW, padx=2)

        ttk.Label(entry_frame, text="Answer:").grid(row=1, column=0, sticky=tk.W, padx=2)
        self.answer_text_entry = ttk.Entry(entry_frame, width=30)
        self.answer_text_entry.grid(row=1, column=1, sticky=tk.EW, padx=2)
        self.answer_text_entry.bind("<FocusOut>", self._validate_answer_length_event) # Basic validation on focus out

        entry_frame.columnconfigure(1, weight=1)

        # Update Button
        self.update_clue_button = ttk.Button(self.clue_entry_frame, text="Update Clue", command=self._update_clue_data, state=tk.DISABLED)
        self.update_clue_button.pack(pady=5)

        # Validation Label
        self.validation_label = ttk.Label(self.clue_entry_frame, text="", foreground="red")
        self.validation_label.pack(pady=(0,5), anchor=tk.W)


    def _create_button_widgets(self):
        """Creates the Submit and Cancel buttons."""
        ttk.Button(self.button_frame, text="Submit Puzzle", command=self._submit_puzzle).pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    # --- Grid Interaction and Drawing ---

    def _handle_grid_click(self, event):
        """Handles clicks on the grid canvas to toggle black/white."""
        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if 0 <= row < self.grid_rows and 0 <= col < self.grid_cols:
            # Check if there's a letter in this position
            letter_tag = f"letter_{row}_{col}"
            letter_items = self.grid_canvas.find_withtag(letter_tag)
            
            # If turning black and there's a letter, show warning
            if not self.grid_state[row][col]['is_black'] and letter_items:
                if not messagebox.askyesno("Warning", 
                    "This cell contains a letter. Making it black will delete the letter. Continue?"):
                    return

            # Toggle state
            self.grid_state[row][col]['is_black'] = not self.grid_state[row][col]['is_black']
            # Clear number if it becomes black
            if self.grid_state[row][col]['is_black']:
                self.grid_state[row][col]['number'] = 0
                # Delete letter (if exists)
                if letter_items:
                    self.grid_canvas.delete(letter_tag)

            # Recalculate numbers and update clue structures
            self._update_clue_numbers()
            # Redraw the affected cell
            self._redraw_cell(row, col)
            # Redraw all numbers (as they might change)
            self._draw_numbers()
            # Update the clue listbox display
            self._populate_clue_listbox()
            # Clear selection as numbering changed
            self._clear_clue_selection()

    def _draw_grid(self):
        """Draws the entire grid initially."""
        self.grid_canvas.delete("all")
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                self._redraw_cell(r, c)
        self._draw_numbers()

    def _redraw_cell(self, row, col, is_selected=False):
        """Draws or redraws a single cell."""
        if not (0 <= row < self.grid_rows and 0 <= col < self.grid_cols): return

        cell_data = self.grid_state[row][col]
        x1, y1 = col * self.cell_size, row * self.cell_size
        x2, y2 = x1 + self.cell_size, y1 + self.cell_size
        tag = cell_data['tags']

        # 保存当前单元格中的字母（如果有）
        letter_tag = f"letter_{row}_{col}"
        letter_items = self.grid_canvas.find_withtag(letter_tag)
        letter_text = ""
        if letter_items:
            letter_text = self.grid_canvas.itemcget(letter_items[0], "text")

        self.grid_canvas.delete(tag) # Delete previous items for this cell

        fill_color = 'black' if cell_data['is_black'] else 'white'
        outline_color = self.selected_outline_color if is_selected else 'grey'
        outline_width = self.selected_outline_width if is_selected else 1

        self.grid_canvas.create_rectangle(x1, y1, x2, y2,
                                          fill=fill_color,
                                          outline=outline_color,
                                          width=outline_width,
                                          tags=tag)

        # 如果单元格不是黑色且之前有字母，重新显示字母
        if not cell_data['is_black'] and letter_text:
            x = col * self.cell_size + self.cell_size/2
            y = row * self.cell_size + self.cell_size/2
            self.grid_canvas.create_text(x, y,
                                       text=letter_text,
                                       font=('Arial', 14),
                                       tags=(letter_tag, "answer_letter"))

    def _draw_numbers(self):
        """Draws the clue numbers on the grid."""
        self.grid_canvas.delete("clue_number") # Clear old numbers
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                cell_data = self.grid_state[r][c]
                if not cell_data['is_black'] and cell_data['number'] > 0:
                    x1, y1 = c * self.cell_size, r * self.cell_size
                    self.grid_canvas.create_text(x1 + 3, y1 + 2, # Small offset
                                                 text=str(cell_data['number']),
                                                 anchor=tk.NW,
                                                 font=self.number_font,
                                                 tags=("clue_number", cell_data['tags'])) # Tag with cell too

    # --- Clue Numbering Logic ---

    def _update_clue_numbers(self):
        """Recalculates clue numbers based on the current grid state."""
        # Reset existing numbers and clue data structure
        self.clues_data = {}
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                self.grid_state[r][c]['number'] = 0

        current_number = 1
        numbered_coords = set() # Track coords that received a number

        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                if not self.grid_state[r][c]['is_black']:
                    # Check if it's a potential start for Across or Down
                    is_across_start = (c == 0 or self.grid_state[r][c-1]['is_black']) and \
                                      (c + 1 < self.grid_cols and not self.grid_state[r][c+1]['is_black'])
                    is_down_start = (r == 0 or self.grid_state[r-1][c]['is_black']) and \
                                    (r + 1 < self.grid_rows and not self.grid_state[r+1][c]['is_black'])

                    if is_across_start or is_down_start:
                        # Assign a number if this coordinate hasn't been numbered yet
                        if (r, c) not in numbered_coords:
                            self.grid_state[r][c]['number'] = current_number
                            self.clues_data[current_number] = {'coords': (r, c)} # Store coords
                            numbered_coords.add((r, c))
                            current_number += 1

                        # Add entries for potential Across/Down clues for this number
                        num = self.grid_state[r][c]['number']
                        if is_across_start:
                            if 'A' not in self.clues_data[num]:
                                self.clues_data[num]['A'] = {'clue': '', 'answer': ''}
                        if is_down_start:
                             if 'D' not in self.clues_data[num]:
                                self.clues_data[num]['D'] = {'clue': '', 'answer': ''}

        self.current_clue_number = current_number # Store next available number


    # --- Clue Entry Logic ---

    def _populate_clue_listbox(self):
        """Updates the listbox with currently available clues."""
        self.clue_listbox.delete(0, tk.END)
        sorted_numbers = sorted(self.clues_data.keys())
        for num in sorted_numbers:
            if 'A' in self.clues_data[num]:
                self.clue_listbox.insert(tk.END, f"{num} Across")
            if 'D' in self.clues_data[num]:
                self.clue_listbox.insert(tk.END, f"{num} Down")

    def _on_clue_select(self, event):
        """Handles selection change in the clue listbox."""
        selection = self.clue_listbox.curselection()
        if not selection:
            self._clear_clue_selection()
            return

        selected_text = self.clue_listbox.get(selection[0])
        parts = selected_text.split()
        try:
            num = int(parts[0])
            direction = 'A' if parts[1] == 'Across' else 'D'

            if num in self.clues_data and direction in self.clues_data[num]:
                self.selected_clue_num = num
                self.selected_clue_dir = direction
                self.selected_clue_label.config(text=f"Selected: {selected_text}")

                # Populate entry fields
                clue_info = self.clues_data[num][direction]
                self.clue_text_entry.delete(0, tk.END)
                self.clue_text_entry.insert(0, clue_info.get('clue', ''))
                self.answer_text_entry.delete(0, tk.END)
                self.answer_text_entry.insert(0, clue_info.get('answer', ''))

                self.update_clue_button.config(state=tk.NORMAL)
                self.validation_label.config(text="") # Clear validation message
                self._highlight_selected_clue_cells() # Highlight on grid
            else:
                self._clear_clue_selection()

        except (IndexError, ValueError):
            self._clear_clue_selection()

    def _clear_clue_selection(self):
        """Resets the clue selection state."""
        self.selected_clue_num = None
        self.selected_clue_dir = None
        self.selected_clue_label.config(text="Selected: None")
        self.clue_text_entry.delete(0, tk.END)
        self.answer_text_entry.delete(0, tk.END)
        self.update_clue_button.config(state=tk.DISABLED)
        self.validation_label.config(text="")
        self.clue_listbox.selection_clear(0, tk.END)
        self._highlight_selected_clue_cells() # Remove highlight

    def _update_clue_data(self):
        """Updates the internal clues_data with values from entry fields."""
        if self.selected_clue_num is None or self.selected_clue_dir is None:
            return

        num = self.selected_clue_num
        direction = self.selected_clue_dir
        clue_text = self.clue_text_entry.get().strip()
        answer_text = self.answer_text_entry.get().strip().upper() # Force uppercase answers

        if num in self.clues_data and direction in self.clues_data[num]:
            # Basic validation
            if not clue_text:
                 self.validation_label.config(text="Clue text cannot be empty")
                 return
            if not answer_text:
                 self.validation_label.config(text="Answer cannot be empty")
                 return
            if not self._validate_answer_length(answer_text): # Check length
                return # Message set by validation function

            # Update data
            self.clues_data[num][direction]['clue'] = clue_text
            self.clues_data[num][direction]['answer'] = answer_text
            self.validation_label.config(text="Clue updated", foreground="green")
            
            # Update letter display in grid
            self._display_answer_in_grid(num, direction, answer_text)
        else:
             self.validation_label.config(text="Error: Clue not found", foreground="red")

    def _display_answer_in_grid(self, num, direction, answer):
        """Display answer letters in the grid"""
        if num not in self.clues_data:
            return
            
        r_start, c_start = self.clues_data[num]['coords']
        
        for i, letter in enumerate(answer):
            r, c = r_start, c_start
            if direction == 'A':
                c += i
            else:  # direction == 'D'
                r += i
                
            if 0 <= r < self.grid_rows and 0 <= c < self.grid_cols:
                # Delete previous letter (if exists)
                self.grid_canvas.delete(f"letter_{r}_{c}")
                # Add new letter
                x = c * self.cell_size + self.cell_size/2
                y = r * self.cell_size + self.cell_size/2
                self.grid_canvas.create_text(x, y,
                                          text=letter,
                                          font=('Arial', 14),
                                          tags=(f"letter_{r}_{c}", "answer_letter"))

    def _highlight_selected_clue_cells(self):
        """Highlights the cells on the grid corresponding to the selected clue."""
        # First, redraw all cells without highlight
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                self._redraw_cell(r, c, is_selected=False)
        self._draw_numbers() # Redraw numbers on top

        if self.selected_clue_num is None or self.selected_clue_dir is None:
            return # Nothing selected

        num = self.selected_clue_num
        direction = self.selected_clue_dir
        if num not in self.clues_data: return
        r_start, c_start = self.clues_data[num]['coords']

        length = self._get_word_length(num, direction)
        if length is None: return

        # Highlight the cells
        for i in range(length):
            r, c = r_start, c_start
            if direction == 'A':
                c += i
            else: # direction == 'D'
                r += i

            if 0 <= r < self.grid_rows and 0 <= c < self.grid_cols and not self.grid_state[r][c]['is_black']:
                 self._redraw_cell(r, c, is_selected=True)

        self._draw_numbers() # Redraw numbers again to ensure they are on top of highlight


    # --- Validation ---

    def _validate_answer_length_event(self, event=None):
        """Validation triggered by FocusOut or potentially button click."""
        if self.selected_clue_num is None or self.selected_clue_dir is None:
            return True # No clue selected to validate against
        answer = self.answer_text_entry.get().strip()
        return self._validate_answer_length(answer)


    def _validate_answer_length(self, answer):
        """Checks if the provided answer length matches the grid space."""
        if self.selected_clue_num is None or self.selected_clue_dir is None:
            return True # Cannot validate if nothing is selected

        expected_length = self._get_word_length(self.selected_clue_num, self.selected_clue_dir)

        if expected_length is None:
             self.validation_label.config(text="Error: Cannot determine grid length.", foreground="red")
             return False

        if len(answer) != expected_length:
            self.validation_label.config(text=f"Error: Answer length ({len(answer)}) must be {expected_length}.", foreground="red")
            return False
        else:
            self.validation_label.config(text="") # Clear validation message on success
            return True

    def _get_word_length(self, number, direction):
        """Calculates the number of white squares for a given clue start."""
        if number not in self.clues_data: return None
        r_start, c_start = self.clues_data[number]['coords']

        length = 0
        if direction == 'A':
            c = c_start
            while c < self.grid_cols and not self.grid_state[r_start][c]['is_black']:
                length += 1
                c += 1
        elif direction == 'D':
            r = r_start
            while r < self.grid_rows and not self.grid_state[r][c_start]['is_black']:
                length += 1
                r += 1
        return length if length > 0 else None


    # --- Data Packaging and Submission ---

    def _submit_puzzle(self):
        """Handles final validation and puzzle submission process."""
        # Collect all missing information
        missing_info = []
        
        # 1. Check title
        title = self.title_entry.get().strip()
        if not title:
            missing_info.append("- Puzzle title")

        # Print debug information
        print("[DEBUG] Current grid state:")
        self._print_grid_state()

        # 2. Check if grid is valid
        valid_grid = False
        white_cells = []
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                if not self.grid_state[r][c]['is_black']:
                    valid_grid = True
                    white_cells.append((r, c))
        
        if not valid_grid:
            missing_info.append("- Grid design (at least one writable white cell needed)")
        
        print(f"[DEBUG] Found white cells: {white_cells}")

        # 3. Check filled answers
        filled_positions = self._get_filled_positions()
        print(f"[DEBUG] Positions with letters: {filled_positions}")

        # 4. Check clue information
        print("[DEBUG] Current clue data:")
        for num in sorted(self.clues_data.keys()):
            clue_info = self.clues_data[num]
            print(f"Number {num}:")
            if 'A' in clue_info:
                print(f"  Across - Clue: {clue_info['A'].get('clue', 'None')}, Answer: {clue_info['A'].get('answer', 'None')}")
            if 'D' in clue_info:
                print(f"  Down - Clue: {clue_info['D'].get('clue', 'None')}, Answer: {clue_info['D'].get('answer', 'None')}")

        # 5. Check clues for each filled position
        if filled_positions:
            for r, c in filled_positions:
                found = False
                for num, clue_data in self.clues_data.items():
                    if self._is_position_in_clue(r, c, num, clue_data):
                        found = True
                        break
                if not found:
                    missing_info.append(f"- Letter at row {r+1} column {c+1} has no corresponding clue")

        # If there's missing information, show error message
        if missing_info:
            error_message = "Missing required information:\n\n" + "\n".join(missing_info)
            messagebox.showerror("Creation Failed", error_message)
            return

        # All validation passed, prepare to submit data
        try:
            puzzle_data = self._prepare_puzzle_data(title)
            print("[DEBUG] Prepared puzzle data:", puzzle_data)

            # If callback function is set, call it
            if hasattr(self, 'submit_callback') and callable(self.submit_callback):
                self.submit_callback(puzzle_data)
            else:
                print("[DEBUG] No submit callback set, showing simulated success message")
                messagebox.showinfo("Success", "Puzzle created successfully (simulated)")
                self.destroy()

        except Exception as e:
            print(f"[ERROR] Error preparing puzzle data: {str(e)}")
            messagebox.showerror("Error", f"Error preparing puzzle data: {str(e)}")

    def _print_grid_state(self):
        """Print current grid state for debugging"""
        for r in range(self.grid_rows):
            row = []
            for c in range(self.grid_cols):
                if self.grid_state[r][c]['is_black']:
                    row.append('#')
                else:
                    letter_tag = f"letter_{r}_{c}"
                    letter_items = self.grid_canvas.find_withtag(letter_tag)
                    if letter_items:
                        letter = self.grid_canvas.itemcget(letter_items[0], "text")
                        row.append(letter)
                    else:
                        row.append('.')
            print(''.join(row))

    def _is_position_in_clue(self, r, c, num, clue_data):
        """Check if the specified position belongs to a clue"""
        if 'coords' not in clue_data:
            return False
            
        start_r, start_c = clue_data['coords']
        
        # Check across clue
        if 'A' in clue_data:
            if r == start_r and c >= start_c:
                length = self._get_word_length(num, 'A')
                if c < start_c + length:
                    return True
                    
        # Check down clue
        if 'D' in clue_data:
            if c == start_c and r >= start_r:
                length = self._get_word_length(num, 'D')
                if r < start_r + length:
                    return True
                    
        return False

    def _prepare_puzzle_data(self, title):
        """Prepare puzzle data for submission"""
        # Create solution grid
        solution_grid = []
        for r in range(self.grid_rows):
            row = []
            for c in range(self.grid_cols):
                if self.grid_state[r][c]['is_black']:
                    row.append('#')
                else:
                    letter_tag = f"letter_{r}_{c}"
                    letter_items = self.grid_canvas.find_withtag(letter_tag)
                    if letter_items:
                        letter = self.grid_canvas.itemcget(letter_items[0], "text")
                        row.append(letter)
                    else:
                        row.append('.')
            solution_grid.append(''.join(row))

        return {
            "title": title,
            "grid": self._convert_grid_state_to_layout(),
            "clues": self._package_clues_data(),
            "solution_key": solution_grid,
            "tags": []
        }

    def _get_filled_positions(self):
        """Get all positions with filled letters"""
        filled_positions = []
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                if not self.grid_state[r][c]['is_black']:
                    letter_tag = f"letter_{r}_{c}"
                    letter_items = self.grid_canvas.find_withtag(letter_tag)
                    if letter_items:
                        filled_positions.append((r, c))
        return filled_positions

    def _package_clues_data(self):
        """Package filled clues and answers into the required format"""
        # Initialize clues structure
        packaged_clues = {
            "across": [],
            "down": []
        }
        
        # Get all filled positions
        filled_positions = self._get_filled_positions()
        if not filled_positions:
            return packaged_clues

        # Process clues
        processed_clues = set()
        for r, c in filled_positions:
            for num, clue_data in self.clues_data.items():
                for direction in ['A', 'D']:
                    if direction in clue_data and (num, direction) not in processed_clues:
                        start_r, start_c = clue_data['coords']
                        length = self._get_word_length(num, direction)
                        
                        # Check if this position belongs to current clue
                        is_part_of_clue = False
                        if direction == 'A' and r == start_r and c >= start_c and c < start_c + length:
                            is_part_of_clue = True
                        elif direction == 'D' and c == start_c and r >= start_r and r < start_r + length:
                            is_part_of_clue = True
                            
                        if is_part_of_clue:
                            clue_info = clue_data[direction]
                            if clue_info.get('clue') and clue_info.get('answer'):
                                # Add clue to appropriate list
                                clue_text = f"{clue_info['clue']}"
                                if direction == 'A':
                                    packaged_clues['across'].append(clue_text)
                                else:  # direction == 'D'
                                    packaged_clues['down'].append(clue_text)
                                processed_clues.add((num, direction))

        return packaged_clues

    def _convert_grid_state_to_layout(self):
        """Convert internal grid state to API required format (list of strings)"""
        layout = []
        for r in range(self.grid_rows):
            row_str = "".join(["#" if self.grid_state[r][c]['is_black'] else "." for c in range(self.grid_cols)])
            layout.append(row_str)
        return layout

    # --- Grid Size Change ---
    def _change_grid_size(self):
        """Allows the user to change the grid dimensions."""
        new_rows = simpledialog.askinteger("Grid Size", "Enter new number of rows:",
                                           initialvalue=self.grid_rows, minvalue=5, maxvalue=30, parent=self)
        if new_rows is None: return # User cancelled

        new_cols = simpledialog.askinteger("Grid Size", "Enter new number of columns:",
                                           initialvalue=self.grid_cols, minvalue=5, maxvalue=30, parent=self)
        if new_cols is None: return # User cancelled

        if new_rows == self.grid_rows and new_cols == self.grid_cols:
            return # No change

        # Confirm data loss
        if messagebox.askyesno("Confirm Resize", "Changing the grid size will clear the current grid and clues. Proceed?"):
            self.grid_rows = new_rows
            self.grid_cols = new_cols

            # Re-initialize everything
            self.grid_state = self._initialize_grid_state()
            self.clues_data = {}
            self.current_clue_number = 1
            self._clear_clue_selection()

            # Resize canvas
            canvas_width = self.grid_cols * self.cell_size
            canvas_height = self.grid_rows * self.cell_size
            self.grid_canvas.config(width=canvas_width, height=canvas_height)

            # Update size label
            for widget in self.info_frame.winfo_children():
                if isinstance(widget, ttk.Button) and "Size:" in widget.cget("text"):
                    widget.config(text=f"Size: {self.grid_rows}x{self.grid_cols}")
                    break

            # Redraw and update clues
            self._update_clue_numbers()
            self._draw_grid()
            self._populate_clue_listbox()
            self.center_window() # Recenter after resize


# --- To run this window for testing (usually launched from main app) ---
if __name__ == '__main__':
    try:
        # Use themed widgets if available
        from ttkthemes import ThemedTk
        root = ThemedTk(theme="arc") # Or other themes like "plastik", "adapta"
    except ImportError:
        root = tk.Tk() # Fallback to standard Tkinter

    root.withdraw() # Hide the main root window

    # Example of how to launch it (replace 'root' with your main app window)
    creator_window = PuzzleCreatorWindow(root)
    root.wait_window(creator_window) # Wait until creator window is closed

    root.destroy()
