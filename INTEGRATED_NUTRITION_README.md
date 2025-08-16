# Integrated Nutrition System

The nutrition system has been completely integrated into the main backend (`app_simple.py`) running on port 5000. No separate port 8000 is needed.

## 🚀 **What Changed**

- ❌ **Removed**: Separate nutrition backend on port 8000
- ✅ **Added**: All nutrition endpoints integrated into main backend
- 🔄 **Updated**: Flutter app now connects to main backend (port 5000)
- 🍎 **New**: Complete detailed food entry system with allergies, medical conditions, and dietary preferences

## 🌐 **New Endpoint Structure**

All nutrition endpoints are now available under `/nutrition/` prefix:

- **GET** `/nutrition/health` - Nutrition service health check
- **GET** `/nutrition/pregnancy-info/<patient_id>` - Get pregnancy week
- **POST** `/nutrition/save-detailed-food-entry` - Save detailed food entry
- **POST** `/nutrition/save-food-entry` - Save basic food entry
- **GET** `/nutrition/get-food-entries/<user_id>` - Get user's food entries
- **GET** `/nutrition/profile/<user_id>` - Get user profile with health data
- **POST** `/nutrition/update-pregnancy-info` - Update pregnancy information
- **POST** `/nutrition/analyze-nutrition` - Analyze food nutrition
- **GET** `/nutrition/daily-calorie-summary/<user_id>` - Get daily calorie summary

## 🎯 **How to Use**

### 1. **Start the Main Backend**
```bash
python app_simple.py
```
The service will run on **http://localhost:5000**

### 2. **Test the Nutrition Endpoints**
```bash
python test_nutrition_endpoints.py
```

### 3. **Use in Flutter App**
- Click "Add Detailed Food Entry" button
- Fill in food details, allergies, medical conditions
- Select dietary preference (veg/non-veg/vegan)
- Pregnancy week automatically fetched from backend
- Save entry - data stored in MongoDB

## 🗄️ **Database Integration**

- **Food Entries**: Stored in `food_entries` collection
- **Patient Health**: Automatically updated in `patients_v2` collection
- **Allergies & Medical Conditions**: Tracked and stored for each patient
- **Dietary Preferences**: Recorded and maintained

## 🔧 **Key Features**

### **Detailed Food Entry**
- Comprehensive food description
- Meal type selection (breakfast, lunch, dinner, snack)
- Dietary preferences (vegetarian, non-vegetarian, vegan, etc.)
- Allergy tracking (nuts, dairy, shellfish, etc.)
- Medical conditions (diabetes, heart problems, etc.)
- Pregnancy week from backend
- Additional notes

### **Backend Integration**
- All endpoints in single backend
- MongoDB integration
- Automatic patient health updates
- Comprehensive error handling
- Input validation

## 📱 **Flutter App Updates**

The Flutter app has been updated to:
- Connect to main backend (port 5000)
- Use new `/nutrition/*` endpoints
- Support detailed food entry window
- Collect comprehensive health information

## 🧪 **Testing**

Run the test script to verify all endpoints work:
```bash
python test_nutrition_endpoints.py
```

This will test:
- Main backend health
- Nutrition service health
- Pregnancy info retrieval
- Detailed food entry saving
- Food entries retrieval
- Nutrition analysis
- Daily calorie summary

## 🎉 **Benefits of Integration**

1. **Single Backend**: No need to manage multiple services
2. **Unified Database**: All data in one MongoDB instance
3. **Simplified Deployment**: One service to start and monitor
4. **Consistent API**: All endpoints follow same patterns
5. **Easier Maintenance**: Single codebase to update

## 🚨 **Important Notes**

- **No port 8000 needed**: Everything runs on port 5000
- **Database**: Uses existing `patients_db` database
- **Collections**: Creates `food_entries` collection automatically
- **Health Data**: Updates patient health data automatically
- **Backward Compatibility**: Basic food entry still supported

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Main Backend Not Running**
   ```bash
   python app_simple.py
   ```

2. **Port 5000 Already in Use**
   ```bash
   netstat -ano | findstr :5000
   taskkill /PID <process_id> /F
   ```

3. **MongoDB Connection Failed**
   - Ensure MongoDB is running
   - Check connection string in environment variables

4. **Flutter App Can't Connect**
   - Verify main backend is running on port 5000
   - Check if using correct URL (127.0.0.1:5000)

### **Logs**
Check the main backend console output for:
- ✅ Success messages
- ❌ Error messages
- 🔍 Debug information

## 🎯 **Next Steps**

1. **Start the main backend**: `python app_simple.py`
2. **Test the endpoints**: `python test_nutrition_endpoints.py`
3. **Run Flutter app**: The detailed food entry system is ready to use!

The nutrition system is now fully integrated and ready to use without any port 8000 dependencies!
