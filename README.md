# CS5003 Crossword Platform

A full-featured crossword puzzle platform with user authentication, puzzle solving, creation, and statistics tracking.

## Features

1. **User Authentication**
   - Register, login, and logout functionality
   - Secure session management with tokens
   - Password hashing (SHA-256)

2. **Puzzle Solving**
   - Browse and filter puzzles by difficulty/tags
   - Interactive grid for solving puzzles
   - Real-time answer validation

3. **Puzzle Creation**
   - Graphical editor for designing puzzles
   - Supports custom grid layouts, clues, and answers
   - Server-side validation

4. **Statistics & Leaderboard**
   - Tracks puzzles solved and average time
   - Global leaderboard ranking
   - Recent activity feed

5. **Technical Highlights**
   - Client-server architecture (TCP/IP + JSON)
   - SQLite database for persistent storage
   - Modular design with clear separation of concerns

## Setup & Usage

1. **Prerequisites**
   - Python 3.8+
   - Required packages: `tkinter`, `sqlite3`

2. **Running the Application**
   ```bash
   # Initialize database (first time only)
   python init_db.py

   # Start servers and client
   python start.py