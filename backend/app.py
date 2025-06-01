from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import jwt
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'dbms')  # Updated MySQL password
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'quiz_system_3')  # Updated database name
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Initialize MySQL
mysql = MySQL(app)

# Test database connection
@app.route('/api/test-db')
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        return jsonify({'message': 'Database connection successful!'}), 200
    except Exception as e:
        return jsonify({'error': 'Database connection failed', 'message': str(e)}), 500

# Error handler for database connection issues
@app.errorhandler(500)
def handle_database_error(e):
    return jsonify({'error': 'Database error occurred', 'message': str(e)}), 500

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return jsonify({'error': 'Not found'}), 404

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# User Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    cursor = mysql.connection.cursor()
    
    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE email = %s', (data['email'],))
    if cursor.fetchone():
        return jsonify({'message': 'User already exists!'}), 409
    
    hashed_password = generate_password_hash(data['password'])
    cursor.execute('INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)',
                  (data['username'], data['email'], hashed_password, 'user'))
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    cursor = mysql.connection.cursor()
    
    cursor.execute('SELECT * FROM users WHERE email = %s', (data['email'],))
    user = cursor.fetchone()
    cursor.close()
    
    if user and check_password_hash(user[3], data['password']):
        token = jwt.encode({
            'user_id': user[0],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'token': token,
            'user_id': user[0],
            'username': user[1],
            'role': user[4]
        })
    
    return jsonify({'message': 'Invalid credentials!'}), 401

# Quiz Routes
@app.route('/api/categories', methods=['GET'])
def get_categories():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM categories')
    categories = cursor.fetchall()
    cursor.close()
    
    return jsonify([{
        'id': cat[0],
        'name': cat[1],
        'description': cat[2]
    } for cat in categories])

@app.route('/api/quiz/<int:category_id>', methods=['GET'])
@token_required
def get_quiz(current_user, category_id):
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT q.*, GROUP_CONCAT(o.option_text) as options, GROUP_CONCAT(o.is_correct) as correct_options
        FROM questions q
        LEFT JOIN options o ON q.id = o.question_id
        WHERE q.category_id = %s
        GROUP BY q.id
        ORDER BY RAND()
        LIMIT 10
    ''', (category_id,))
    
    questions = cursor.fetchall()
    cursor.close()
    
    formatted_questions = []
    for q in questions:
        options = q[6].split(',')
        correct_options = q[7].split(',')
        formatted_questions.append({
            'id': q[0],
            'question': q[2],
            'points': q[3],
            'difficulty': q[4],
            'options': options,
            'correct_options': [i for i, x in enumerate(correct_options) if x == '1']
        })
    
    return jsonify(formatted_questions)

@app.route('/api/submit-quiz', methods=['POST'])
@token_required
def submit_quiz(current_user):
    data = request.json
    cursor = mysql.connection.cursor()
    
    # Calculate score
    score = 0
    total_time = data['total_time']
    correct_answers = 0
    
    for answer in data['answers']:
        cursor.execute('SELECT points FROM questions WHERE id = %s', (answer['question_id'],))
        question = cursor.fetchone()
        if answer['is_correct']:
            score += question[0]
            correct_answers += 1
    
    # Save quiz attempt
    cursor.execute('''
        INSERT INTO quiz_attempts 
        (user_id, category_id, score, total_time, correct_answers, total_questions)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (current_user, data['category_id'], score, total_time, correct_answers, len(data['answers'])))
    
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({
        'score': score,
        'correct_answers': correct_answers,
        'total_questions': len(data['answers']),
        'time_taken': total_time
    })

@app.route('/api/leaderboard/<int:category_id>', methods=['GET'])
def get_leaderboard(category_id):
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT u.username, qa.score, qa.total_time
        FROM quiz_attempts qa
        JOIN users u ON qa.user_id = u.id
        WHERE qa.category_id = %s
        ORDER BY qa.score DESC, qa.total_time ASC
        LIMIT 10
    ''', (category_id,))
    
    leaderboard = cursor.fetchall()
    cursor.close()
    
    return jsonify([{
        'username': entry[0],
        'score': entry[1],
        'time': entry[2]
    } for entry in leaderboard])

# Admin Routes
@app.route('/api/admin/questions', methods=['POST'])
@token_required
def add_question(current_user):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT role FROM users WHERE id = %s', (current_user,))
    user_role = cursor.fetchone()[0]
    
    if user_role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.json
    cursor.execute('''
        INSERT INTO questions (category_id, question_text, points, difficulty)
        VALUES (%s, %s, %s, %s)
    ''', (data['category_id'], data['question'], data['points'], data['difficulty']))
    
    question_id = cursor.lastrowid
    
    for option in data['options']:
        cursor.execute('''
            INSERT INTO options (question_id, option_text, is_correct)
            VALUES (%s, %s, %s)
        ''', (question_id, option['text'], option['is_correct']))
    
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({'message': 'Question added successfully!'}), 201

if __name__ == '__main__':
    app.run(debug=True) 