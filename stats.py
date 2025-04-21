from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_stats(user_id):
    db = get_db()
    
    stats = db.execute('''
        SELECT 
            COUNT(DISTINCT puzzle_id) as puzzles_solved,
            AVG(completion_time) as average_solve_time
        FROM solved_puzzles
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    return jsonify({
        'puzzles_solved': stats['puzzles_solved'],
        'average_solve_time': stats['average_solve_time']
    })

@stats_bp.route('/puzzles', methods=['GET'])
@jwt_required()
def get_puzzle_stats():
    db = get_db()
    
    stats = db.execute('''
        SELECT 
            p.title,
            p.difficulty,
            COUNT(sp.puzzle_id) as times_solved,
            AVG(sp.completion_time) as avg_time
        FROM puzzles p
        LEFT JOIN solved_puzzles sp ON p.id = sp.puzzle_id
        GROUP BY p.id
        ORDER BY times_solved DESC
    ''').fetchall()
    
    return jsonify([dict(row) for row in stats])