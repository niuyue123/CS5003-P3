import sqlite3
import os
import json
import traceback
import sys
import hashlib
from datetime import datetime

# Define database file path
DATABASE = 'DATABASE-puzzles.db'

def hash_password(password):
    """Hash password using SHA-256"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    return hashlib.sha256(password).hexdigest()

def init_db():
    """Initialize database"""
    try:
        # Delete existing database file
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
            print(f"Deleted existing database file: {DATABASE}")
        
        # Connect to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Read and execute schema.sql file
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema = f.read()
        cursor.executescript(schema)
        print("Created database table structure")
        
        # Create test user
        test_user = {
            'username': 'test',
            'password_hash': hash_password('test123')
        }
        
        cursor.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        """, (test_user['username'], test_user['password_hash']))
        
        test_user_id = cursor.lastrowid
        print(f"Created test user, ID: {test_user_id}")
        
        # Initialize user statistics
        cursor.execute("""
            INSERT INTO user_stats (user_id, puzzles_solved, avg_time, last_login)
            VALUES (?, 0, 0, CURRENT_TIMESTAMP)
        """, (test_user_id,))
        print("Initialized test user statistics")
        
        # Add sample puzzles
        sample_puzzles = [
            {
                'title': 'Simple Crossword 1',
                'tags': json.dumps(['easy', 'beginner']),
                'grid': json.dumps([
                    ['#', '.', '.', '.', '#'],
                    ['.', '.', '.', '.', '.'],
                    ['.', '.', '.', '.', '.'],
                    ['.', '.', '.', '.', '.'],
                    ['#', '.', '.', '.', '#']
                ]),
                'clues': json.dumps({
                    'across': [
                        'Informal greeting',
                        'Planet Earth',
                        'Common greeting'
                    ],
                    'down': [
                        'Feeling of joy',
                        'Feeling unhappy',
                        'Feeling mad'
                    ]
                }),
                'solution_key': json.dumps([
                    ['#', 'H', 'E', 'Y', '#'],
                    ['W', 'O', 'R', 'L', 'D'],
                    ['H', 'E', 'L', 'L', 'O'],
                    ['B', 'Y', 'E', '!', '!'],
                    ['#', 'S', 'A', 'D', '#']
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
                'clues': json.dumps({
                    'across': [
                        'King of the jungle',
                        'Fastest land animal',
                        'Largest big cat'
                    ],
                    'down': [
                        'Long-necked animal',
                        'Large gray mammal',
                        'Black and white bear'
                    ]
                }),
                'solution_key': json.dumps([
                    ['L', 'I', 'O', 'N', '#'],
                    ['E', '#', 'L', 'A', 'P'],
                    ['O', 'T', 'E', '#', 'A'],
                    ['P', 'I', 'G', 'E', 'R'],
                    ['#', 'G', 'E', 'R', 'S']
                ])
            },{
                'title': 'NY TIMES, THU, JAN 01, 1976',
                'tags': json.dumps(['classic', 'challenging']),
                'grid': json.dumps([
                    ['#','.','.','.','#','.','.','.','#','#','.','.','.','.','#'],
                    ['.','.','.','.','#','.','.','.','.','#','.','.','.','.','.'],
                    ['.','.','.','.','#','.','.','.','.','.','.','.','.','.','.'],
                    ['.','.','.','.','.','.','.','.','#','.','.','.','.','.','#'],
                    ['#','#','#','#','.','.','.','.','#','.','.','.','.','#','#'],
                    ['#','#','.','.','.','.','.','.','#','.','.','.','.','.','.'],
                    ['.','.','.','.','.','.','.','#','.','.','.','.','.','#','.'],
                    ['.','.','.','.','.','.','#','#','.','.','.','.','#','.','.'],
                    ['.','.','.','.','.','#','.','.','.','.','.','#','.','.','.'],
                    ['.','.','.','.','.','.','.','.','.','.','#','.','.','.','.'],
                    ['.','.','#','#','#','.','.','.','.','#','.','.','.','.','#'],
                    ['#','#','#','#','.','.','.','.','.','#','.','.','.','.','.'],
                    ['.','.','.','.','.','.','.','.','.','.','.','.','.','#','.'],
                    ['.','.','.','.','.','.','.','.','#','.','.','.','.','#','.'],
                    ['.','.','.','.','.','.','.','.','#','.','.','.','.','#','.']
                ]),
                'clues': json.dumps({
                    'across': [
                        {'number': 1, 'direction': 'A', 'row': 0, 'col': 0, 'clue': 'Attention getter', 'answer': 'AHEM'},
                        {'number': 5, 'direction': 'A', 'row': 0, 'col': 5, 'clue': 'Zola title', 'answer': 'NANA'},
                        {'number': 9, 'direction': 'A', 'row': 0, 'col': 10, 'clue': 'Garlic unit', 'answer': 'CLOVE'},
                        {'number': 14, 'direction': 'A', 'row': 1, 'col': 0, 'clue': 'Met V.I.P.', 'answer': 'DIVA'},
                        {'number': 15, 'direction': 'A', 'row': 1, 'col': 5, 'clue': 'Is obligated', 'answer': 'OWES'},
                        {'number': 16, 'direction': 'A', 'row': 1, 'col': 10, 'clue': 'Volcanic outputs', 'answer': 'LAVAS'},
                        {'number': 17, 'direction': 'A', 'row': 2, 'col': 0, 'clue': 'Hymn word', 'answer': 'AMEN'},
                        {'number': 18, 'direction': 'A', 'row': 2, 'col': 5, 'clue': 'Nail specialist', 'answer': 'MANICURIST'},
                        {'number': 20, 'direction': 'A', 'row': 3, 'col': 0, 'clue': 'May apple', 'answer': 'MANDRAKE'},
                        {'number': 22, 'direction': 'A', 'row': 3, 'col': 9, 'clue': 'Tolerate', 'answer': 'ABIDE'},
                        {'number': 23, 'direction': 'A', 'row': 4, 'col': 4, 'clue': 'Staff man', 'answer': 'AIDE'},
                        {'number': 24, 'direction': 'A', 'row': 4, 'col': 9, 'clue': 'Terza ___', 'answer': 'RIMA'},
                        {'number': 25, 'direction': 'A', 'row': 5, 'col': 2, 'clue': 'Bowling scores', 'answer': 'SPARES'},
                        {'number': 28, 'direction': 'A', 'row': 5, 'col': 9, 'clue': 'Aquatic mammals', 'answer': 'MANATEES'},
                        {'number': 32, 'direction': 'A', 'row': 6, 'col': 2, 'clue': 'Red dye', 'answer': 'EOSIN'},
                        {'number': 33, 'direction': 'A', 'row': 6, 'col': 8, 'clue': "Baker's ___", 'answer': 'DOZEN'},
                        {'number': 34, 'direction': 'A', 'row': 7, 'col': 0, 'clue': 'Geographical abbr.', 'answer': 'LAT'},
                        {'number': 35, 'direction': 'A', 'row': 7, 'col': 3, 'clue': 'Org.', 'answer': 'ASSN'},
                        {'number': 36, 'direction': 'A', 'row': 7, 'col': 8, 'clue': 'Tender spots', 'answer': 'SORES'},
                        {'number': 37, 'direction': 'A', 'row': 7, 'col': 13, 'clue': 'Venetian ruler', 'answer': 'DOGE'},
                        {'number': 38, 'direction': 'A', 'row': 8, 'col': 0, 'clue': 'Draw', 'answer': 'TIE'},
                        {'number': 39, 'direction': 'A', 'row': 8, 'col': 6, 'clue': 'Something, in Germany', 'answer': 'ETWAS'},
                        {'number': 40, 'direction': 'A', 'row': 8, 'col': 12, 'clue': 'Turn back', 'answer': 'REPEL'},
                        {'number': 41, 'direction': 'A', 'row': 9, 'col': 1, 'clue': 'Footstools', 'answer': 'OTTOMANS'},
                        {'number': 43, 'direction': 'A', 'row': 9, 'col': 11, 'clue': '"I am a ___"', 'answer': 'CAMERA'},
                        {'number': 44, 'direction': 'A', 'row': 10, 'col': 5, 'clue': 'Chimneys, in Glasgow', 'answer': 'LUMS'},
                        {'number': 45, 'direction': 'A', 'row': 10, 'col': 10, 'clue': 'Teasdale', 'answer': 'SARA'},
                        {'number': 46, 'direction': 'A', 'row': 11, 'col': 4, 'clue': 'Soup server', 'answer': 'LADLE'},
                        {'number': 48, 'direction': 'A', 'row': 11, 'col': 10, 'clue': 'Fictional villain', 'answer': 'FUMANCHU'},
                        {'number': 52, 'direction': 'A', 'row': 12, 'col': 0, 'clue': 'Pawed', 'answer': 'MANHANDLED'},
                        {'number': 54, 'direction': 'A', 'row': 12, 'col': 13, 'clue': 'Sullen', 'answer': 'DOUR'},
                        {'number': 55, 'direction': 'A', 'row': 13, 'col': 3, 'clue': 'Old English coin', 'answer': 'GROAT'},
                        {'number': 56, 'direction': 'A', 'row': 13, 'col': 9, 'clue': 'Florida county', 'answer': 'DADE'},
                        {'number': 57, 'direction': 'A', 'row': 14, 'col': 0, 'clue': 'Fitzgerald', 'answer': 'ELLA'},
                        {'number': 58, 'direction': 'A', 'row': 14, 'col': 4, 'clue': 'French relative', 'answer': 'TANTE'},
                        {'number': 59, 'direction': 'A', 'row': 14, 'col': 9, 'clue': 'Machine gun', 'answer': 'STEN'},
                        {'number': 60, 'direction': 'A', 'row': 14, 'col': 14, 'clue': 'Start a card game', 'answer': 'DEAL'}
                    ],
                    'down': [
                        {'number': 1, 'direction': 'D', 'row': 0, 'col': 0, 'clue': 'Bede', 'answer': 'ADAM'},
                        {'number': 2, 'direction': 'D', 'row': 0, 'col': 1, 'clue': 'Uganda people', 'answer': 'HIMA'},
                        {'number': 3, 'direction': 'D', 'row': 0, 'col': 2, 'clue': 'Smooth', 'answer': 'EVEN'},
                        {'number': 4, 'direction': 'D', 'row': 0, 'col': 3, 'clue': 'Orange', 'answer': 'MANDARIN'},
                        {'number': 5, 'direction': 'D', 'row': 0, 'col': 5, 'clue': 'Restless ones', 'answer': 'NOMADS'},
                        {'number': 6, 'direction': 'D', 'row': 0, 'col': 6, 'clue': "On one's toes", 'answer': 'AWAKE'},
                        {'number': 7, 'direction': 'D', 'row': 0, 'col': 7, 'clue': 'Hawaiian goose', 'answer': 'NENE'},
                        {'number': 8, 'direction': 'D', 'row': 0, 'col': 8, 'clue': '"___ was saying..."', 'answer': 'ASI'},
                        {'number': 9, 'direction': 'D', 'row': 0, 'col': 10, 'clue': 'Elk or Rotarian', 'answer': 'CLUBMAN'},
                        {'number': 10, 'direction': 'D', 'row': 0, 'col': 11, 'clue': 'Lasso', 'answer': 'LARIAT'},
                        {'number': 11, 'direction': 'D', 'row': 0, 'col': 12, 'clue': 'Roman poet', 'answer': 'OVID'},
                        {'number': 12, 'direction': 'D', 'row': 0, 'col': 13, 'clue': 'Flower holder', 'answer': 'VASE'},
                        {'number': 13, 'direction': 'D', 'row': 0, 'col': 14, 'clue': 'Superlative ending', 'answer': 'EST'},
                        {'number': 19, 'direction': 'D', 'row': 2, 'col': 4, 'clue': 'Actor Michael and family', 'answer': 'CAINES'},
                        {'number': 21, 'direction': 'D', 'row': 3, 'col': 8, 'clue': 'Nothing, in Paris', 'answer': 'RIEN'},
                        {'number': 24, 'direction': 'D', 'row': 4, 'col': 9, 'clue': 'Destroys', 'answer': 'RAZES'},
                        {'number': 25, 'direction': 'D', 'row': 5, 'col': 2, 'clue': 'Treaty org.', 'answer': 'SEATO'},
                        {'number': 26, 'direction': 'D', 'row': 5, 'col': 3, 'clue': 'Assume', 'answer': 'POSIT'},
                        {'number': 27, 'direction': 'D', 'row': 5, 'col': 4, 'clue': 'Black-ink item', 'answer': 'ASSET'},
                        {'number': 28, 'direction': 'D', 'row': 5, 'col': 9, 'clue': 'S.A. trees', 'answer': 'MORAS'},
                        {'number': 29, 'direction': 'D', 'row': 5, 'col': 10, 'clue': 'Run off', 'answer': 'ELOPE'},
                        {'number': 30, 'direction': 'D', 'row': 5, 'col': 11, 'clue': 'Agog', 'answer': 'EAGER'},
                        {'number': 31, 'direction': 'D', 'row': 5, 'col': 12, 'clue': 'Stone slab', 'answer': 'STELA'},
                        {'number': 33, 'direction': 'D', 'row': 6, 'col': 8, 'clue': 'Football units', 'answer': 'DOWNS'},
                        {'number': 36, 'direction': 'D', 'row': 7, 'col': 8, 'clue': 'Flower part', 'answer': 'STAMEN'},
                        {'number': 37, 'direction': 'D', 'row': 7, 'col': 13, 'clue': 'Called for', 'answer': 'DEMANDED'},
                        {'number': 39, 'direction': 'D', 'row': 8, 'col': 6, 'clue': 'Rival', 'answer': 'EMULATE'},
                        {'number': 40, 'direction': 'D', 'row': 8, 'col': 12, 'clue': '___ avis', 'answer': 'RARA'},
                        {'number': 42, 'direction': 'D', 'row': 9, 'col': 10, 'clue': 'Passé', 'answer': 'OLDHAT'},
                        {'number': 43, 'direction': 'D', 'row': 9, 'col': 11, 'clue': 'N.J. city', 'answer': 'CAMDEN'},
                        {'number': 45, 'direction': 'D', 'row': 10, 'col': 10, 'clue': 'Shoe material', 'answer': 'SUEDE'},
                        {'number': 46, 'direction': 'D', 'row': 11, 'col': 4, 'clue': 'Pasternak heroine', 'answer': 'LARA'},
                        {'number': 47, 'direction': 'D', 'row': 11, 'col': 5, 'clue': 'Soon', 'answer': 'ANON'},
                        {'number': 48, 'direction': 'D', 'row': 11, 'col': 10, 'clue': 'Stale', 'answer': 'FLAT'},
                        {'number': 49, 'direction': 'D', 'row': 11, 'col': 11, 'clue': 'Porter', 'answer': 'COLE'},
                        {'number': 50, 'direction': 'D', 'row': 11, 'col': 12, 'clue': 'Oahu dance', 'answer': 'HULA'},
                        {'number': 51, 'direction': 'D', 'row': 11, 'col': 13, 'clue': 'Russian range', 'answer': 'URAL'},
                        {'number': 52, 'direction': 'D', 'row': 12, 'col': 0, 'clue': "Labor's counterpart: Abbr.", 'answer': 'MGT'},
                        {'number': 53, 'direction': 'D', 'row': 12, 'col': 1, 'clue': 'Dental degree', 'answer': 'DDS'}
                    ]
                }),
                'solution_key': json.dumps([
                    ['#','A','H','E','#','N','A','N','#','#','C','L','O','V','#'],
                    ['D','I','V','A','#','O','W','E','S','#','L','A','V','A','S'],
                    ['A','M','E','N','#','M','A','N','I','C','U','R','I','S','T'],
                    ['M','A','N','D','R','A','K','E','#','A','B','I','D','E','#'],
                    ['#','#','#','#','A','I','D','E','#','R','I','M','A','#','#'],
                    ['#','#','S','P','A','R','E','S','#','M','A','N','A','T','E'],
                    ['E','S','E','O','S','I','N','#','D','O','Z','E','N','#','L'],
                    ['A','T','A','S','S','N','#','#','S','O','R','E','#','D','O'],
                    ['G','E','T','I','E','#','E','T','W','A','S','#','R','E','P'],
                    ['E','L','O','T','T','O','M','A','N','S','#','C','A','M','E'],
                    ['R','A','#','#','#','L','U','M','S','#','S','A','R','A','#'],
                    ['#','#','#','#','L','A','D','L','E','#','F','U','M','A','N'],
                    ['C','H','U','M','A','N','H','A','N','D','L','E','D','#','D'],
                    ['O','U','R','G','R','O','A','T','#','D','A','D','E','#','E'],
                    ['L','L','A','T','A','N','T','E','#','S','T','E','N','#','D']
                ])
            }
        ]
        
        for puzzle in sample_puzzles:
            cursor.execute("""
                INSERT INTO puzzles (title, tags, grid, clues, solution_key, author_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (puzzle['title'], puzzle['tags'], puzzle['grid'], 
                  puzzle['clues'], puzzle['solution_key'], test_user_id))
            print(f"Added sample puzzle: {puzzle['title']}")
        
        # Commit changes
        conn.commit()
        print("Database initialization complete")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        traceback.print_exc()  # Print full error traceback
        if 'conn' in locals():
            conn.rollback()
    except Exception as e:
        print(f"Other error: {e}")
        traceback.print_exc()  # Print full error traceback
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    init_db() 