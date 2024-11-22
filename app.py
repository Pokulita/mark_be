import datetime
from flask import Flask, jsonify, request
import os
import psycopg2
import bcrypt
import jwt
from flask_cors import CORS


app = Flask(__name__)

# Apply CORS globally, allowing requests from your frontend's origin (localhost:3000)
CORS(app, resources={r"/*": {"origins": "https://mark-fe.onrender.com"}})

def get_db_connection():
    connection = psycopg2.connect(
        dbname="mymark",
        user="pokulita",
        password="99ZJSsxtv8DA38u0bCHmEvjXK9MAZErf",
        host="dpg-ct07htm8ii6s73fiimc0-a.frankfurt-postgres.render.com",
        port="5432"
    )
    return connection

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')



    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()

    if result[0] > 0:
        return jsonify({"success": False, "message": "Email is already in use."}), 400

    cursor.execute(
        "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
        (username, email, hashed_password.decode('utf-8'))
    )

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM courses")
    courses = cursor.fetchall()

    print(courses)
    print(user_id)
    for course in courses:
        course_id = course[0]
        cursor.execute(
            "INSERT INTO student_courses (user_id, course_id, pass_status) VALUES (%s, %s, 0)",
            (user_id, course_id)
        )
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"success": True, "message": "Registration successful!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')



    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, password, username FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()

    if result is None:
        return jsonify({"success": False, "message": "Email not found."}), 400

    # Check if the email and password combination is correct

    user_id,stored_password, username = result  # Unpack the result

    # Check if the password matches
    if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        return jsonify({"success": False, "message": "Password incorrect."}), 400

    # Generate JWT token (set an expiration time if necessary)
    payload = {
        'id':user_id,
        'username': username,
        'email': email
    }
    secret_key = '12'
    print(user_id, payload, secret_key)
    # You need to have a secret key in your app's config
    token = jwt.encode(payload,secret_key , algorithm='HS256')


    cursor.close()
    connection.close()
    return jsonify({"success": True, "token": token}), 200

@app.route('/course', methods=['GET'])
def get_user_courses():
    tuser_id = request.args.get('user_id')
    connection = get_db_connection()
    cursor = connection.cursor()

    print(tuser_id)
    cursor.execute("SELECT * FROM courses")  # Adjust with your actual table and columns
    result = cursor.fetchall()

    # Convert the result to a list of dictionaries
    courses = [{"id": row[0], "name": row[1], "ects": row[2]} for row in result]

    cursor.close()
    connection.close()

    return jsonify(courses)


@app.route('/courses', methods=['GET'])
def get_user_courses():
    tuser_id = request.args.get('user_id')
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT c.id, c.name, c.ects, sc.pass_status 
        FROM student_courses sc
        JOIN courses c ON c.id = sc.course_id
        WHERE sc.user_id = %s
    """, (tuser_id,))# Adjust with your actual table and columns
    result = cursor.fetchall()

    # Convert the result to a list of dictionaries
    courses = [{"id": row[0], "name": row[1], "ects": row[2],"passed" :row[3]} for row in result]

    cursor.close()
    connection.close()

    return jsonify(courses)

@app.route('/mark_course_passed', methods=['POST'])
def mark_course_passed():
    data = request.get_json()
    user_id = data.get('user_id')
    course_id = data.get('course_id')

    if not user_id or not course_id:
        return jsonify({"success": False, "message": "User ID and Course ID are required"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()


    # Update the 'passed' status of the course
    cursor.execute("""
        UPDATE student_courses
        SET pass_status = 1
        WHERE user_id = %s AND course_id = %s
    """, (user_id, course_id))
    connection.commit()
    return jsonify({"success": True, "message": "Course marked as passed"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))