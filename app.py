# Extended Flask App for MedTrack
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import uuid
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# ---------- Logging Setup ----------
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ---------- In-Memory Storage ----------
users = {}                 # userid: {...}
appointments_dict = {}     # appointment_id: {...}
diagnoses = []             # list of diagnosis dicts
notifications = []         # list of notification dicts


# ----- temp users -----

users = {
    'doc1': {
        'name': 'Alice Smith',
        'email': 'cafilep241@apklamp.com',
        'password': generate_password_hash('111'),
        'role': 'doctor',
        'extra': {
            'specialization': 'Cardiology',
            'experience': '10 years',
            'age': None,
            'gender': 'Female',
            'address': '123 Heart Street',
            'medical_history': None
        }
    },
    'doc2': {
        'name': 'Bob Johnson',
        'email': 'monster73372@gmail.com',
        'password': generate_password_hash('111'),
        'role': 'doctor',
        'extra': {
            'specialization': 'Dermatology',
            'experience': '8 years',
            'age': None,
            'gender': 'Male',
            'address': '456 Skin Ave',
            'medical_history': None
        }
    },
    'pat1': {
        'name': 'Charlie Brown',
        'email': 'fatoker454@hosliy.com',
        'password': generate_password_hash('111'),
        'role': 'patient',
        'extra': {
            'age': 30,
            'gender': 'Male',
            'address': '789 Peace Lane',
            'medical_history': 'Allergy to penicillin',
            'specialization': None,
            'experience': None
        }
    },
    'pat2': {
        'name': 'Diana Prince',
        'email': 'vosaro3888@btcours.com',
        'password': generate_password_hash('111'),
        'role': 'patient',
        'extra': {
            'age': 28,
            'gender': 'Female',
            'address': '321 Justice Blvd',
            'medical_history': 'Asthma',
            'specialization': None,
            'experience': None
        }
    }
}

# -----temp appointmets ------

appointments_dict = {
    # ------------------ Appointments for doc1 (Cardiologist) ------------------
    'appt1': {
        'appointment_id': 'appt1',
        'doctor_id': 'doc1',
        'patient_id': 'pat1',
        'date': date.today().strftime('%Y-%m-%d'),
        'time': '09:00 AM',
        'symptoms': 'Chest pain',
        'status': 'Pending'
    },
    'appt2': {
        'appointment_id': 'appt2',
        'doctor_id': 'doc1',
        'patient_id': 'pat2',
        'date': date.today().strftime('%Y-%m-%d'),
        'time': '10:00 AM',
        'symptoms': 'Fatigue and dizziness',
        'status': 'Pending'
    },
    'appt3': {
        'appointment_id': 'appt3',
        'doctor_id': 'doc1',
        'patient_id': 'pat1',
        'date': date.today().strftime('%Y-%m-%d'),
        'time': '11:30 AM',
        'symptoms': 'Shortness of breath',
        'status': 'Pending'
    },
    'appt4': {
        'appointment_id': 'appt4',
        'doctor_id': 'doc1',
        'patient_id': 'pat2',
        'date': date.today().strftime('%Y-%m-%d'),
        'time': '01:00 PM',
        'symptoms': 'Heart palpitations',
        'status': 'Pending'
    },

    # ------------------ Appointments for doc2 (Dermatologist) ------------------
    'appt5': {
        'appointment_id': 'appt5',
        'doctor_id': 'doc2',
        'patient_id': 'pat1',
        'date': date.today().strftime('%Y-%m-%d'),
        'time': '02:00 PM',
        'symptoms': 'Skin rash',
        'status': 'Pending'
    },
    'appt6': {
        'appointment_id': 'appt6',
        'doctor_id': 'doc2',
        'patient_id': 'pat2',
        'date': date.today().strftime('%Y-%m-%d'),
        'time': '03:00 PM',
        'symptoms': 'Allergic reaction',
        'status': 'Pending'
    },
    'appt7': {
        'appointment_id': 'appt7',
        'doctor_id': 'doc2',
        'patient_id': 'pat1',
        'date': date.today().strftime('%Y-%m-%d'),
        'time': '04:15 PM',
        'symptoms': 'Acne',
        'status': 'Pending'
    },
    'appt8': {
        'appointment_id': 'appt8',
        'doctor_id': 'doc2',
        'patient_id': 'pat2',
        'date': date.today().strftime('%Y-%m-%d'),
        'time': '05:30 PM',
        'symptoms': 'Skin dryness',
        'status': 'Pending'
    }
}



