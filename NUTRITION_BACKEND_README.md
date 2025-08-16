# Nutrition Backend with Detailed Food Entry System

This system provides a comprehensive food tracking solution for pregnant patients, including detailed information about allergies, medical conditions, and dietary preferences.

## Features

### 🍎 Detailed Food Entry
- **Food Details**: Comprehensive description of meals
- **Allergies**: Track food allergies (nuts, dairy, etc.)
- **Medical Conditions**: Record conditions like diabetes, heart problems
- **Dietary Preferences**: Vegetarian, non-vegetarian, vegan, etc.
- **Pregnancy Week**: Automatically fetched from backend
- **Meal Types**: Breakfast, lunch, dinner, snack

### 🔄 Backend Integration
- **MongoDB Storage**: All data stored in `food_entries` collection
- **Patient Health Updates**: Automatically updates patient's health data
- **Pregnancy Info**: Fetches current pregnancy week from database
- **API Endpoints**: RESTful API for all operations

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements_nutrition.txt
```

### 2. Start the Nutrition Backend
```bash
python start_nutrition_backend.py
```

Or manually:
```bash
python nutrition_backend.py
```

The service will run on **http://localhost:8000**

### 3. Flutter App Configuration
The Flutter app is already configured to connect to:
- **Nutrition Backend**: `http://127.0.0.1:8000`

## API Endpoints

### Health Check
- **GET** `/health` - Service health status

### Pregnancy Information
- **GET** `/pregnancy-info/<patient_id>` - Get current pregnancy week

### Food Entries
- **POST** `/save-detailed-food-entry` - Save detailed food entry
- **POST** `/save-food-entry` - Save basic food entry (backward compatibility)
- **GET** `/get-food-entries/<user_id>` - Get user's food entries

### User Profile
- **GET** `/profile/<user_id>` - Get user profile with health data
- **POST** `/update-pregnancy-info` - Update pregnancy information

### Nutrition Analysis
- **POST** `/analyze-nutrition` - Analyze food nutrition
- **GET** `/daily-calorie-summary/<user_id>` - Get daily calorie summary

## Database Schema

### Food Entries Collection
```json
{
  "userId": "PAT123456",
  "userRole": "patient",
  "username": "John Doe",
  "email": "john@example.com",
  "food_details": "Grilled chicken with vegetables",
  "meal_type": "lunch",
  "pregnancy_week": 12,
  "dietary_preference": "non-vegetarian",
  "allergies": ["nuts", "shellfish"],
  "medical_conditions": ["diabetes", "hypertension"],
  "notes": "Felt good after this meal",
  "timestamp": "2024-01-15T12:00:00Z",
  "created_at": "2024-01-15T12:00:00Z",
  "entry_type": "detailed"
}
```

### Patient Health Data Updates
The system automatically updates the patient's health data in the `patients_v2` collection:
- `health_data.allergies` - List of food allergies
- `health_data.medical_conditions` - List of medical conditions
- `health_data.dietary_preference` - Dietary preference

## Flutter App Usage

### 1. Open Detailed Food Entry
- Click the **"Add Detailed Food Entry"** button in the food tracking screen
- This opens a new window with comprehensive food entry form

### 2. Fill in Details
- **Food Details**: Describe what you ate
- **Meal Type**: Select breakfast, lunch, dinner, or snack
- **Dietary Preference**: Choose from vegetarian, non-vegetarian, vegan, etc.
- **Allergies**: Add food allergies (e.g., nuts, dairy)
- **Medical Conditions**: Add conditions (e.g., diabetes, heart problem)
- **Additional Notes**: Any extra information

### 3. Pregnancy Week
- Automatically fetched from backend
- Can be refreshed with the refresh button
- Shows current week with visual indicator

### 4. Save Entry
- Click **"Save Detailed Food Entry"**
- Data is sent to backend and stored in MongoDB
- Patient's health data is automatically updated
- Returns to main food tracking screen

## Error Handling

The system includes comprehensive error handling:
- **Database Connection**: Graceful fallback if MongoDB is unavailable
- **Validation**: Required field validation for all endpoints
- **User Feedback**: Clear error messages and success notifications
- **Logging**: Detailed logging for debugging

## Security Features

- **Input Validation**: All inputs are validated and sanitized
- **Database Indexes**: Optimized queries with proper indexing
- **Error Logging**: Secure error logging without exposing sensitive data

## Troubleshooting

### Common Issues

1. **Port 8000 Already in Use**
   ```bash
   # Find process using port 8000
   netstat -ano | findstr :8000
   # Kill the process
   taskkill /PID <process_id> /F
   ```

2. **MongoDB Connection Failed**
   - Ensure MongoDB is running
   - Check connection string in environment variables
   - Verify database name and collection access

3. **Flutter App Can't Connect**
   - Verify nutrition backend is running on port 8000
   - Check if using correct URL (127.0.0.1 vs localhost)
   - Ensure CORS is properly configured

### Logs
Check the console output for:
- ✅ Success messages
- ❌ Error messages
- 🔍 Debug information

## Future Enhancements

- **AI Nutrition Analysis**: Integration with GPT-4 for detailed nutrition insights
- **Food Image Recognition**: Photo-based food identification
- **Barcode Scanning**: Scan food packages for nutrition info
- **Meal Planning**: AI-powered meal suggestions
- **Health Alerts**: Notifications for dietary restrictions

## Support

For issues or questions:
1. Check the console logs for error messages
2. Verify all services are running
3. Check database connectivity
4. Review API endpoint responses
