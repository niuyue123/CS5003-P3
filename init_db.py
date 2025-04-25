import sqlite3
import os
import json
import traceback
import sys
import hashlib
from datetime import datetime

def hash_password(password):
    """使用SHA-256哈希密码"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    return hashlib.sha256(password).hexdigest()

def init_db():
    """初始化数据库"""
    try:
        # 删除现有数据库文件
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
            print(f"已删除现有数据库文件: {DATABASE}")
        
        # 连接到数据库
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 读取并执行schema.sql文件
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema = f.read()
        cursor.executescript(schema)
        print("已创建数据库表结构")
        
        # 创建测试用户
        test_user = {
            'username': 'test',
            'password': hash_password('test123'),
            'email': 'test@example.com',
            'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, registration_date)
            VALUES (?, ?, ?, ?)
        """, (test_user['username'], test_user['password'], 
              test_user['email'], test_user['registration_date']))
        
        test_user_id = cursor.lastrowid
        print(f"已创建测试用户，ID: {test_user_id}")
        
        # 初始化用户统计信息
        cursor.execute("""
            INSERT INTO user_stats (user_id, puzzles_solved, total_time, avg_solve_time)
            VALUES (?, 0, 0, 0)
        """, (test_user_id,))
        print("已初始化测试用户统计信息")
        
        # 添加示例谜题
        sample_puzzles = [
            {
                'title': 'Basic English Crossword 1',
                'tags': json.dumps(['easy', 'beginner']),
                'grid': json.dumps([
                    ['#', '.', '.', '.', '#'],
                    ['.', '.', '.', '.', '.'],
                    ['.', '.', '.', '.', '.'],
                    ['.', '.', '.', '.', '.'],
                    ['#', '.', '.', '.', '#']
                ]),
                'clues': json.dumps([
                    {
                        'number': 1,
                        'direction': 'A',
                        'row': 0,
                        'col': 1,
                        'clue': 'Greeting (3 letters)',
                        'answer': 'HI'
                    },
                    {
                        'number': 2,
                        'direction': 'A',
                        'row': 1,
                        'col': 0,
                        'clue': 'Our planet (5 letters)',
                        'answer': 'EARTH'
                    },
                    {
                        'number': 3,
                        'direction': 'A',
                        'row': 2,
                        'col': 0,
                        'clue': 'Opposite of "no" (3 letters)',
                        'answer': 'YES'
                    },
                    {
                        'number': 1,
                        'direction': 'D',
                        'row': 0,
                        'col': 1,
                        'clue': 'To perceive sound (4 letters)',
                        'answer': 'HEAR'
                    },
                    {
                        'number': 2,
                        'direction': 'D',
                        'row': 0,
                        'col': 2,
                        'clue': 'Vision organ (3 letters)',
                        'answer': 'EYE'
                    },
                    {
                        'number': 3,
                        'direction': 'D',
                        'row': 0,
                        'col': 3,
                        'clue': 'Exist (2 letters)',
                        'answer': 'BE'
                    }
                ]),
                'solution_key': json.dumps([
                    ['#', 'H', 'E', 'Y', '#'],
                    ['E', 'A', 'R', 'T', 'H'],
                    ['Y', 'E', 'S', '!', '!'],
                    ['!', '!', '!', '!', '!'],
                    ['#', '!', '!', '!', '#']
                ])
            },
            {
                'title': 'Animal Crossword',
                'tags': json.dumps(['animals', 'medium']),
                'grid': json.dumps([
                    ['.', '.', '.', '.', '#'],
                    ['.', '#', '.', '.', '.'],
                    ['.', '.', '.', '#', '.'],
                    ['.', '.', '.', '.', '.'],
                    ['#', '.', '.', '.', '.']
                ]),
                'clues': json.dumps([
                    {
                        'number': 1,
                        'direction': 'A',
                        'row': 0,
                        'col': 0,
                        'clue': 'King of the jungle (4 letters)',
                        'answer': 'LION'
                    },
                    {
                        'number': 2,
                        'direction': 'A',
                        'row': 1,
                        'col': 0,
                        'clue': 'Fastest land animal (7 letters)',
                        'answer': 'CHEETAH'
                    },
                    {
                        'number': 3,
                        'direction': 'A',
                        'row': 2,
                        'col': 0,
                        'clue': 'Largest cat species (5 letters)',
                        'answer': 'TIGER'
                    },
                    {
                        'number': 1,
                        'direction': 'D',
                        'row': 0,
                        'col': 0,
                        'clue': 'Animal with a long neck (7 letters)',
                        'answer': 'GIRAFFE'
                    },
                    {
                        'number': 2,
                        'direction': 'D',
                        'row': 0,
                        'col': 2,
                        'clue': 'Large gray mammal with a trunk (8 letters)',
                        'answer': 'ELEPHANT'
                    },
                    {
                        'number': 3,
                        'direction': 'D',
                        'row': 0,
                        'col': 3,
                        'clue': 'Black and white bear (5 letters)',
                        'answer': 'PANDA'
                    }
                ]),
                'solution_key': json.dumps([
                    ['L', 'I', 'O', 'N', '#'],
                    ['G', '#', 'E', 'L', 'E'],
                    ['I', 'R', 'P', '#', 'P'],
                    ['R', 'A', 'H', 'A', 'H'],
                    ['#', 'F', 'A', 'N', 'T']
                ])
            }
        ]
        
        for puzzle in sample_puzzles:
            cursor.execute("""
                INSERT INTO puzzles (title, tags, grid, clues, solution_key, author_id, date, solved_count)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 0)
            """, (puzzle['title'], puzzle['tags'], puzzle['grid'], 
                  puzzle['clues'], puzzle['solution_key'], test_user_id))
            print(f"已添加示例谜题：{puzzle['title']}")
        
        # 提交更改
        conn.commit()
        print("数据库初始化完成")
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        if 'conn' in locals():
            conn.rollback()
    except Exception as e:
        print(f"其他错误: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    init_db() 