from flask import Flask, request, jsonify
from flask_cors import CORS
import pymongo
import bcrypt
import os
import uuid
import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import re
import jwt
from functools import wraps
from bson import ObjectId

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database connection
class Database:
    def __init__(self):
        self.client = None
        self.patients_collection = None
        self.connect()
    
    def connect(self):
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            db_name = os.getenv("DB_NAME", "patients_db")
            
            self.client = pymongo.MongoClient(mongo_uri)
            db = self.client[db_name]
            self.patients_collection = db["patients_v2"]
            
            # Create indexes
            self.patients_collection.create_index("patient_id", unique=True, sparse=True)
            self.patients_collection.create_index("email", unique=True, sparse=True)
            self.patients_collection.create_index("mobile", unique=True, sparse=True)
            
            print("✅ Connected to MongoDB successfully")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.patients_collection = None
    
    def close(self):
        if self.client:
            self.client.close()

# Initialize database
db = Database()

# User Activity Tracking System
class UserActivityTracker:
    """Track all user activities from login to logout"""
    
    def __init__(self, db):
        self.db = db
        self.activities_collection = db.client[os.getenv("DB_NAME", "patients_db")]["user_activities"]
        
        # Create indexes for efficient querying
        self.activities_collection.create_index("user_email")
        self.activities_collection.create_index("session_id")
        self.activities_collection.create_index("timestamp")
        self.activities_collection.create_index("activity_type")
        print("✅ User Activity Tracker initialized")
    
    def start_user_session(self, user_email, user_role, username, user_id):
        """Start tracking a new user session"""
        session_id = str(uuid.uuid4())
        session_start = datetime.now()
        
        session_data = {
            "session_id": session_id,
            "user_email": user_email,
            "user_role": user_role,
            "username": username,
            "user_id": user_id,
            "session_start": session_start,
            "session_end": None,
            "is_active": True,
            "activities": [],
            "created_at": session_start
        }
        
        result = self.activities_collection.insert_one(session_data)
        print(f"🔍 Started tracking session {session_id} for user {user_email}")
        return session_id
    
    def end_user_session(self, user_email, session_id=None):
        """End a user session"""
        if session_id:
            # End specific session
            result = self.activities_collection.update_one(
                {"session_id": session_id, "is_active": True},
                {
                    "$set": {
                        "session_end": datetime.now(),
                        "is_active": False
                    }
                }
            )
        else:
            # End all active sessions for user
            result = self.activities_collection.update_many(
                {"user_email": user_email, "is_active": True},
                {
                    "$set": {
                        "session_end": datetime.now(),
                        "is_active": False
                    }
                }
            )
        
        print(f"🔍 Ended session(s) for user {user_email}")
        return result.modified_count
    
    def log_activity(self, user_email, activity_type, activity_data, session_id=None):
        """Log a user activity"""
        if not session_id:
            # Find active session for user
            active_session = self.activities_collection.find_one(
                {"user_email": user_email, "is_active": True}
            )
            if active_session:
                session_id = active_session["session_id"]
            else:
                print(f"⚠️ No active session found for user {user_email}")
                return None
        
        activity_entry = {
            "activity_id": str(uuid.uuid4()),
            "timestamp": datetime.now(),
            "activity_type": activity_type,
            "activity_data": activity_data,
            "ip_address": request.remote_addr if request else "unknown"
        }
        
        # Add activity to session
        result = self.activities_collection.update_one(
            {"session_id": session_id},
            {"$push": {"activities": activity_entry}}
        )
        
        print(f"🔍 Logged activity: {activity_type} for user {user_email}")
        return activity_entry["activity_id"]
    
    def get_user_activities(self, user_email, limit=100):
        """Get all activities for a user"""
        sessions = list(self.activities_collection.find(
            {"user_email": user_email},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit))
        
        return sessions
    
    def get_session_activities(self, session_id):
        """Get all activities for a specific session"""
        session = self.activities_collection.find_one(
            {"session_id": session_id},
            {"_id": 0}
        )
        return session
    
    def get_activity_summary(self, user_email):
        """Get summary of user activities"""
        pipeline = [
            {"$match": {"user_email": user_email}},
            {"$unwind": "$activities"},
            {"$group": {
                "_id": "$activities.activity_type",
                "count": {"$sum": 1},
                "last_activity": {"$max": "$activities.timestamp"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        summary = list(self.activities_collection.aggregate(pipeline))
        return summary

# Initialize activity tracker
activity_tracker = UserActivityTracker(db)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Token expires in 24 hours

def generate_jwt_token(user_data):
    """Generate JWT token for user"""
    payload = {
        "user_id": str(user_data.get("_id")) if user_data.get("_id") else None,
        "patient_id": user_data.get("patient_id"),
        "email": user_data.get("email"),
        "username": user_data.get("username"),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Add user data to request
        request.user_data = payload
        return f(*args, **kwargs)
    
    return decorated

# Utility functions
def generate_patient_id():
    """Generate unique patient ID with timestamp and random component"""
    import time
    timestamp = int(time.time())
    random_component = uuid.uuid4().hex[:6].upper()
    return f"PAT{timestamp}{random_component}"

def generate_unique_patient_id():
    """Generate a unique patient ID that doesn't exist in database"""
    max_attempts = 10
    for attempt in range(max_attempts):
        patient_id = generate_patient_id()
        
        # Check if this patient ID already exists
        if db.patients_collection is not None:
            existing_patient = db.patients_collection.find_one({"patient_id": patient_id})
            if existing_patient is None:
                return patient_id
        
        # If we've tried too many times, add a random suffix
        if attempt == max_attempts - 1:
            extra_random = uuid.uuid4().hex[:4].upper()
            patient_id = f"{patient_id}{extra_random}"
            return patient_id
    
    # Fallback: use timestamp with more random components
    timestamp = int(time.time() * 1000)  # Use milliseconds
    random_component = uuid.uuid4().hex[:8].upper()
    return f"PAT{timestamp}{random_component}"

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email using Gmail SMTP"""
    try:
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        
        if not sender_email or not sender_password:
            print("Email configuration missing - using mock email")
            return True  # Mock success for testing
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return True  # Mock success for testing

def send_otp_email(email: str, otp: str) -> bool:
    """Send OTP email"""
    subject = "Patient Alert System - OTP Verification"
    body = f"""
    Hello!
    
    Your OTP for Patient Alert System is: {otp}
    
    This OTP is valid for 10 minutes.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    Patient Alert System Team
    """
    return send_email(email, subject, body)

def send_patient_id_email(email: str, patient_id: str, username: str) -> bool:
    """Send Patient ID to user's email"""
    subject = "Patient Alert System - Your Patient ID"
    body = f"""
    Hello {username}!
    
    Your account has been successfully created.
    
    Your Patient ID is: {patient_id}
    
    Please keep this Patient ID safe. You may need it for future reference.
    
    You can now login using your Patient ID or email address.
    
    Best regards,
    Patient Alert System Team
    """
    return send_email(email, subject, body)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        # Ensure password is string and encode it
        if isinstance(password, bytes):
            password = password.decode('utf-8')
        password_bytes = password.encode('utf-8')
        
        # Ensure hashed is string and encode it
        if isinstance(hashed, bytes):
            hashed = hashed.decode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_mobile(mobile: str) -> bool:
    """Validate mobile number"""
    return mobile.isdigit() and len(mobile) >= 10

def is_profile_complete(patient_doc: dict) -> bool:
    """Check if patient profile is complete"""
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'blood_type']
    return all(field in patient_doc for field in required_fields)

# API Routes
@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Patient Alert System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "POST /signup - Register new patient",
            "POST /send-otp - Send OTP to email",
            "POST /verify-otp - Verify OTP and activate account",
            "POST /login - Login with Patient ID/Email",
            "POST /forgot-password - Send password reset OTP",
            "POST /reset-password - Reset password with OTP",
            "POST /complete-profile - Complete patient profile",
            "GET /profile/<patient_id> - Get patient profile",
            "GET / - API information"
        ]
    })

@app.route('/signup', methods=['POST'])
def signup():
    """Register a new patient - Step 1: Collect data and send OTP"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'mobile', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        username = data['username'].strip()
        email = data['email'].strip()
        mobile = data['mobile'].strip()
        password = data['password']
        
        # Validate email and mobile
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        if not validate_mobile(mobile):
            return jsonify({"error": "Invalid mobile number"}), 400
        
        # Check if username exists
        if db.patients_collection.find_one({"username": username}):
            return jsonify({"error": "Username already exists"}), 400
        
        # Check if email exists
        if db.patients_collection.find_one({"email": email}):
            return jsonify({"error": "Email already exists"}), 400
        
        # Check if mobile exists
        if db.patients_collection.find_one({"mobile": mobile}):
            return jsonify({"error": "Mobile number already exists"}), 400
        
        # Generate OTP
        otp = generate_otp()
        
        # Store temporary signup data (not a real account yet)
        temp_signup_data = {
            "username": username,
            "email": email,
            "mobile": mobile,
            "password_hash": hash_password(password),
            "otp": otp,
            "otp_created_at": datetime.now(),
            "otp_expires_at": datetime.now() + timedelta(minutes=10),
            "status": "temp_signup",
            "created_at": datetime.now()
        }
        
        # Store in temporary collection or with temp status
        db.patients_collection.insert_one(temp_signup_data)
        
        # Send OTP email
        if send_otp_email(email, otp):
            return jsonify({
                "email": email,
                "status": "otp_sent",
                "message": "Please check your email for OTP verification."
            }), 200
        else:
            # Remove temporary data if email failed
            db.patients_collection.delete_one({"email": email, "status": "temp_signup"})
            return jsonify({"error": "Failed to send OTP email"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to email for verification"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Check if user exists
        user = db.patients_collection.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP in database (with expiration)
        db.patients_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "otp": otp,
                    "otp_created_at": datetime.now(),
                    "otp_expires_at": datetime.now() + timedelta(minutes=10)
                }
            }
        )
        
        # Send OTP email
        if send_otp_email(email, otp):
            return jsonify({
                "message": "OTP sent successfully",
                "email": email
            }), 200
        else:
            return jsonify({"error": "Failed to send OTP email"}), 500
    
    except Exception as e:
        return jsonify({"error": f"OTP sending failed: {str(e)}"}), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and create actual account"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400
        
        # Find temporary signup data by email
        temp_user = db.patients_collection.find_one({"email": email, "status": "temp_signup"})
        if not temp_user:
            return jsonify({"error": "No pending signup found for this email"}), 404
        
        # Check OTP
        if temp_user.get("otp") != otp:
            return jsonify({"error": "Invalid OTP"}), 400
        
        # Check if OTP expired
        if temp_user.get("otp_expires_at") < datetime.now():
            return jsonify({"error": "OTP has expired"}), 400
        
        # Generate unique patient ID for actual account
        patient_id = generate_unique_patient_id()
        
        # Create actual account by updating the temporary data
        db.patients_collection.update_one(
            {"email": email, "status": "temp_signup"},
            {
                "$set": {
                    "patient_id": patient_id,
                    "status": "active",
                    "email_verified": True,
                    "verified_at": datetime.now()
                },
                "$unset": {
                    "otp": "",
                    "otp_created_at": "",
                    "otp_expires_at": ""
                }
            }
        )
        
        # Send Patient ID email
        send_patient_id_email(email, patient_id, temp_user["username"])
        
        # Get the updated user data
        updated_user = db.patients_collection.find_one({"patient_id": patient_id})
        
        # Generate JWT token
        token = generate_jwt_token(updated_user)
        
        return jsonify({
            "patient_id": patient_id,
            "username": temp_user["username"],
            "email": temp_user["email"],
            "mobile": temp_user["mobile"],
            "status": "active",
            "token": token,
            "message": "Account created and verified successfully! Your Patient ID has been sent to your email."
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"OTP verification failed: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login patient with Patient ID/Email and password"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        login_identifier = data.get('login_identifier', '').strip()
        password = data.get('password', '')
        
        if not login_identifier or not password:
            return jsonify({"error": "Login identifier and password are required"}), 400
        
        # Find user by Patient ID or Email
        user = db.patients_collection.find_one({"patient_id": login_identifier})
        if not user:
            user = db.patients_collection.find_one({"email": login_identifier})
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check if account is active
        if user.get("status") != "active":
            return jsonify({"error": "Account not activated. Please verify your email."}), 401
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check profile completion
        profile_complete = is_profile_complete(user)
        
        # Debug logging to identify null values
        print(f"🔍 Login Debug - User Data:")
        print(f"  patient_id: {user.get('patient_id')}")
        print(f"  username: {user.get('username')}")
        print(f"  email: {user.get('email')}")
        print(f"  _id: {user.get('_id')}")
        print(f"  status: {user.get('status')}")
        print(f"  profile_complete: {profile_complete}")
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        # Start tracking user session
        session_id = activity_tracker.start_user_session(
            user_email=user["email"],
            user_role="patient",
            username=user["username"],
            user_id=user["patient_id"]
        )
        
        # Log login activity
        activity_tracker.log_activity(
            user_email=user["email"],
            activity_type="login",
            activity_data={
                "login_method": "email" if "@" in login_identifier else "patient_id",
                "profile_complete": profile_complete,
                "session_id": session_id
            },
            session_id=session_id
        )
        
        return jsonify({
            "patient_id": user.get("patient_id", ""),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "object_id": str(user.get("_id", "")) if user.get("_id") else "",  # Handle null Object ID
            "is_profile_complete": profile_complete,
            "token": token,
            "session_id": session_id,  # Include session ID for tracking
            "message": "Login successful" if profile_complete else "Login successful. Please complete your profile."
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout user and end session tracking"""
    try:
        data = request.get_json()
        user_email = data.get('email')
        session_id = data.get('session_id')
        
        if not user_email:
            return jsonify({"error": "User email is required"}), 400
        
        # Log logout activity before ending session
        activity_tracker.log_activity(
            user_email=user_email,
            activity_type="logout",
            activity_data={
                "logout_time": datetime.now().isoformat(),
                "session_id": session_id
            },
            session_id=session_id
        )
        
        # End user session
        ended_sessions = activity_tracker.end_user_session(user_email, session_id)
        
        return jsonify({
            "success": True,
            "message": "Logout successful",
            "ended_sessions": ended_sessions
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset OTP"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        login_identifier = data.get('login_identifier', '').strip()
        
        if not login_identifier:
            return jsonify({"error": "Login identifier is required"}), 400
        
        # Find user by Patient ID or Email
        user = db.patients_collection.find_one({"patient_id": login_identifier})
        if not user:
            user = db.patients_collection.find_one({"email": login_identifier})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        email = user["email"]
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP
        db.patients_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_otp": otp,
                    "reset_otp_created_at": datetime.now(),
                    "reset_otp_expires_at": datetime.now() + timedelta(minutes=10)
                }
            }
        )
        
        # Send OTP email
        if send_otp_email(email, otp):
            return jsonify({
                "message": "Password reset OTP sent successfully",
                "email": email
            }), 200
        else:
            return jsonify({"error": "Failed to send OTP email"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Password reset failed: {str(e)}"}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with OTP"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '')
        
        if not email or not otp or not new_password:
            return jsonify({"error": "Email, OTP, and new password are required"}), 400
        
        # Find user by email
        user = db.patients_collection.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check OTP
        if user.get("reset_otp") != otp:
            return jsonify({"error": "Invalid OTP"}), 400
        
        # Check if OTP expired
        if user.get("reset_otp_expires_at") < datetime.now():
            return jsonify({"error": "OTP has expired"}), 400
        
        # Hash new password
        new_hashed_password = hash_password(new_password)
        
        # Update password
        db.patients_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "password_hash": new_hashed_password,
                    "password_updated_at": datetime.now()
                },
                "$unset": {
                    "reset_otp": "",
                    "reset_otp_created_at": "",
                    "reset_otp_expires_at": ""
                }
            }
        )
        
        return jsonify({
            "patient_id": user.get("patient_id", ""),
            "username": user.get("username", ""),
            "email": user["email"],
            "mobile": user.get("mobile", ""),
            "status": "active",
            "message": "Password reset successfully"
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Password reset failed: {str(e)}"}), 500

@app.route('/complete-profile', methods=['POST'])
@token_required
def complete_profile():
    """Complete patient profile information"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        # Get patient_id from JWT token
        patient_id = request.user_data.get('patient_id')
        
        if not patient_id:
            return jsonify({"error": "Patient ID not found in token"}), 400
        
        # Find user by Patient ID
        user = db.patients_collection.find_one({"patient_id": patient_id})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Extract profile data with safe handling of null values
        first_name = request.json.get('first_name', '').strip() if request.json.get('first_name') else ''
        last_name = request.json.get('last_name', '').strip() if request.json.get('last_name') else ''
        date_of_birth = request.json.get('date_of_birth', '').strip() if request.json.get('date_of_birth') else ''
        blood_type = request.json.get('blood_type', '').strip() if request.json.get('blood_type') else ''
        is_pregnant = request.json.get('is_pregnant', False)
        last_period_date = request.json.get('last_period_date', '').strip() if request.json.get('last_period_date') else ''
        weight = request.json.get('weight', '').strip() if request.json.get('weight') else ''
        height = request.json.get('height', '').strip() if request.json.get('height') else ''
        
        # Emergency contact
        emergency_contact = {
            "name": request.json.get('emergency_name', '').strip() if request.json.get('emergency_name') else '',
            "relationship": request.json.get('emergency_relationship', '').strip() if request.json.get('emergency_relationship') else '',
            "phone": request.json.get('emergency_phone', '').strip() if request.json.get('emergency_phone') else ''
        }
        
        # Calculate age
        age = None
        if date_of_birth:
            try:
                from datetime import datetime
                birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d')
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            except:
                age = None
        
        # Calculate pregnancy information if pregnant
        calculated_pregnancy_week = None
        calculated_expected_delivery = None
        
        if is_pregnant and last_period_date:
            try:
                from datetime import datetime, timedelta
                last_period = datetime.strptime(last_period_date, '%Y-%m-%d')
                today = datetime.now()
                
                # Calculate pregnancy week (gestational age)
                days_diff = (today - last_period).days
                calculated_pregnancy_week = max(1, min(42, days_diff // 7))
                
                # Calculate expected delivery date (40 weeks from last period)
                calculated_expected_delivery = last_period + timedelta(weeks=40)
                calculated_expected_delivery = calculated_expected_delivery.strftime('%Y-%m-%d')
                
            except Exception as e:
                print(f"Error calculating pregnancy dates: {e}")
        
        # Update profile
        update_data = {
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": date_of_birth,
            "age": age,
            "blood_type": blood_type,
            "weight": weight,
            "height": height,
            "is_pregnant": is_pregnant,
            "last_period_date": last_period_date if is_pregnant else None,
            "pregnancy_week": calculated_pregnancy_week if is_pregnant else None,
            "expected_delivery_date": calculated_expected_delivery if is_pregnant else None,
            "emergency_contact": emergency_contact,
            "profile_completed_at": datetime.now()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": update_data}
        )
        
        return jsonify({
            "patient_id": patient_id,
            "message": "Profile completed successfully",
            "is_profile_complete": True
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Profile completion failed: {str(e)}"}), 500

@app.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token and return user data"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({"error": "Token is required"}), 400
        
        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        return jsonify({
            "valid": True,
            "user_data": payload,
            "message": "Token is valid"
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 500

@app.route('/profile/<patient_id>', methods=['GET'])
def get_profile(patient_id):
    """Get patient profile information"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        return jsonify({
            "patient_id": patient["patient_id"],
            "username": patient["username"],
            "email": patient["email"],
            "mobile": patient["mobile"],
            "first_name": patient.get("first_name"),
            "last_name": patient.get("last_name"),
            "age": patient.get("age"),
            "blood_type": patient.get("blood_type"),
            "is_pregnant": patient.get("is_pregnant"),
            "last_period_date": patient.get("last_period_date"),
            "pregnancy_week": patient.get("pregnancy_week"),
            "expected_delivery_date": patient.get("expected_delivery_date"),
            "emergency_contact": patient.get("emergency_contact"),
            "preferences": patient.get("preferences")
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to get profile: {str(e)}"}), 500

@app.route('/save-sleep-log', methods=['POST'])
def save_sleep_log():
    """Save sleep log data to MongoDB"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received sleep log data: {json.dumps(data, indent=2)}")
        
        # Validate required fields
        required_fields = ['userId', 'userRole', 'startTime', 'endTime', 'totalSleep', 'sleepRating']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Check if we have Patient ID for precise linking
        patient_id = data.get('userId')
        if not patient_id:
            return jsonify({
                'success': False, 
                'message': 'Patient ID is required for precise patient linking. Please ensure you are logged in.',
                'debug_info': {
                    'received_userId': data.get('userId'),
                    'received_data': data
                }
            }), 400
        
        # Create sleep log document
        sleep_log = {
            'userId': data['userId'],
            'userRole': data['userRole'],
            'username': data.get('username', 'unknown'),
            'email': data.get('email', 'unknown'),  # Add email for better user linking
            'startTime': data['startTime'],
            'endTime': data['endTime'],
            'totalSleep': data['totalSleep'],
            'smartAlarmEnabled': data.get('smartAlarmEnabled', False),
            'optimalWakeUpTime': data.get('optimalWakeUpTime', ''),
            'sleepRating': data['sleepRating'],
            'notes': data.get('notes', ''),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'createdAt': datetime.now(),
        }
        
        # Store sleep log within the patient's document
        if data['userRole'] == 'doctor':
            # For doctors, store in separate collection (as before)
            collection = db.doctors_collection
            result = collection.insert_one(sleep_log)
            
            if result.inserted_id:
                return jsonify({
                    'success': True,
                    'message': 'Sleep log saved successfully',
                    'sleepLogId': str(result.inserted_id)
                }), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to save sleep log'}), 500
        else:
            # For patients, store within their patient document using Patient ID
            patient_id = data.get('userId')
            if not patient_id:
                return jsonify({
                    'success': False, 
                    'message': 'Patient ID is required. Please ensure you are logged in.',
                    'debug_info': {
                        'received_userId': data.get('userId'),
                        'received_data': data
                    }
                }), 400
            
            print(f"🔍 Looking for patient with ID: {patient_id}")
            
            # Find patient by Patient ID (more reliable than email)
            patient = db.patients_collection.find_one({"patient_id": patient_id})
            if not patient:
                return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
            
            print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
            
            # Create sleep log entry (without MongoDB _id)
            sleep_log_entry = {
                'startTime': data['startTime'],
                'endTime': data['endTime'],
                'totalSleep': data['totalSleep'],
                'smartAlarmEnabled': data.get('smartAlarmEnabled', False),
                'optimalWakeUpTime': data.get('optimalWakeUpTime', ''),
                'sleepRating': data['sleepRating'],
                'notes': data.get('notes', ''),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'createdAt': datetime.now(),
            }
            
            # Add sleep log to patient's sleep_logs array using Patient ID
            result = db.patients_collection.update_one(
                {"patient_id": patient_id},
                {
                    "$push": {"sleep_logs": sleep_log_entry},
                    "$set": {"last_updated": datetime.now()}
                }
            )
            
            if result.modified_count > 0:
                # Log the sleep log activity
                activity_tracker.log_activity(
                    user_email=patient.get('email'),
                    activity_type="sleep_log_created",
                    activity_data={
                        "sleep_log_id": "embedded_in_patient_doc",
                        "sleep_data": sleep_log_entry,
                        "patient_id": patient_id,
                        "total_sleep_logs": len(patient.get('sleep_logs', [])) + 1
                    }
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Sleep log saved successfully to patient profile',
                    'patientId': patient_id,
                    'patientEmail': patient.get('email'),
                    'sleepLogsCount': len(patient.get('sleep_logs', [])) + 1
                }), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to save sleep log to patient profile'}), 500
            
    except Exception as e:
        print(f"Error saving sleep log: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-sleep-logs/<username>', methods=['GET'])
def get_sleep_logs(username):
    """Get sleep logs for a specific user"""
    try:
        # Get user role from the username
        user_doc = db.patients_collection.find_one({"username": username})
        if not user_doc:
            # Try doctors collection
            user_doc = db.doctors_collection.find_one({"username": username})
            if not user_doc:
                return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_role = user_doc.get('role', 'patient')
        
        # Get sleep logs for this user
        if user_role == 'doctor':
            collection = db.doctors_collection
        else:
            collection = db.patients_collection
        
        # Find all sleep logs for this user
        sleep_logs = list(collection.find(
            {"username": username, "startTime": {"$exists": True}},
            {"_id": 0}  # Exclude MongoDB _id
        ))
        
        return jsonify({
            'success': True,
            'username': username,
            'userRole': user_role,
            'sleepLogs': sleep_logs,
            'count': len(sleep_logs)
        }), 200
        
    except Exception as e:
        print(f"Error retrieving sleep logs: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-sleep-logs-by-email/<email>', methods=['GET'])
def get_sleep_logs_by_email(email):
    """Get sleep logs for a specific user by email"""
    try:
        # Get user role from the email
        user_doc = db.patients_collection.find_one({"email": email})
        if not user_doc:
            # Try doctors collection
            user_doc = db.doctors_collection.find_one({"email": email})
            if not user_doc:
                return jsonify({'success': False, 'message': 'User not found with this email'}), 404
        
        user_role = user_doc.get('role', 'patient')
        username = user_doc.get('username', 'unknown')
        
        # Get sleep logs for this user by email
        if user_role == 'doctor':
            # For doctors, get from separate collection
            collection = db.doctors_collection
            sleep_logs = list(collection.find(
                {"email": email, "startTime": {"$exists": True}},
                {"_id": 0}  # Exclude MongoDB _id
            ))
        else:
            # For patients, get from their document's sleep_logs array
            sleep_logs = user_doc.get('sleep_logs', [])
        
        return jsonify({
            'success': True,
            'email': email,
            'username': username,
            'userRole': user_role,
            'sleepLogs': sleep_logs,
            'count': len(sleep_logs)
        }), 200
        
    except Exception as e:
        print(f"Error retrieving sleep logs by email: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/patient-complete-profile/<email>', methods=['GET'])
def get_patient_complete_profile(email):
    """Get complete patient profile including all health data"""
    try:
        # Find patient by email
        patient = db.patients_collection.find_one({"email": email})
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found with this email'}), 404
        
        # Return complete patient profile with all data
        complete_profile = {
            'success': True,
            'patient_id': patient.get('patient_id'),
            'username': patient.get('username'),
            'email': patient.get('email'),
            'mobile': patient.get('mobile'),
            'first_name': patient.get('first_name'),
            'last_name': patient.get('last_name'),
            'age': patient.get('age'),
            'blood_type': patient.get('blood_type'),
            'weight': patient.get('weight'),
            'height': patient.get('height'),
            'is_pregnant': patient.get('is_pregnant'),
            'last_period_date': patient.get('last_period_date'),
            'pregnancy_week': patient.get('pregnancy_week'),
            'expected_delivery_date': patient.get('expected_delivery_date'),
            'emergency_contact': patient.get('emergency_contact'),
            'preferences': patient.get('preferences'),
            'profile_completed_at': patient.get('profile_completed_at'),
            'last_updated': patient.get('last_updated'),
            'health_data': {
                'sleep_logs': patient.get('sleep_logs', []),
                'sleep_logs_count': len(patient.get('sleep_logs', [])),
                'food_logs': patient.get('food_logs', []),
                'food_logs_count': len(patient.get('food_logs', [])),
                'medication_logs': patient.get('medication_logs', []),
                'medication_logs_count': len(patient.get('medication_logs', [])),
                'symptom_logs': patient.get('symptom_logs', []),
                'symptom_logs_count': len(patient.get('symptom_logs', [])),
                'mental_health_logs': patient.get('mental_health_logs', []),
                'mental_health_logs_count': len(patient.get('mental_health_logs', [])),
                'kick_count_logs': patient.get('kick_count_logs', []),
                'kick_count_logs_count': len(patient.get('kick_count_logs', [])),
            }
        }
        
        return jsonify(complete_profile), 200
        
    except Exception as e:
        print(f"Error retrieving complete patient profile: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# User Activity Management Endpoints
@app.route('/user-activities/<email>', methods=['GET'])
def get_user_activities(email):
    """Get all activities for a specific user"""
    try:
        activities = activity_tracker.get_user_activities(email)
        return jsonify({
            'success': True,
            'user_email': email,
            'activities': activities,
            'total_sessions': len(activities)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/session-activities/<session_id>', methods=['GET'])
def get_session_activities(session_id):
    """Get all activities for a specific session"""
    try:
        session = activity_tracker.get_session_activities(session_id)
        if session:
            return jsonify({
                'success': True,
                'session': session
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/activity-summary/<email>', methods=['GET'])
def get_activity_summary(email):
    """Get summary of user activities"""
    try:
        summary = activity_tracker.get_activity_summary(email)
        return jsonify({
            'success': True,
            'user_email': email,
            'summary': summary,
            'total_activities': sum(item['count'] for item in summary)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/track-activity', methods=['POST'])
def track_activity():
    """Manually track a user activity"""
    try:
        data = request.get_json()
        user_email = data.get('email')
        activity_type = data.get('activity_type')
        activity_data = data.get('activity_data', {})
        session_id = data.get('session_id')
        
        if not user_email or not activity_type:
            return jsonify({'success': False, 'message': 'Email and activity_type are required'}), 400
        
        # Log the activity
        activity_id = activity_tracker.log_activity(
            user_email=user_email,
            activity_type=activity_type,
            activity_data=activity_data,
            session_id=session_id
        )
        
        if activity_id:
            return jsonify({
                'success': True,
                'message': 'Activity tracked successfully',
                'activity_id': activity_id
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to track activity'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/active-sessions/<email>', methods=['GET'])
def get_active_sessions(email):
    """Get all active sessions for a user"""
    try:
        active_sessions = list(activity_tracker.activities_collection.find(
            {"user_email": email, "is_active": True},
            {"_id": 0}
        ))
        
        return jsonify({
            'success': True,
            'user_email': email,
            'active_sessions': active_sessions,
            'count': len(active_sessions)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/save-kick-session', methods=['POST'])
def save_kick_session():
    """Save kick session data to MongoDB"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received kick session data: {json.dumps(data, indent=2)}")
        
        # Validate required fields
        required_fields = ['userId', 'userRole', 'kickCount', 'sessionDuration']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Check if we have Patient ID for precise linking
        patient_id = data.get('userId')
        if not patient_id:
            return jsonify({
                'success': False, 
                'message': 'Patient ID is required for precise patient linking. Please ensure you are logged in.',
                'debug_info': {
                    'received_userId': data.get('userId'),
                    'received_data': data
                }
            }), 400
        
        print(f"🔍 Looking for patient with ID: {patient_id}")
        
        # Find patient by Patient ID (more reliable than email)
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
        
        # Create kick session entry
        kick_session_entry = {
            'kickCount': data['kickCount'],
            'sessionDuration': data['sessionDuration'],
            'sessionStartTime': data.get('sessionStartTime'),
            'sessionEndTime': data.get('sessionEndTime'),
            'averageKicksPerMinute': data.get('averageKicksPerMinute', 0),
            'notes': data.get('notes', ''),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'createdAt': datetime.now(),
        }
        
        # Add kick session to patient's kick_count_logs array using Patient ID
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {
                "$push": {"kick_count_logs": kick_session_entry},
                "$set": {"last_updated": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            # Log the kick session activity
            activity_tracker.log_activity(
                user_email=patient.get('email'),
                activity_type="kick_session_created",
                activity_data={
                    "kick_session_id": "embedded_in_patient_doc",
                    "kick_data": kick_session_entry,
                    "patient_id": patient_id,
                    "total_kick_sessions": len(patient.get('kick_count_logs', [])) + 1
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Kick session saved successfully to patient profile',
                'patientId': patient_id,
                'patientEmail': patient.get('email'),
                'kickSessionsCount': len(patient.get('kick_count_logs', [])) + 1
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save kick session to patient profile'}), 500
            
    except Exception as e:
        print(f"Error saving kick session: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-kick-history/<patient_id>', methods=['GET'])
def get_kick_history(patient_id):
    """Get kick history for a specific patient"""
    try:
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get kick count logs
        kick_logs = patient.get('health_data', {}).get('kick_count_logs', [])
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'kick_logs': kick_logs,
            'totalSessions': len(kick_logs)
        }), 200
        
    except Exception as e:
        print(f"Error getting kick history: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-food-history/<patient_id>', methods=['GET'])
def get_food_history(patient_id):
    """Get food history for a specific patient"""
    try:
        print(f"🔍 Getting food history for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get food logs from patient document
        food_logs = patient.get('food_logs', [])
        
        # Sort by newest first
        food_logs.sort(key=lambda x: x.get('createdAt', datetime.min), reverse=True)
        
        # Convert datetime objects to strings for JSON serialization
        for entry in food_logs:
            if 'createdAt' in entry:
                entry['createdAt'] = entry['createdAt'].isoformat()
        
        print(f"✅ Retrieved {len(food_logs)} food entries for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'food_logs': food_logs,
            'totalEntries': len(food_logs)
        }), 200
        
    except Exception as e:
        print(f"Error getting food history: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-current-pregnancy-week/<patient_id>', methods=['GET'])
def get_current_pregnancy_week(patient_id):
    """Get current pregnancy week for a specific patient"""
    try:
        print(f"🔍 Getting current pregnancy week for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Try to get pregnancy week from patient's health data
        pregnancy_week = 1  # Default fallback
        pregnancy_info = {}
        auto_fetched = False
        
        try:
            # First try to get pregnancy week directly from patient document (your current structure)
            if 'pregnancy_week' in patient:
                pregnancy_week = patient['pregnancy_week']
                auto_fetched = True
                print(f"✅ Found pregnancy week in patient document: {pregnancy_week}")
            else:
                # Try to get from patient's health data
                health_data = patient.get('health_data', {})
                if 'pregnancy_week' in health_data:
                    pregnancy_week = health_data['pregnancy_week']
                    auto_fetched = True
                    print(f"✅ Found pregnancy week in health data: {pregnancy_week}")
                else:
                    # Try to get from pregnancy info
                    pregnancy_info = health_data.get('pregnancy_info', {})
                    if pregnancy_info and 'current_week' in pregnancy_info:
                        pregnancy_week = pregnancy_info['current_week']
                        auto_fetched = True
                        print(f"✅ Found pregnancy week in pregnancy info: {pregnancy_week}")
                    else:
                        print(f"⚠️ No pregnancy week found, using default: {pregnancy_week}")
        except Exception as e:
            print(f"⚠️ Error fetching pregnancy week: {e}, using default: {pregnancy_week}")
        
        print(f"✅ Retrieved pregnancy week: {pregnancy_week} for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'patientEmail': patient.get('email'),
            'current_pregnancy_week': pregnancy_week,
            'pregnancy_info': pregnancy_info,
            'auto_fetched': auto_fetched,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error getting current pregnancy week: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== NUTRITION ENDPOINTS ====================

@app.route('/nutrition/health', methods=['GET'])
def nutrition_health_check():
    """Health check endpoint for nutrition service"""
    return jsonify({
        'success': True,
        'message': 'Nutrition Service is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/nutrition/pregnancy-info/<patient_id>', methods=['GET'])
def get_pregnancy_info(patient_id):
    """Get pregnancy information for a patient"""
    try:
        if db.patients_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database not available'
            }), 500
        
        # Find patient by patient_id
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {patient_id}'
            }), 404
        
        # Extract pregnancy information from DIRECT fields (not health_data)
        is_pregnant = patient.get('is_pregnant', False)
        pregnancy_week = patient.get('pregnancy_week', 1)
        last_period_date = patient.get('last_period_date')
        expected_delivery_date = patient.get('expected_delivery_date')
        
        print(f"🤱 Patient pregnancy status: {is_pregnant}")
        print(f" Pregnancy week: {pregnancy_week}")
        
        if is_pregnant:
            # Determine trimester based on pregnancy week
            if pregnancy_week <= 12:
                trimester = "First Trimester"
            elif pregnancy_week <= 26:
                trimester = "Second Trimester"
            else:
                trimester = "Third Trimester"
            
            pregnancy_info = {
                'current_week': pregnancy_week,
                'trimester': trimester,
                'expected_delivery_date': expected_delivery_date,
                'last_period_date': last_period_date
            }
        else:
            pregnancy_info = {}
        
        return jsonify({
            'success': True,
            'is_pregnant': is_pregnant,
            'pregnancy_info': pregnancy_info
        }), 200
        
    except Exception as e:
        print(f"Error getting pregnancy info: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/save-detailed-food-entry', methods=['POST'])
def save_detailed_food_entry():
    """Save detailed food entry with allergies, medical conditions, and dietary preferences"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received detailed food entry data: {json.dumps(data, indent=2)}")
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields (pregnancy_week is now optional - will be auto-fetched)
        required_fields = ['userId', 'food_details', 'meal_type', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if we have Patient ID for precise linking
        patient_id = data.get('userId')
        user_email = data.get('email')
        
        if not patient_id:
            return jsonify({
                'success': False, 
                'message': 'Patient ID is required for precise patient linking. Please ensure you are logged in.',
                'debug_info': {
                    'received_userId': data.get('userId'),
                    'received_data': data
                }
            }), 400
        
        print(f"🔍 Looking for patient with ID: {patient_id}")
        
        # Find patient by Patient ID (more reliable than email)
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
        
        # Auto-fetch pregnancy week from patient's profile
        pregnancy_week = 1  # Default fallback
        try:
            # First try to get pregnancy week directly from patient document (your current structure)
            if 'pregnancy_week' in patient:
                pregnancy_week = patient['pregnancy_week']
                print(f"✅ Auto-fetched pregnancy week from patient document: {pregnancy_week}")
            else:
                # Try to get from patient's health data
                health_data = patient.get('health_data', {})
                if 'pregnancy_week' in health_data:
                    pregnancy_week = health_data['pregnancy_week']
                    print(f"✅ Auto-fetched pregnancy week from health data: {pregnancy_week}")
                else:
                    # Try to get from pregnancy info
                    pregnancy_info = health_data.get('pregnancy_info', {})
                    if pregnancy_info and 'current_week' in pregnancy_info:
                        pregnancy_week = pregnancy_info['current_week']
                        print(f"✅ Auto-fetched pregnancy week from pregnancy info: {pregnancy_week}")
                    else:
                        print(f"⚠️ No pregnancy week found, using default: {pregnancy_week}")
        except Exception as e:
            print(f"⚠️ Error fetching pregnancy week: {e}, using default: {pregnancy_week}")
        
        # Create food entry (without MongoDB _id) with auto-fetched pregnancy week
        food_entry = {
            'food_details': data['food_details'],
            'meal_type': data['meal_type'],
            'pregnancy_week': pregnancy_week,  # Auto-fetched value
            'dietary_preference': data.get('dietary_preference', 'vegetarian'),
            'allergies': data.get('allergies', []),
            'medical_conditions': data.get('medical_conditions', []),
            'notes': data.get('notes', ''),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'createdAt': datetime.now(),
            'entry_type': 'detailed',
            'auto_fetched_pregnancy_week': True  # Flag to show it was auto-fetched
        }
        
        # Add food entry to patient's food_logs array using Patient ID
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {
                "$push": {"food_logs": food_entry},
                "$set": {"last_updated": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            # Also update patient's health data with allergies and medical conditions
            try:
                update_data = {}
                
                if data.get('allergies'):
                    update_data['health_data.allergies'] = data['allergies']
                
                if data.get('medical_conditions'):
                    update_data['health_data.medical_conditions'] = data['medical_conditions']
                
                if data.get('dietary_preference'):
                    update_data['health_data.dietary_preference'] = data['dietary_preference']
                
                if update_data:
                    db.patients_collection.update_one(
                        {"patient_id": patient_id},
                        {"$set": update_data}
                    )
                    print(f"✅ Updated patient health data for: {patient_id}")
            except Exception as e:
                print(f"⚠️ Warning: Could not update patient health data: {e}")
            
            # Log the food entry activity
            activity_tracker.log_activity(
                user_email=patient.get('email'),
                activity_type="detailed_food_entry_created",
                activity_data={
                    "food_entry_id": "embedded_in_patient_doc",
                    "food_data": food_entry,
                    "patient_id": patient_id,
                    "total_food_logs": len(patient.get('food_logs', [])) + 1
                }
            )
            
            print(f"✅ Detailed food entry saved successfully for user: {patient_id}")
            
            return jsonify({
                'success': True,
                'message': 'Detailed food entry saved successfully to patient profile',
                'patientId': patient_id,
                'patientEmail': patient.get('email'),
                'foodLogsCount': len(patient.get('food_logs', [])) + 1
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save food entry to patient profile'}), 500
        
    except Exception as e:
        print(f"Error saving detailed food entry: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/save-food-entry', methods=['POST'])
def save_food_entry():
    """Save basic food entry (for backward compatibility)"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received basic food entry data: {json.dumps(data, indent=2)}")
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields (pregnancy_week is now optional - will be auto-fetched)
        required_fields = ['userId', 'food_details', 'meal_type', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if we have Patient ID for precise linking
        patient_id = data.get('userId')
        user_email = data.get('email')
        
        if not patient_id:
            return jsonify({
                'success': False, 
                'message': 'Patient ID is required for precise patient linking. Please ensure you are logged in.',
                'debug_info': {
                    'received_userId': data.get('userId'),
                    'received_data': data
                }
            }), 400
        
        print(f"🔍 Looking for patient with ID: {patient_id}")
        
        # Find patient by Patient ID (more reliable than email)
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
        
        # Auto-fetch pregnancy week from patient's profile
        pregnancy_week = 1  # Default fallback
        try:
            # First try to get pregnancy week directly from patient document (your current structure)
            if 'pregnancy_week' in patient:
                pregnancy_week = patient['pregnancy_week']
                print(f"✅ Auto-fetched pregnancy week from patient document: {pregnancy_week}")
            else:
                # Try to get from patient's health data
                health_data = patient.get('health_data', {})
                if 'pregnancy_week' in health_data:
                    pregnancy_week = health_data['pregnancy_week']
                    print(f"✅ Auto-fetched pregnancy week from health data: {pregnancy_week}")
                else:
                    # Try to get from pregnancy info
                    pregnancy_info = health_data.get('pregnancy_info', {})
                    if pregnancy_info and 'current_week' in pregnancy_info:
                        pregnancy_week = pregnancy_info['current_week']
                        print(f"✅ Auto-fetched pregnancy week from pregnancy info: {pregnancy_week}")
                    else:
                        print(f"⚠️ No pregnancy week found, using default: {pregnancy_week}")
        except Exception as e:
            print(f"⚠️ Error fetching pregnancy week: {e}, using default: {pregnancy_week}")
        
        # Create food entry (without MongoDB _id) with auto-fetched pregnancy week
        food_entry = {
            'food_details': data['food_details'],
            'meal_type': data['meal_type'],
            'pregnancy_week': pregnancy_week,  # Auto-fetched value
            'notes': data.get('notes', ''),
            'transcribed_text': data.get('transcribed_text', ''),
            'nutritional_breakdown': data.get('nutritional_breakdown', {}),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'createdAt': datetime.now(),
            'entry_type': 'basic',
            'auto_fetched_pregnancy_week': True  # Flag to show it was auto-fetched
        }
        
        # Add food entry to patient's food_logs array using Patient ID
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {
                "$push": {"food_logs": food_entry},
                "$set": {"last_updated": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            # Log the food entry activity
            activity_tracker.log_activity(
                user_email=patient.get('email'),
                activity_type="basic_food_entry_created",
                activity_data={
                    "food_entry_id": "embedded_in_patient_doc",
                    "food_data": food_entry,
                    "patient_id": patient_id,
                    "total_food_logs": len(patient.get('food_logs', [])) + 1
                }
            )
            
            print(f"✅ Basic food entry saved successfully for user: {patient_id}")
            
            return jsonify({
                'success': True,
                'message': 'Food entry saved successfully to patient profile',
                'patientId': patient_id,
                'patientEmail': patient.get('email'),
                'foodLogsCount': len(patient.get('food_logs', [])) + 1
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save food entry to patient profile'}), 500
        
    except Exception as e:
        print(f"Error saving food entry: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/get-food-entries/<user_id>', methods=['GET'])
def get_food_entries(user_id):
    """Get food entries for a specific user"""
    try:
        print(f"🔍 Getting food entries for user ID: {user_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": user_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {user_id}'
            }), 404
        
        # Get food logs from patient document
        food_logs = patient.get('food_logs', [])
        
        # Sort by newest first (most recent createdAt)
        food_logs.sort(key=lambda x: x.get('createdAt', datetime.min), reverse=True)
        
        # Convert datetime objects to strings for JSON serialization
        for entry in food_logs:
            if 'createdAt' in entry:
                entry['createdAt'] = entry['createdAt'].isoformat()
        
        print(f"✅ Retrieved {len(food_logs)} food entries for user: {user_id}")
        
        return jsonify({
            'success': True,
            'entries': food_logs,
            'total_entries': len(food_logs)
        }), 200
        
    except Exception as e:
        print(f"Error getting food entries: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile information"""
    try:
        if db.patients_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database not available'
            }), 500
        
        # Find patient by patient_id
        patient = db.patients_collection.find_one({"patient_id": user_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {user_id}'
            }), 404
        
        # Extract relevant profile information
        profile = {
            'username': patient.get('username', ''),
            'email': patient.get('email', ''),
            'pregnancy_week': patient.get('health_data', {}).get('pregnancy_week', 1),
            'allergies': patient.get('health_data', {}).get('allergies', []),
            'medical_conditions': patient.get('health_data', {}).get('medical_conditions', []),
            'dietary_preference': patient.get('health_data', {}).get('dietary_preference', 'vegetarian')
        }
        
        return jsonify({
            'success': True,
            'profile': profile
        }), 200
        
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/update-pregnancy-info', methods=['POST'])
def update_pregnancy_info():
    """Update pregnancy information for a patient"""
    try:
        if db.patients_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database not available'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        patient_id = data.get('patient_id')
        if not patient_id:
            return jsonify({
                'success': False,
                'message': 'Patient ID is required'
            }), 400
        
        # Find and update patient
        update_data = {
            'health_data.is_pregnant': data.get('is_pregnant', True),
            'last_updated': datetime.now()
        }
        
        if data.get('last_period_date'):
            update_data['health_data.pregnancy_info.last_period_date'] = data['last_period_date']
        
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({
                'success': True,
                'message': 'Pregnancy information updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No changes made to pregnancy information'
            }), 400
        
    except Exception as e:
        print(f"Error updating pregnancy info: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/daily-calorie-summary/<user_id>', methods=['GET'])
def get_daily_calorie_summary(user_id):
    """Get daily calorie summary for a user"""
    try:
        print(f"🔍 Getting daily calorie summary for user ID: {user_id}")
        
        # Get today's date
        today = datetime.now().date()
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": user_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {user_id}'
            }), 404
        
        # Get food logs from patient document
        food_logs = patient.get('food_logs', [])
        
        # Filter food entries for today
        today_entries = []
        for entry in food_logs:
            entry_date = entry.get('createdAt')
            if isinstance(entry_date, datetime):
                if entry_date.date() == today:
                    today_entries.append(entry)
            elif isinstance(entry_date, str):
                try:
                    entry_datetime = datetime.fromisoformat(entry_date.replace('Z', '+00:00'))
                    if entry_datetime.date() == today:
                        today_entries.append(entry)
                except:
                    continue
        
        # Calculate summary
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        meals_eaten = len(today_entries)
        
        for entry in today_entries:
            nutritional = entry.get('nutritional_breakdown', {})
            total_calories += nutritional.get('estimated_calories', 0)
            total_protein += nutritional.get('protein_grams', 0)
            total_carbs += nutritional.get('carbohydrates_grams', 0)
            total_fat += nutritional.get('fat_grams', 0)
        
        # Mock recommendations (in real app, these would come from nutrition database)
        recommended_calories = 2200  # Example for pregnant woman
        calories_remaining = max(0, recommended_calories - total_calories)
        meals_remaining = max(0, 5 - meals_eaten)  # Assuming 5 meals per day
        calories_per_remaining_meal = calories_remaining // meals_remaining if meals_remaining > 0 else 0
        percentage_of_daily_needs = (total_calories / recommended_calories * 100) if recommended_calories > 0 else 0
        
        daily_summary = {
            'total_calories_today': total_calories,
            'total_protein_today': total_protein,
            'total_carbs_today': total_carbs,
            'total_fat_today': total_fat,
            'meals_eaten_today': meals_eaten
        }
        
        calorie_recommendations = {
            'recommended_daily_calories': recommended_calories,
            'calories_remaining': calories_remaining,
            'meals_remaining': meals_remaining,
            'calories_per_remaining_meal': calories_per_remaining_meal,
            'percentage_of_daily_needs': round(percentage_of_daily_needs, 1)
        }
        
        smart_tips = [
            "Stay hydrated by drinking plenty of water",
            "Include protein-rich foods in your meals",
            "Eat small, frequent meals throughout the day",
            "Focus on whole grains and fresh vegetables"
        ]
        
        print(f"✅ Daily calorie summary calculated for user: {user_id}")
        print(f"📊 Meals eaten today: {meals_eaten}")
        print(f"🔥 Total calories: {total_calories}")
        
        return jsonify({
            'success': True,
            'date': today.isoformat(),
            'daily_summary': daily_summary,
            'calorie_recommendations': calorie_recommendations,
            'smart_tips': smart_tips
        }), 200
        
    except Exception as e:
        print(f"Error getting daily calorie summary: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/analyze-nutrition', methods=['POST'])
def analyze_nutrition():
    """Analyze nutrition for food input"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        food_input = data.get('food_input', '')
        user_id = data.get('user_id')  # Get user ID to auto-fetch pregnancy week
        
        if not food_input:
            return jsonify({
                'success': False,
                'message': 'Food input is required'
            }), 400
        
        # Auto-fetch pregnancy week from patient profile
        pregnancy_week = 1  # Default fallback
        if user_id:
            try:
                # Find patient by Patient ID
                patient = db.patients_collection.find_one({"patient_id": user_id})
                if patient:
                    # First try to get pregnancy week directly from patient document
                    if 'pregnancy_week' in patient:
                        pregnancy_week = patient['pregnancy_week']
                        print(f"✅ Auto-fetched pregnancy week for nutrition analysis: {pregnancy_week}")
                    else:
                        # Try to get from patient's health data
                        health_data = patient.get('health_data', {})
                        if 'pregnancy_week' in health_data:
                            pregnancy_week = health_data['pregnancy_week']
                            print(f"✅ Auto-fetched pregnancy week from health data: {pregnancy_week}")
                        else:
                            print(f"⚠️ No pregnancy week found, using default: {pregnancy_week}")
                else:
                    print(f"⚠️ Patient not found for ID: {user_id}, using default pregnancy week: {pregnancy_week}")
            except Exception as e:
                print(f"⚠️ Error fetching pregnancy week: {e}, using default: {pregnancy_week}")
        else:
            print(f"⚠️ No user_id provided, using default pregnancy week: {pregnancy_week}")
        
        # Mock nutrition analysis (in real app, this would use AI/ML models)
        # This is a simplified example
        estimated_calories = len(food_input) * 2  # Rough estimate
        protein_grams = max(10, estimated_calories // 20)
        carbs_grams = max(20, estimated_calories // 15)
        fat_grams = max(5, estimated_calories // 25)
        fiber_grams = max(3, estimated_calories // 30)
        
        nutritional_breakdown = {
            'estimated_calories': estimated_calories,
            'protein_grams': protein_grams,
            'carbohydrates_grams': carbs_grams,
            'fat_grams': fat_grams,
            'fiber_grams': fiber_grams
        }
        
        # Mock daily calorie tracking
        daily_calorie_tracking = {
            'minimum_daily_calories': 1800,
            'recommended_daily_calories': 2200,
            'calories_contributed': estimated_calories,
            'percentage_of_daily_needs': round((estimated_calories / 2200) * 100, 1)
        }
        
        # Mock remaining calories
        remaining_calories = {
            'calories_remaining': max(0, 2200 - estimated_calories),
            'meals_remaining': 4,  # Assuming 5 meals per day
            'calories_per_remaining_meal': max(0, (2200 - estimated_calories) // 4)
        }
        
        # Mock smart tips
        smart_tips_for_today = {
            'next_meal_suggestions': 'Consider adding leafy greens for folate',
            'best_combinations': 'Pair with whole grains for sustained energy',
            'hydration_tips': 'Drink 8-10 glasses of water daily',
            'pregnancy_week_specific_advice': f'At week {pregnancy_week}, focus on iron-rich foods'
        }
        
        # Mock pregnancy benefits
        pregnancy_benefits = f"This meal provides essential nutrients for week {pregnancy_week} of pregnancy, including protein for fetal development and fiber for digestive health."
        
        # Mock safety considerations
        safety_considerations = "Ensure all foods are properly cooked and avoid raw seafood, unpasteurized dairy, and undercooked meats."
        
        # Mock portion recommendations
        portion_recommendations = f"Consider this as a moderate portion. For pregnancy week {pregnancy_week}, aim for balanced meals with adequate protein and fiber."
        
        # Mock alternative suggestions
        alternative_suggestions = "If you have food allergies, consider substituting with similar nutrient-rich alternatives. Consult your healthcare provider for personalized advice."
        
        return jsonify({
            'success': True,
            'nutritional_breakdown': nutritional_breakdown,
            'daily_calorie_tracking': daily_calorie_tracking,
            'remaining_calories': remaining_calories,
            'smart_tips_for_today': smart_tips_for_today,
            'pregnancy_benefits': pregnancy_benefits,
            'safety_considerations': safety_considerations,
            'portion_recommendations': portion_recommendations,
            'alternative_suggestions': alternative_suggestions
        }), 200
        
    except Exception as e:
        print(f"Error analyzing nutrition: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/get-patient-profile-by-email/<email>', methods=['GET'])
def get_patient_profile_by_email(email):
    """Get patient profile by email"""
    try:
        patient = db.patients_collection.find_one({"email": email})
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'}), 404
        
        profile_data = {
            'patient_id': patient.get('patient_id'),
            'username': patient.get('username'),
            'email': patient.get('email'),
            'pregnancy_week': patient.get('pregnancy_week'),
            # Add other fields as needed
        }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get-patient-profile/<patient_id>', methods=['GET'])
def get_patient_profile(patient_id):
    """Get patient profile by patient ID (same pattern as kick count)"""
    try:
        print(f"🔍 Getting patient profile for patient ID: {patient_id}")
        
        # Find patient by Patient ID (same as kick count storage)
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {patient_id}'
            }), 404
        
        # Prepare profile data (same structure as kick count)
        profile_data = {
            'patient_id': patient.get('patient_id'),
            'username': patient.get('username'),
            'email': patient.get('email'),
            'mobile': patient.get('mobile'),
            'first_name': patient.get('first_name'),
            'last_name': patient.get('last_name'),
            'age': patient.get('age'),
            'blood_type': patient.get('blood_type'),
            'date_of_birth': patient.get('date_of_birth'),
            'height': patient.get('height'),
            'weight': patient.get('weight'),
            'is_pregnant': patient.get('is_pregnant'),
            'pregnancy_week': patient.get('pregnancy_week'),
            'last_period_date': patient.get('last_period_date'),
            'expected_delivery_date': patient.get('expected_delivery_date'),
            'emergency_contact': patient.get('emergency_contact'),
            'status': patient.get('status'),
            'created_at': patient.get('created_at'),
            'last_updated': patient.get('last_updated'),
            'profile_completed_at': patient.get('profile_completed_at'),
            'email_verified': patient.get('email_verified'),
            'verified_at': patient.get('verified_at'),
            'password_updated_at': patient.get('password_updated_at'),
        }
        
        print(f"✅ Patient profile retrieved successfully for patient ID: {patient_id}")
        print(f"🆔 Patient ID: {profile_data['patient_id']}")
        print(f" Username: {profile_data['username']}")
        print(f"📧 Email: {profile_data['email']}")
        print(f"📅 Pregnancy Week: {profile_data['pregnancy_week']}")
        print(f" Expected Delivery: {profile_data['expected_delivery_date']}")
        
        return jsonify({
            'success': True,
            'profile': profile_data,
            'message': 'Patient profile retrieved successfully'
        }), 200
        
    except Exception as e:
        print(f"Error getting patient profile by patient ID: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Patient Alert System Flask API...")
    print("📱 API will be available at: http://localhost:5000")
    print("🌐 Web app can be accessed at: http://localhost:8080")
    app.run(host='0.0.0.0', port=5000, debug=True) 