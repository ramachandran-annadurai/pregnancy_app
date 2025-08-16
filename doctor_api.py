from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['patients_db']

# Separate collections for patients and doctors
patients_collection = db['patients_v2']
doctors_collection = db['doctor_v2']

# Import bcrypt for password hashing
import bcrypt

# OTP Functions
def generate_otp():
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP via email. For now, just print to console."""
    try:
        # In production, implement actual email sending
        print(f"📧 OTP {otp} sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send OTP email: {e}")
        return False

def store_otp(email, otp, purpose):
    """Store OTP in doctor_v2 collection with expiration."""
    try:
        # Remove any existing OTPs for this email and purpose
        doctors_collection.delete_many({'email': email, 'otp_purpose': purpose})
        
        # Store new OTP with 10-minute expiration in doctor_v2 collection
        otp_doc = {
            'email': email,
            'otp': otp,
            'otp_purpose': purpose,  # 'signup' or 'password_reset'
            'otp_created_at': datetime.utcnow(),
            'otp_expires_at': datetime.utcnow() + timedelta(minutes=10),
            'is_otp_document': True  # Flag to identify OTP documents
        }
        
        doctors_collection.insert_one(otp_doc)
        return True
    except Exception as e:
        print(f"❌ Failed to store OTP: {e}")
        return False

def verify_otp(email, otp, purpose):
    """Verify OTP from doctor_v2 collection."""
    try:
        print(f"🔍 Verifying OTP for email: {email}, purpose: {purpose}")
        
        # Find OTP document in doctor_v2 collection
        otp_doc = doctors_collection.find_one({
            'email': email,
            'otp': otp,
            'otp_purpose': purpose,
            'is_otp_document': True
        })
        
        print(f"📄 OTP document found: {otp_doc is not None}")
        if otp_doc:
            print(f"📋 OTP document keys: {list(otp_doc.keys())}")
            print(f"⏰ OTP expires at: {otp_doc.get('otp_expires_at')}")
            print(f"🕐 Current time: {datetime.utcnow()}")
        
        if not otp_doc:
            return False, "OTP not found"
        
        # Check if OTP has expired
        if datetime.utcnow() > otp_doc['otp_expires_at']:
            print(f"⏰ OTP expired, removing...")
            # Remove expired OTP
            doctors_collection.delete_one({'_id': otp_doc['_id']})
            return False, "OTP has expired"
        
        print(f"✅ OTP verified successfully")
        # Return success without deleting - let the calling endpoint handle cleanup
        return True, "OTP verified successfully"
        
    except Exception as e:
        print(f"❌ Error verifying OTP: {e}")
        return False, "Error verifying OTP"

@app.route('/doctor-signup', methods=['POST'])
def doctor_signup():
    try:
        data = request.get_json()
        
        # Extract doctor signup data
        username = data.get('username')
        email = data.get('email')
        mobile = data.get('mobile')
        password = data.get('password')
        role = data.get('role', 'doctor')
        
        # Validate required fields
        if not all([username, email, mobile, password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if email already exists
        existing_doctor = doctors_collection.find_one({'email': email})
        if existing_doctor:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Check if username already exists
        existing_username = doctors_collection.find_one({'username': username})
        if existing_doctor:
            return jsonify({'error': 'Username already exists'}), 400
        
        # Check if mobile already exists
        existing_mobile = doctors_collection.find_one({'mobile': mobile})
        if existing_mobile:
            return jsonify({'error': 'Mobile number already exists'}), 400
        
        # Store signup data temporarily in doctor_v2 collection
        temp_signup_data = {
            'username': username,
            'email': email,
            'mobile': mobile,
            'password': password,
            'role': role,
            'created_at': datetime.utcnow()
        }
        
        # Generate and send OTP
        otp = generate_otp()
        print(f"🔐 Generated OTP: {otp} for email: {email}")
        
        if send_otp_email(email, otp):
            # Store OTP and signup data in doctor_v2 collection
            otp_document = {
                'email': email,
                'otp': otp,
                'otp_purpose': 'signup',
                'signup_data': temp_signup_data,
                'otp_created_at': datetime.utcnow(),
                'otp_expires_at': datetime.utcnow() + timedelta(minutes=10),
                'is_otp_document': True
            }
            
            print(f"💾 Storing OTP document: {otp_document}")
            result = doctors_collection.insert_one(otp_document)
            print(f"✅ OTP document stored with ID: {result.inserted_id}")
            
            return jsonify({
                'success': True,
                'message': 'OTP sent to your email. Please verify to complete signup.',
                'email': email
            }), 200
        else:
            return jsonify({'error': 'Failed to send OTP'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctor-login', methods=['POST'])
def doctor_login():
    try:
        data = request.get_json()
        
        login_identifier = data.get('login_identifier')
        password = data.get('password')
        role = data.get('role', 'doctor')
        
        if not all([login_identifier, password]):
            return jsonify({'error': 'Missing login credentials'}), 400
        
        # Find doctor by email
        doctor = doctors_collection.find_one({'email': login_identifier})
        
        if not doctor:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        stored_hash = doctor['password_hash']
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate a simple token (you can implement JWT here)
        token = f"doctor_token_{doctor['_id']}"
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'doctor_id': str(doctor['_id']),
            'username': doctor['username'],
            'email': doctor['email'],
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctor-verify-otp', methods=['POST'])
def doctor_verify_otp():
    try:
        data = request.get_json()
        
        email = data.get('email')
        otp = data.get('otp')
        role = data.get('role', 'doctor')
        
        if not all([email, otp]):
            return jsonify({'error': 'Missing email or OTP'}), 400
        
        # Verify OTP
        is_valid, message = verify_otp(email, otp, 'signup')
        
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Get signup data from doctor_v2 collection
        print(f"🔍 Looking for OTP document for email: {email}")
        otp_doc = doctors_collection.find_one({
            'email': email,
            'otp_purpose': 'signup',
            'is_otp_document': True
        })
        
        print(f"📄 OTP document found: {otp_doc is not None}")
        if otp_doc:
            print(f"📋 OTP document keys: {list(otp_doc.keys())}")
            print(f"📝 Has signup_data: {'signup_data' in otp_doc}")
        
        if not otp_doc or 'signup_data' not in otp_doc:
            return jsonify({'error': 'Signup data not found'}), 400
        
        signup_data = otp_doc['signup_data']
        
        # Hash password and create doctor account
        hashed_password = bcrypt.hashpw(signup_data['password'].encode('utf-8'), bcrypt.gensalt())
        
        doctor_doc = {
            'username': signup_data['username'],
            'email': signup_data['email'],
            'mobile': signup_data['mobile'],
            'password_hash': hashed_password,
            'role': signup_data['role'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert doctor into doctors collection
        result = doctors_collection.insert_one(doctor_doc)
        
        if result.inserted_id:
            # Clean up OTP data from doctor_v2 collection
            doctors_collection.delete_one({'_id': otp_doc['_id']})
            
            # Generate token
            token = f"doctor_token_{result.inserted_id}"
            
            return jsonify({
                'success': True,
                'message': 'Doctor account created successfully',
                'doctor_id': str(result.inserted_id),
                'username': signup_data['username'],
                'email': signup_data['email'],
                'token': token
            }), 201
        else:
            return jsonify({'error': 'Failed to create doctor account'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctor-send-otp', methods=['POST'])
def doctor_send_otp():
    try:
        data = request.get_json()
        
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Find doctor by email
        doctor = doctors_collection.find_one({'email': email})
        
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404
        
        # For now, just return success (you can implement actual OTP sending)
        return jsonify({
            'success': True,
            'message': 'OTP sent successfully',
            'email': email
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctor-forgot-password', methods=['POST'])
def doctor_forgot_password():
    try:
        data = request.get_json()
        
        login_identifier = data.get('login_identifier')
        
        if not login_identifier:
            return jsonify({'error': 'Login identifier is required'}), 400
        
        # Find doctor by email
        doctor = doctors_collection.find_one({'email': login_identifier})
        
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404
        
        # Generate and send OTP for password reset
        otp = generate_otp()
        if send_otp_email(doctor['email'], otp):
            # Store OTP for password reset
            store_otp(doctor['email'], otp, 'password_reset')
            
            return jsonify({
                'success': True,
                'message': 'OTP sent to your email for password reset',
                'email': doctor['email']
            }), 200
        else:
            return jsonify({'error': 'Failed to send OTP'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctor-reset-password', methods=['POST'])
def doctor_reset_password():
    try:
        data = request.get_json()
        
        email = data.get('email')
        otp = data.get('otp')
        new_password = data.get('new_password')
        
        if not all([email, otp, new_password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Find doctor by email
        doctor = doctors_collection.find_one({'email': email})
        
        if not doctor:
            return jsonify({'error': 'Doctor not found'}), 404
        
        # Verify OTP for password reset
        is_valid, message = verify_otp(email, otp, 'password_reset')
        
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update password
        result = doctors_collection.update_one(
            {'email': email},
            {'$set': {'password_hash': hashed_password, 'updated_at': datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            # Clean up OTP document after successful password reset
            doctors_collection.delete_many({
                'email': email,
                'otp_purpose': 'password_reset',
                'is_otp_document': True
            })
            
            return jsonify({
                'success': True,
                'message': 'Password reset successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to reset password'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/complete-doctor-profile', methods=['POST'])
def complete_doctor_profile():
    try:
        data = request.get_json()
        
        # Extract doctor profile data
        doctor_profile = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'qualification': data.get('qualification'),
            'specialization': data.get('specialization'),
            'working_hospital': data.get('working_hospital'),
            'doctor_id': data.get('doctor_id'),
            'license_number': data.get('license_number'),
            'phone': data.get('phone'),
            'address': data.get('address'),
            'city': data.get('city'),
            'state': data.get('state'),
            'zip_code': data.get('zip_code'),
            'experience_years': data.get('experience_years'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'qualification', 'specialization', 
                         'working_hospital', 'doctor_id', 'license_number']
        
        for field in required_fields:
            if not doctor_profile[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if doctor ID already exists
        existing_doctor = doctors_collection.find_one({'doctor_id': doctor_profile['doctor_id']})
        if existing_doctor:
            return jsonify({'error': 'Doctor ID already exists'}), 400
        
        # Check if license number already exists
        existing_license = doctors_collection.find_one({'license_number': doctor_profile['license_number']})
        if existing_license:
            return jsonify({'error': 'License number already exists'}), 400
        
        # Insert doctor profile into doctors collection
        result = doctors_collection.insert_one(doctor_profile)
        
        if result.inserted_id:
            return jsonify({
                'success': True,
                'message': 'Doctor profile completed successfully',
                'doctor_id': str(result.inserted_id)
            }), 201
        else:
            return jsonify({'error': 'Failed to create doctor profile'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctor-profile/<doctor_id>', methods=['GET'])
def get_doctor_profile(doctor_id):
    try:
        # Try to find by ObjectId first
        try:
            doctor = doctors_collection.find_one({'_id': ObjectId(doctor_id)})
        except:
            # If not ObjectId, try to find by doctor_id field
            doctor = doctors_collection.find_one({'doctor_id': doctor_id})
        
        if doctor:
            # Convert ObjectId to string for JSON serialization
            doctor['_id'] = str(doctor['_id'])
            return jsonify(doctor), 200
        else:
            return jsonify({'error': 'Doctor profile not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctors', methods=['GET'])
def get_all_doctors():
    try:
        doctors = list(doctors_collection.find({}))
        
        # Convert ObjectIds to strings
        for doctor in doctors:
            doctor['_id'] = str(doctor['_id'])
        
        return jsonify(doctors), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctor-profile/<doctor_id>', methods=['PUT'])
def update_doctor_profile(doctor_id):
    try:
        data = request.get_json()
        
        # Update timestamp
        data['updated_at'] = datetime.utcnow()
        
        # Try to find by ObjectId first
        try:
            result = doctors_collection.update_one(
                {'_id': ObjectId(doctor_id)},
                {'$set': data}
            )
        except:
            # If not ObjectId, try to update by doctor_id field
            result = doctors_collection.update_one(
                {'doctor_id': doctor_id},
                {'$set': data}
            )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Doctor profile updated successfully'}), 200
        else:
            return jsonify({'error': 'Doctor profile not found or no changes made'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/doctor-profile/<doctor_id>', methods=['DELETE'])
def delete_doctor_profile(doctor_id):
    try:
        # Try to find by ObjectId first
        try:
            result = doctors_collection.delete_one({'_id': ObjectId(doctor_id)})
        except:
            # If not ObjectId, try to delete by doctor_id field
            result = doctors_collection.delete_one({'doctor_id': doctor_id})
        
        if result.deleted_count > 0:
            return jsonify({'success': True, 'message': 'Doctor profile deleted successfully'}), 200
        else:
            return jsonify({'error': 'Doctor profile not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Doctor API Server Starting...")
    print("📊 MongoDB Collections:")
    print(f"   - Patients: {patients_collection.name}")
    print(f"   - Doctors: {doctors_collection.name}")
    print("🔗 API Endpoints:")
    print("   - POST /doctor-signup")
    print("   - POST /doctor-login")
    print("   - POST /doctor-verify-otp")
    print("   - POST /doctor-send-otp")
    print("   - POST /doctor-forgot-password")
    print("   - POST /doctor-reset-password")
    print("   - POST /complete-doctor-profile")
    print("   - GET  /doctor-profile/<doctor_id>")
    print("   - GET  /doctors")
    print("   - PUT  /doctor-profile/<doctor_id>")
    print("   - DELETE /doctor-profile/<doctor_id>")
    print("🌐 Server running on http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 