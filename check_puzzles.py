import sqlite3
import json

def check_puzzles():
    try:
        conn = sqlite3.connect('DATABASE-puzzles.db')
        c = conn.cursor()
        
        print("查询puzzles表中的所有谜题：")
        c.execute("""
            SELECT p.id, p.title, p.tags, p.grid, p.clues, p.solution_key, 
                   p.author_id, u.username as author_name
            FROM puzzles p
            LEFT JOIN users u ON p.author_id = u.id
        """)
        puzzles = c.fetchall()
        
        if not puzzles:
            print("puzzles表中没有数据")
        else:
            print("\nID | 标题 | 作者 | 标签")
            print("-" * 80)
            for puzzle in puzzles:
                puzzle_id, title, tags, grid, clues, solution, author_id, author_name = puzzle
                tags_list = json.loads(tags) if tags else []
                print(f"{puzzle_id} | {title} | {author_name} | {', '.join(tags_list)}")
                print(f"网格结构：")
                grid_data = json.loads(grid)
                for row in grid_data:
                    print(''.join(row))
                print("-" * 80)
                
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_puzzles() 