# ---------- Utility: Role Required Decorator ----------
def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'userid' not in session or session.get('role') != role:
                flash("Unauthorized access.", "danger")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ---------- Helper: Send Email ----------
def send_email(to_email, subject, message):
    from_email = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'html'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.send_message(msg)
        logging.info(f"Email sent to {to_email}")
    except Exception as e:
        logging.error(f"Email failed to send: {e}")

# ---------- Routes ----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        generated_id = f"{request.form['role'][:3].upper()}{str(uuid.uuid4())[:5]}"

        if any(user['email'] == request.form['email'] for user in users.values()):
            flash("User with this email already exists.")
            return redirect(url_for('register'))

        if request.form['password'] != request.form['confirm_password']:
            flash("Passwords do not match.")
            return redirect(url_for('register'))

        users[generated_id] = {
            'name': request.form['name'],
            'email': request.form['email'],
            'password': generate_password_hash(request.form['password']),
            'role': request.form['role'],
            'extra': {
                'age': request.form.get('age'),
                'gender': request.form.get('gender'),
                'address': request.form.get('address'),
                'specialization': request.form.get('specialization'),
                'experience': request.form.get('experience'),
                'medical_history': request.form.get('medical_history')
            }
        }

        logging.info(f"User registered: {generated_id}")
        flash(f"Registration successful! Your User ID is: {generated_id}")
        return redirect(url_for('login'))

    return render_template('register.html')


# Login validation
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        selected_role = request.form['role']  # Get selected role from hidden input

        user_id = None
        for uid, user in users.items():
            if user['email'] == email:
                user_id = uid
                break

        # Validate credentials
        if user_id and check_password_hash(users[user_id]['password'], password):
            actual_role = users[user_id]['role']
            if actual_role != selected_role:
                flash("Role mismatch! Please select the correct role for your account.")
                logging.warning(f"Role mismatch for email: {email} (selected: {selected_role}, actual: {actual_role})")
                return redirect(url_for('login'))

            # Set session and redirect
            session['userid'] = user_id
            session['role'] = actual_role
            logging.info(f"Login success: {user_id} as {actual_role}")
            return redirect(url_for(f"{actual_role}_dashboard"))
        else:
            flash("Invalid credentials.")
            logging.warning(f"Login failed for email: {email}")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ---------- Patient Dashboard ----------
@app.route('/patient_dashboard')
@role_required('patient')
def patient_dashboard():
    user_id = session['userid']
    user = users[user_id]

    # Get all appointments for this user
    user_appointments = [a for a in appointments_dict.values() if a['patient_id'] == user_id]

    # Get search query
    search_query = request.args.get('search', '').strip().lower()

    # Filter appointments based on search query
    if search_query:
        filtered_appointments = []
        for a in user_appointments:
            doctor_name = users[a['doctor_id']]['name'].lower()
            status = a['status'].lower()
            if search_query in doctor_name or search_query in status:
                filtered_appointments.append(a)
        user_appointments = filtered_appointments

    # Stats after filtering
    pending = sum(1 for a in user_appointments if a['status'] == 'Pending')
    completed = sum(1 for a in user_appointments if a['status'] == 'Completed')
    total = len(user_appointments)

    # Doctor list for Available Doctors tab
    doctor_list = {uid: info for uid, info in users.items() if info['role'] == 'doctor'}

    return render_template(
        'patient_dashboard.html',
        user=user,
        appointments=user_appointments,
        pending=pending,
        completed=completed,
        total=total,
        doctor_list=doctor_list,
        users=users
    )

# ---------- Doctor Dashboard ----------
@app.route('/doctor_dashboard')
@role_required('doctor')
def doctor_dashboard():
    user_id = session['userid']
    user = users[user_id]

    # Get all appointments for this doctor
    user_appointments = [a for a in appointments_dict.values() if a['doctor_id'] == user_id]

    # Get search query (if any)
    search_query = request.args.get('search', '').strip().lower()

    # Apply search filter
    if search_query:
        user_appointments = [
            a for a in user_appointments
            if search_query in users[a['patient_id']]['name'].lower()
        ]

    # Stats after filtering
    pending = sum(1 for a in user_appointments if a['status'] == 'Pending')
    completed = sum(1 for a in user_appointments if a['status'] == 'Completed')
    total = len(user_appointments)

    return render_template(
        'doctor_dashboard.html',
        user=user,
        appointments=user_appointments,
        pending=pending,
        completed=completed,
        total=total,
        users=users
    )


