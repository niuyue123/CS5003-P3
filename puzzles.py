from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db
import json

puzzles_bp = Blueprint('puzzles', __name__)

@puzzles_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_puzzles():
    db = get_db()
    puzzles = db.execute('''
        SELECT p.*, u.username as creator_name,
               COUNT(sp.puzzle_id) as times_solved
        FROM puzzles p
        JOIN users u ON p.created_by = u.id
        LEFT JOIN solved_puzzles sp ON p.id = sp.puzzle_id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    return jsonify([dict(p) for p in puzzles])

@puzzles_bp.route('/<int:puzzle_id>', methods=['GET'])
@jwt_required()
def get_puzzle(puzzle_id):
    db = get_db()
    puzzle = db.execute(
        'SELECT * FROM puzzles WHERE id = ?', (puzzle_id,)
    ).fetchone()
    
    if not puzzle:
        return jsonify({'error': 'Puzzle not found'}), 404
        
    return jsonify(dict(puzzle))

@puzzles_bp.route('/', methods=['POST'])
@jwt_required()
def create_puzzle():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    required_fields = ['title', 'grid', 'clues', 'solution', 'difficulty']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
        
    db = get_db()
    try:
        cursor = db.execute('''
            INSERT INTO puzzles (title, grid, clues, solution, difficulty, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['title'],
            json.dumps(data['grid']),
            json.dumps(data['clues']),
            json.dumps(data['solution']),
            data['difficulty'],
            user_id
        ))
        db.commit()
        return jsonify({'id': cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@puzzles_bp.route('/<int:puzzle_id>/validate', methods=['POST'])
@jwt_required()
def validate_solution(puzzle_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    
    if 'solution' not in data or 'time' not in data:
        return jsonify({'error': 'Missing solution or time'}), 400
        
    db = get_db()
    puzzle = db.execute(
        'SELECT solution FROM puzzles WHERE id = ?', (puzzle_id,)
    ).fetchone()
    
    if not puzzle:
        return jsonify({'error': 'Puzzle not found'}), 404
        
    is_correct = data['solution'] == json.loads(puzzle['solution'])
    
    if is_correct:
        db.execute('''
            INSERT OR REPLACE INTO solved_puzzles (user_id, puzzle_id, completion_time)
            VALUES (?, ?, ?)
        ''', (user_id, puzzle_id, data['time']))
        db.commit()
        
    return jsonify({'correct': is_correct})