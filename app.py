from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lms.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    assignments = db.relationship('Assignment', backref='student', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    lecture_link = db.Column(db.String(200))
    assignments = db.relationship('Assignment', backref='course', lazy=True)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    submission = db.Column(db.String(200))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    courses = Course.query.all()
    return render_template('dashboard.html', courses=courses)

@app.route('/course/<int:course_id>')
@login_required
def course(course_id):
    course = Course.query.get_or_404(course_id)
    assignments = Assignment.query.filter_by(course_id=course_id).all()
    return render_template('course.html', course=course, assignments=assignments)

@app.route('/submit_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    if 'file' not in request.files:
        flash('No file submitted')
        return redirect(url_for('course', course_id=assignment.course_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('course', course_id=assignment.course_id))
    
    # Save file logic here
    flash('Assignment submitted successfully')
    return redirect(url_for('course', course_id=assignment.course_id))

# Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    courses = Course.query.all()
    assignments = Assignment.query.all()
    return render_template('admin/dashboard.html', users=users, courses=courses, assignments=assignments)

@app.route('/admin/course/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_course():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        lecture_link = request.form.get('lecture_link')
        
        course = Course(title=title, description=description, lecture_link=lecture_link)
        db.session.add(course)
        db.session.commit()
        
        flash('Course added successfully!')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_course.html')

@app.route('/admin/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.lecture_link = request.form.get('lecture_link')
        
        db.session.commit()
        flash('Course updated successfully!')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_course.html', course=course)

@app.route('/admin/course/<int:course_id>/delete')
@login_required
@admin_required
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/assignment/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_assignment():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%dT%H:%M')
        course_id = request.form.get('course_id')
        
        assignment = Assignment(
            title=title,
            description=description,
            due_date=due_date,
            course_id=course_id
        )
        db.session.add(assignment)
        db.session.commit()
        
        flash('Assignment added successfully!')
        return redirect(url_for('admin_dashboard'))
    
    courses = Course.query.all()
    return render_template('admin/add_assignment.html', courses=courses)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>/toggle-admin')
@login_required
@admin_required
def admin_toggle_user_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot modify your own admin status!')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'Admin status updated for {user.username}')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
