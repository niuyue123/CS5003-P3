import sqlite3
import json

def check_puzzles():
    try:
        conn = sqlite3.connect('DATABASE-puzzles.db')
        c = conn.cursor()
        
        print("Querying all puzzles in puzzles table:")
        c.execute("""
            SELECT p.id, p.title, p.tags, p.grid, p.clues, p.solution_key, 
                   p.author_id, u.username as author_name
            FROM puzzles p
            LEFT JOIN users u ON p.author_id = u.id
        """)
        puzzles = c.fetchall()
        
        if not puzzles:
            print("No data in puzzles table")
        else:
            print("\nID | Title | Author | Tags")
            print("-" * 80)
            for puzzle in puzzles:
                puzzle_id, title, tags, grid, clues, solution, author_id, author_name = puzzle
                tags_list = json.loads(tags) if tags else []
                print(f"{puzzle_id} | {title} | {author_name} | {', '.join(tags_list)}")
                print(f"Grid structure:")
                grid_data = json.loads(grid)
                for row in grid_data:
                    print(''.join(row))
                print("-" * 80)
                
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_puzzles() 