# ---------- Book Appointment ----------
@app.route('/book_appointment', methods=['GET', 'POST'])
@role_required('patient')
def book_appointment():
    if request.method == 'POST':
        appointment_id = str(uuid.uuid4())[:8]
        appointment = {
            'appointment_id': appointment_id,
            'patient_id': session['userid'],
            'doctor_id': request.form['doctor_id'],
            'date': request.form['appointment_date'],
            'time': request.form['appointment_time'],
            'symptoms': request.form['symptoms'],
            'status': 'Pending',
            'created_at': datetime.now()
        }

        appointments_dict[appointment_id] = appointment

        notifications.append({
            'id': str(uuid.uuid4()),
            'user_id': appointment['doctor_id'],
            'message': f"New appointment booked by {users[appointment['patient_id']]['name']}",
            'timestamp': datetime.now()
        })

        patient_email = users[appointment['patient_id']]['email']
        send_email(patient_email, "Appointment Confirmation",
                   f"<h3>Appointment Booked</h3><p>Date: {appointment['date']}<br>Time: {appointment['time']}</p>")

        logging.info(f"Appointment booked: {appointment}")
        flash("Appointment booked successfully.", "success")
        return redirect(url_for('patient_dashboard'))

    doctors = {uid: info for uid, info in users.items() if info['role'] == 'doctor'}
    return render_template('book_appointment.html', doctors=doctors)




# ---------- View Appointment + Diagnosis ----------
@app.route('/appointment/<appointment_id>')
@role_required('doctor')
def view_appointment_doctor(appointment_id):
    appointment = appointments_dict.get(appointment_id)
    if not appointment or appointment['doctor_id'] != session['userid']:
        flash("Unauthorized or invalid appointment.", "danger")
        return redirect(url_for('doctor_dashboard'))

    patient = users.get(appointment['patient_id'], {})
    return render_template(
        'view_appointment_doctor.html',
        appointment=appointment,
        patient=patient
    )

@app.route('/submit_diagnosis/<appointment_id>', methods=['POST'])
@role_required('doctor')
def submit_diagnosis(appointment_id):
    appointment = appointments_dict.get(appointment_id)
    
    if not appointment or appointment['doctor_id'] != session['userid']:
        flash("Unauthorized or invalid appointment.", "danger")
        return redirect(url_for('doctor_dashboard'))  # Must be valid for logged-in doctor

    # Update the appointment with diagnosis data
    appointment['diagnosis'] = request.form['diagnosis']
    appointment['treatment_plan'] = request.form['treatment_plan']
    appointment['prescription'] = request.form['prescription']
    appointment['status'] = 'Completed'

    flash("Diagnosis submitted successfully!", "success")
    return redirect(url_for('doctor_dashboard'))





@app.route('/appointment_patient/<appointment_id>')
@role_required('patient')
def view_appointment_patient(appointment_id):
    appointment = appointments_dict.get(appointment_id)
    if not appointment or appointment['patient_id'] != session['userid']:
        flash("Unauthorized or invalid appointment.", "danger")
        return redirect(url_for('patient_dashboard'))

    if 'created_at' not in appointment:
        appointment['created_at'] = datetime.now()

    doctor = users.get(appointment['doctor_id'], {})
    return render_template('view_appointment_patient.html', appointment=appointment, doctor=doctor)

# ---------- Update Profile ----------


@app.route('/doctor/profile')
@role_required('doctor')
def doctor_profile():
    user = users.get(session['userid'])
    return render_template('doctor_profile.html', user=user)

@app.route('/patient/profile')
@role_required('patient')
def patient_profile():
    user = users.get(session['userid'])
    return render_template('patient_profile.html', user=user)



# ---------- View Diagnosis ----------
@app.route('/view_diagnosis')
@role_required('patient')
def view_diagnosis():
    patient_id = session['userid']
    patient_diagnoses = [a for a in appointments_dict.values() if a['patient_id'] == patient_id and a.get('diagnosis')]
    return render_template('view_diagnosis.html', diagnoses=patient_diagnoses)

# ---------- Notifications ----------
@app.route('/notifications')
def view_notifications():
    if 'userid' not in session:
        return redirect(url_for('login'))

    user_id = session['userid']
    user_notifications = [n for n in notifications if n['user_id'] == user_id]
    return render_template('notifications.html', notifications=user_notifications)

# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True)
