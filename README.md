# Patient Alert System

A complete patient login and management system with Flask API and web frontend.

## 🚀 Quick Start

### Option 1: Automatic Startup
```bash
python start_system.py
```

### Option 2: Manual Startup
1. Start Flask API:
   ```bash
   python app_simple.py
   ```

2. Start Frontend (in new terminal):
   ```bash
   cd simple_frontend
   python -m http.server 8080
   ```

3. Open browser: `http://localhost:8080`

## 📁 Project Structure

```
Patient Alert System/
├── app_simple.py                    # Main Flask API
├── start_system.py                  # Auto-startup script
├── requirements_flask_simple.txt    # Python dependencies
├── .env                            # Environment variables
├── simple_frontend/                # Web frontend
│   └── index.html                  # Main frontend page
├── patient_login.py                # Original CLI version
├── patient_info_collector.py       # Patient data collection
├── otp_service.py                  # Email OTP service
└── Postman_Collection_Guide.md     # API testing guide
```

## 🔧 Setup

### 1. Install Dependencies
```bash
pip install -r requirements_flask_simple.txt
```

### 2. Configure Environment
Create `.env` file with:
```
MONGO_URI=your_mongodb_connection_string
SENDER_EMAIL=your_gmail@gmail.com
SENDER_PASSWORD=your_app_password
```

### 3. Start MongoDB
Ensure MongoDB is running on your system.

## 📱 Features

### Frontend (`http://localhost:8080`)
- ✅ Modern, responsive design
- ✅ Login/Signup tabs
- ✅ OTP verification
- ✅ Patient ID generation
- ✅ Email notifications

### API (`http://localhost:5000`)
- ✅ Patient registration (OTP required)
- ✅ Email verification with OTP
- ✅ Login with Patient ID/Email
- ✅ Password reset with OTP
- ✅ Profile management
- ✅ MongoDB integration

## 🧪 Testing

### API Testing
- **Postman Collection**: `Patient_Alert_System_Flask_API.postman_collection.json`
- **Guide**: `Postman_Collection_Guide.md`

### Manual Testing
1. Open `http://localhost:8080`
2. Create new account
3. Check email for OTP
4. Verify account
5. Login with Patient ID or Email

## 🔒 Security Features

- ✅ Password hashing with bcrypt
- ✅ Email verification with OTP
- ✅ Unique Patient ID generation
- ✅ Input validation
- ✅ MongoDB injection protection

## 📊 Database Schema

### Patients Collection
```json
{
  "patient_id": "PAT12345678",
  "username": "john_doe",
  "email": "john@example.com",
  "mobile": "1234567890",
  "password_hash": "hashed_password",
  "is_verified": true,
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01",
  "blood_type": "O+",
  "is_pregnant": false,
  "pregnancy_week": null,
  "emergency_contact": {
    "name": "Jane Doe",
    "relationship": "Spouse",
    "phone": "9876543210"
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use**
   - Change ports in `app_simple.py` (line 500) and `start_system.py` (line 8080)

2. **MongoDB connection failed**
   - Check `.env` file
   - Ensure MongoDB is running

3. **Email not sending**
   - Verify Gmail credentials in `.env`
   - Enable 2FA and use App Password

4. **Frontend not loading**
   - Check if `simple_frontend/index.html` exists
   - Ensure port 8080 is available

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the Postman collection for API testing
3. Check console logs for detailed error messages

## 🎉 Success!

Your Patient Alert System is now running with:
- ✅ Clean, organized codebase
- ✅ Working Flask API
- ✅ Modern web frontend
- ✅ Complete documentation
- ✅ Easy startup script

Enjoy using your Patient Alert System! 🚀 