from flask import Flask, jsonify
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user
import re


user = 'root'
password = 'Marah@2001'
host = 'localhost'
port = 3307
database = 'test'

def get_connection():
    password_encoded = quote_plus(password)
    return create_engine(
        f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/{database}"
    )

app = Flask(__name__)

engine = get_connection()
Session = sessionmaker(bind=engine)
Base = declarative_base()

app.config["SECRET_KEY"] = "MarahD"


class Auth(Base):
    __tablename__ = 'auth'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Make id auto-incrementing
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    age = Column(Integer)
    email = Column(String(100))

class Instructor(Base):
    __tablename__ = 'instructors'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    department = Column(String(100))

    courses = relationship("Course", back_populates="instructor")

class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    instructor_id = Column(Integer, ForeignKey('instructors.id'))
    credits = Column(Integer)

    instructor = relationship("Instructor", back_populates="courses")


#######################################################################################################

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
# def load_user(username):
#     user = auth.query.filter_by(username=username).first()

    # return user


#################### AUTH APIs ####################################
@app.route('/signup', methods=["POST"])
def register():
    session = Session()

    data = request.json
    username = data['username']
    password = data['password']
    confirm = data['confirm']
    if len(username) < 5: # check length of username
        return jsonify({'error': 'username should be at least 5 characters long'})

    elif password != confirm: # check if passwrod equal confirm
        return jsonify({'error': 'password and confirm do not match'})

    # check password strength
    elif len(password) < 8 or re.search("[a-z]", password) is None or re.search("[A-Z]", password) is None or re.search(
            "[0-9]", password) is None or re.search("[!@#$%^&*()_+=]", password) is None:
        return jsonify({'error': 'password is not strong, it should be at least 8 characters and contain small letters, capital letters, numbers, and special characters'})

    elif session.query(Auth).filter_by(username = username).first() is not None:
        return jsonify({'error': 'username already exists, choose other one'})

    else:
        hashed_password = generate_password_hash(password).decode('utf-8')
        user = Auth(username=username, password=hashed_password)
        session.add(user)
        session.commit()
        session.close()
        return jsonify({'message': 'success, Welcome oo our system' + username + '!'}), 200


@app.route('/login', methods=['POST'])
def login():
    session = Session()

    data = request.json
    username = data['username']
    password = data['password']
    print(username + password)
    user = session.query(Auth).filter_by(username = username).first()
    print(user)
    if user is not None:
        if check_password_hash(user.password, password) is True:
            return jsonify({'message': 'Welcome again ' + username + '!'}), 200
        else:
            return jsonify({'error': 'username or password is incorrect'}), 404


    else:
        return jsonify({'error': 'username or password is incorrect'}), 404





############################################################################################################
# API to get all students
@app.route('/students', methods=['GET'])
def get_students():
    session = Session()
    students = session.query(Student).all()
    session.close()
    return jsonify([{'id': student.id, 'name': student.name, 'age': student.age, 'email': student.email} for student in students])


#API to get all instructors
@app.route('/instructors', methods=['GET'])
def get_instructors():
    session = Session()
    instructors = session.query(Instructor).all()
    session.close()
    return jsonify([{
        'id': instructor.id,
        'name': instructor.name,
        'email': instructor.email,
        'department': instructor.department
    } for instructor in instructors])


# API to get all courses
@app.route('/courses', methods=['GET'])
def get_courses():
    session = Session()
    courses = session.query(Course).all()
    session.close()
    return jsonify([{
        'id': course.id,
        'name': course.name,
        'instructor_id': course.instructor_id,
        'credits': course.credits
    } for course in courses])



from flask import request

# API to create a new student
@app.route('/newStudent', methods=['POST'])
def create_student():
    data = request.json
    id = data.get('id')
    name = data.get('name')
    age = data.get('age')
    email = data.get('email')

    if not id or not name or not age or not email:
        return jsonify({'error': 'Incomplete data'}), 400

    new_student = Student(id=id, name=name, age=age, email=email)

    session = Session()
    session.add(new_student)
    session.commit()
    session.close()

    return jsonify({'message': 'new student added successfully'}), 200

# API to create a new instructor
@app.route('/newInstructor', methods=['POST'])
def create_instructor():
    data = request.json
    id=data.get('id')
    name = data.get('name')
    email = data.get('email')
    department = data.get('department')

    if not id or not name or not email or not department:
        return jsonify({'error': 'Incomplete data '}), 400

    new_instructor = Instructor(id=id, name=name, email=email, department=department)

    session = Session()
    session.add(new_instructor)
    session.commit()
    session.close()

    return jsonify({'message': 'Instructor added successfully'}), 200


# API to create a new course
@app.route('/newCourse', methods=['POST'])
def create_course():
    data = request.json
    id = data.get('id')
    name = data.get('name')
    instructor_id = data.get('instructor_id')
    credits = data.get('credits')
    session = Session()

    if not id or not name or not instructor_id or not credits:
        return jsonify({'error': 'Incomplete data '}), 400

    instructor = session.query(Instructor).filter_by(id=instructor_id).first()
    if not instructor:
        return jsonify({'error': 'Instructor with ID {} not found'.format(instructor_id)}), 404

    new_course = Course(id=id, name=name, instructor_id=instructor_id, credits=credits)

    # Add the new course to the database
    session.add(new_course)
    session.commit()

    return jsonify({'message': 'Course added successfully'}), 200


# API to get all courses of an instructor by name
@app.route('/coursesByInstructor', methods=['GET'])
def get_courses_instructor():
    data = request.json
    instructor_name = data.get('name')
    session = Session()
    if not instructor_name:
        return jsonify({'error': 'enter instructor name'}), 400

    instructor = session.query(Instructor).filter_by(name=instructor_name).first()

    if not instructor:
        return jsonify({'error': 'Instructor not exist'}), 404

    # Get all courses taught by the instructor
    courses = session.query(Course).filter_by(instructor_id=instructor.id).all()

    # Prepare the response data
    courses_data = [{'id': course.id, 'name': course.name, 'credits': course.credits} for course in courses]

    return jsonify(courses_data), 200


# API to delete a student by ID
@app.route('/deleteStudent/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    session = Session()
    student = session.query(Student).filter_by(id=student_id).first()

    if not student:
        return jsonify({'error': 'Student not found'}), 404

    # Delete the student from the database
    session.delete(student)
    session.commit()

    return jsonify({'message': 'Student deleted successfully'}), 200


# API to update student email by ID
@app.route('/updateEmail', methods=['PUT'])
def update_student_email():
    session = Session()
    data = request.json
    student_id = data.get('id')
    email = data.get('newEmail')
    student = session.query(Student).filter_by(id=student_id).first()

    if not student:
        return jsonify({'error': 'Student not found'}), 404

    if not email:
        return jsonify({'error': 'Email not provided in the body'}), 400

    student.email = email

    session.commit()

    return jsonify({'message': 'Student email updated successfully'}), 200

if __name__ == '__main__':
    try:
        print(f"Connection to the {host} for user {user} created successfully.")
        app.run(debug=True)
    except Exception as ex:
        print("Connection could not be made due to the following error: \n", ex)
