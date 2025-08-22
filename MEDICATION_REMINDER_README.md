# Medication Reminder System

## Overview
The Medication Reminder System automatically sends email alerts to patients when it's time to take their medication. It runs in the background and checks for upcoming dosages every 15 minutes.

## Features

### 🔔 Automatic Email Reminders
- **Scheduled Checks**: Runs every 15 minutes in the background
- **Smart Timing**: Sends reminders within 15 minutes of scheduled dose time
- **Personalized Content**: Includes medication name, dosage, time, and special instructions
- **User-Friendly**: Sends to the patient's registered email address

### 📧 Email Content
Each reminder email includes:
- Patient's name
- Medication name
- Dosage amount
- Scheduled time
- Frequency
- Special instructions (if any)
- Professional medical disclaimer

### 🚀 API Endpoints

#### 1. Send Reminders to All Patients
```http
POST /medication/send-reminders
```
**Purpose**: Manually trigger medication reminder check for all patients
**Response**: Number of reminders sent

#### 2. Test Reminder for Specific Patient
```http
POST /medication/test-reminder/<patient_id>
```
**Purpose**: Send a test reminder email to verify functionality
**Response**: Confirmation of email sent

#### 3. Get Upcoming Dosages
```http
GET /medication/get-upcoming-dosages/<patient_id>
```
**Purpose**: Retrieve upcoming medication schedule for a patient
**Response**: List of upcoming dosages with timing information

## How It Works

### 1. Background Scheduler
- Starts automatically when the Flask app launches
- Runs in a daemon thread (doesn't block the main application)
- Checks every 15 minutes for medications due within the next 15 minutes

### 2. Medication Detection
- Scans all patient records in the database
- Looks for medications with `reminder_enabled: true`
- Calculates time differences to determine when to send reminders

### 3. Email Delivery
- Uses existing Gmail SMTP configuration
- Sends personalized emails to each patient
- Includes all relevant medication information

## Configuration

### Environment Variables Required
```bash
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

### Database Structure
The system expects medication data in this format:
```json
{
  "medication_logs": [
    {
      "medication_name": "Iron",
      "dosages": [
        {
          "dosage": "500mg",
          "time": "09:00",
          "frequency": "Twice daily",
          "reminder_enabled": true,
          "special_instructions": "Take with food"
        }
      ]
    }
  ]
}
```

## Testing

### 1. Test All Reminders
```bash
curl -X POST http://127.0.0.1:5000/medication/send-reminders
```

### 2. Test Specific Patient
```bash
curl -X POST http://127.0.0.1:5000/medication/test-reminder/PATIENT_ID
```

### 3. Run Test Script
```bash
python test_medication_reminder.py
```

## Troubleshooting

### Common Issues

#### 1. Emails Not Sending
- Check Gmail SMTP credentials in environment variables
- Verify Gmail 2-factor authentication is enabled
- Use App Password instead of regular password

#### 2. Scheduler Not Running
- Check Flask app logs for scheduler startup messages
- Verify the scheduler thread is running in background
- Restart the Flask application

#### 3. Wrong Timing
- Ensure medication times are in 24-hour format (HH:MM)
- Check timezone settings on the server
- Verify `reminder_enabled` is set to `true`

### Log Messages
The system provides detailed logging:
- `⏰ Medication reminder scheduler running...`
- `🔍 Checking for medication reminders...`
- `✅ Medication reminder sent to email@example.com for Medication at 09:00`
- `❌ Failed to send medication reminder to email@example.com`

## Security Considerations

### Email Privacy
- Patient emails are stored securely in the database
- SMTP credentials are stored as environment variables
- No sensitive medical information in email subjects

### Rate Limiting
- Reminders are sent only when due (within 15 minutes)
- No spam or excessive email sending
- Background scheduler prevents overwhelming the system

## Future Enhancements

### Planned Features
- **SMS Reminders**: Add text message support
- **Push Notifications**: Mobile app notifications
- **Customizable Timing**: Patient-defined reminder windows
- **Reminder History**: Track sent reminders to avoid duplicates
- **Escalation**: Notify caregivers if medication is missed

### Integration Points
- **Calendar Apps**: Google Calendar, Outlook integration
- **Smart Devices**: Alexa, Google Home reminders
- **Wearables**: Apple Watch, Fitbit notifications

## Support

For technical support or questions about the medication reminder system:
1. Check the Flask application logs
2. Verify environment variable configuration
3. Test individual endpoints using the test script
4. Ensure the backend is running and accessible

---

**Note**: This system is designed for medical applications. Always ensure compliance with healthcare regulations and patient privacy requirements.
