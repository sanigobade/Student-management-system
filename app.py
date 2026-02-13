from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'student_admin_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/student_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    students = db.relationship('Student', backref='admin', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Current') 
    total_fees = db.Column(db.Float, default=0.0)
    due_fees = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

# --- Routes ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash("Email already registered!")
        else:
            db.session.add(User(email=email, password=password))
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'], password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            session['email'] = user.email
            return redirect(url_for('dashboard'))
        flash("Invalid Credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    uid = session['user_id']
    stats = {
        "total": Student.query.filter_by(user_id=uid).count(),
        "passout": Student.query.filter_by(user_id=uid, status='Passout').count(),
        "current": Student.query.filter_by(user_id=uid, status='Current').count(),
        "fees": db.session.query(func.sum(Student.total_fees)).filter(Student.user_id==uid).scalar() or 0,
        "due": db.session.query(func.sum(Student.due_fees)).filter(Student.user_id==uid).scalar() or 0
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        new_s = Student(
            name=request.form['name'], phone=request.form['phone'],
            status=request.form['status'], total_fees=float(request.form['total_fees']),
            due_fees=float(request.form['due_fees']), user_id=session['user_id']
        )
        db.session.add(new_s)
        db.session.commit()
        return redirect(url_for('view_students'))
    return render_template('add_student.html')

@app.route('/view_students')
def view_students():
    if 'user_id' not in session: return redirect(url_for('login'))
    students = Student.query.filter_by(user_id=session['user_id']).all()
    return render_template('view_students.html', students=students)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    s = Student.query.get(id)
    if request.method == 'POST':
        s.name, s.phone, s.status = request.form['name'], request.form['phone'], request.form['status']
        s.total_fees, s.due_fees = float(request.form['total_fees']), float(request.form['due_fees'])
        db.session.commit()
        return redirect(url_for('view_students'))
    return render_template('edit_student.html', s=s)

@app.route('/delete/<int:id>')
def delete_student(id):
    db.session.delete(Student.query.get(id))
    db.session.commit()
    return redirect(url_for('view_students'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)