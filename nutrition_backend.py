from flask import Flask, request, jsonify
from flask_cors import CORS
import pymongo
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database connection
class NutritionDatabase:
    def __init__(self):
        self.client = None
        self.patients_collection = None
        self.food_entries_collection = None
        self.connect()
    
    def connect(self):
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            db_name = os.getenv("DB_NAME", "patients_db")
            
            self.client = pymongo.MongoClient(mongo_uri)
            db = self.client[db_name]
            self.patients_collection = db["patients_v2"]
            self.food_entries_collection = db["food_entries"]
            
            # Create indexes
            self.food_entries_collection.create_index("userId")
            self.food_entries_collection.create_index("timestamp")
            self.food_entries_collection.create_index("meal_type")
            
            print("✅ Connected to MongoDB successfully")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.patients_collection = None
            self.food_entries_collection = None
    
    def close(self):
        if self.client:
            self.client.close()

# Initialize database
db = NutritionDatabase()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Nutrition Backend is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/pregnancy-info/<patient_id>', methods=['GET'])
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
        
        # Extract pregnancy information
        health_data = patient.get('health_data', {})
        is_pregnant = health_data.get('is_pregnant', False)
        pregnancy_info = health_data.get('pregnancy_info', {})
        
        if is_pregnant:
            # Calculate current pregnancy week
            last_period_date = pregnancy_info.get('last_period_date')
            if last_period_date:
                try:
                    if isinstance(last_period_date, str):
                        last_period_date = datetime.fromisoformat(last_period_date.replace('Z', '+00:00'))
                    
                    weeks_pregnant = (datetime.now() - last_period_date).days // 7
                    current_week = min(weeks_pregnant, 40)  # Cap at 40 weeks
                    
                    # Determine trimester
                    if current_week <= 12:
                        trimester = "First Trimester"
                    elif current_week <= 26:
                        trimester = "Second Trimester"
                    else:
                        trimester = "Third Trimester"
                    
                    # Calculate expected delivery date
                    expected_delivery = last_period_date + datetime.timedelta(days=280)
                    
                    pregnancy_info = {
                        'current_week': current_week,
                        'trimester': trimester,
                        'expected_delivery_date': expected_delivery.strftime('%Y-%m-%d'),
                        'last_period_date': last_period_date.strftime('%Y-%m-%d')
                    }
                except Exception as e:
                    print(f"Error calculating pregnancy week: {e}")
                    pregnancy_info = {
                        'current_week': 1,
                        'trimester': "First Trimester",
                        'expected_delivery_date': None,
                        'last_period_date': None
                    }
            else:
                pregnancy_info = {
                    'current_week': 1,
                    'trimester': "First Trimester",
                    'expected_delivery_date': None,
                    'last_period_date': None
                }
        
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

@app.route('/save-detailed-food-entry', methods=['POST'])
def save_detailed_food_entry():
    """Save detailed food entry with allergies, medical conditions, and dietary preferences"""
    try:
        if db.food_entries_collection is None:
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
        
        # Validate required fields
        required_fields = ['userId', 'food_details', 'meal_type', 'pregnancy_week']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Create food entry document
        food_entry = {
            'userId': data['userId'],
            'userRole': data.get('userRole', 'patient'),
            'username': data.get('username', ''),
            'email': data.get('email', ''),
            'food_details': data['food_details'],
            'meal_type': data['meal_type'],
            'pregnancy_week': data['pregnancy_week'],
            'dietary_preference': data.get('dietary_preference', 'vegetarian'),
            'allergies': data.get('allergies', []),
            'medical_conditions': data.get('medical_conditions', []),
            'notes': data.get('notes', ''),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'created_at': datetime.now(),
            'entry_type': 'detailed'
        }
        
        # Save to database
        result = db.food_entries_collection.insert_one(food_entry)
        
        if result.inserted_id:
            print(f"✅ Detailed food entry saved successfully for user: {data['userId']}")
            
            # Also update patient's health data with allergies and medical conditions
            try:
                if db.patients_collection:
                    # Update patient's allergies and medical conditions
                    update_data = {}
                    
                    if data.get('allergies'):
                        update_data['health_data.allergies'] = data['allergies']
                    
                    if data.get('medical_conditions'):
                        update_data['health_data.medical_conditions'] = data['medical_conditions']
                    
                    if data.get('dietary_preference'):
                        update_data['health_data.dietary_preference'] = data['dietary_preference']
                    
                    if update_data:
                        update_data['last_updated'] = datetime.now()
                        db.patients_collection.update_one(
                            {"patient_id": data['userId']},
                            {"$set": update_data}
                        )
                        print(f"✅ Updated patient health data for: {data['userId']}")
            except Exception as e:
                print(f"⚠️ Warning: Could not update patient health data: {e}")
            
            return jsonify({
                'success': True,
                'message': 'Detailed food entry saved successfully',
                'entry_id': str(result.inserted_id),
                'timestamp': food_entry['timestamp']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save food entry'
            }), 500
        
    except Exception as e:
        print(f"Error saving detailed food entry: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/save-food-entry', methods=['POST'])
def save_food_entry():
    """Save basic food entry (for backward compatibility)"""
    try:
        if db.food_entries_collection is None:
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
        
        # Validate required fields
        required_fields = ['userId', 'food_details', 'meal_type', 'pregnancy_week']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Create food entry document
        food_entry = {
            'userId': data['userId'],
            'userRole': data.get('userRole', 'patient'),
            'username': data.get('username', ''),
            'email': data.get('email', ''),
            'food_details': data['food_details'],
            'meal_type': data['meal_type'],
            'pregnancy_week': data['pregnancy_week'],
            'notes': data.get('notes', ''),
            'transcribed_text': data.get('transcribed_text', ''),
            'nutritional_breakdown': data.get('nutritional_breakdown', {}),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'created_at': datetime.now(),
            'entry_type': 'basic'
        }
        
        # Save to database
        result = db.food_entries_collection.insert_one(food_entry)
        
        if result.inserted_id:
            print(f"✅ Basic food entry saved successfully for user: {data['userId']}")
            return jsonify({
                'success': True,
                'message': 'Food entry saved successfully',
                'entry_id': str(result.inserted_id),
                'timestamp': food_entry['timestamp']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save food entry'
            }), 500
        
    except Exception as e:
        print(f"Error saving food entry: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/get-food-entries/<user_id>', methods=['GET'])
def get_food_entries(user_id):
    """Get food entries for a specific user"""
    try:
        if db.food_entries_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database not available'
            }), 500
        
        # Get food entries for the user
        entries = list(db.food_entries_collection.find(
            {"userId": user_id},
            {"_id": 0}  # Exclude MongoDB _id
        ).sort("created_at", -1))  # Sort by newest first
        
        # Convert datetime objects to strings for JSON serialization
        for entry in entries:
            if 'created_at' in entry:
                entry['created_at'] = entry['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'entries': entries,
            'total_entries': len(entries)
        }), 200
        
    except Exception as e:
        print(f"Error getting food entries: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/profile/<user_id>', methods=['GET'])
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

@app.route('/update-pregnancy-info', methods=['POST'])
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

@app.route('/daily-calorie-summary/<user_id>', methods=['GET'])
def get_daily_calorie_summary(user_id):
    """Get daily calorie summary for a user"""
    try:
        if db.food_entries_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database not available'
            }), 500
        
        # Get today's date
        today = datetime.now().date()
        
        # Get food entries for today
        today_entries = list(db.food_entries_collection.find({
            "userId": user_id,
            "created_at": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lt": datetime.combine(today + datetime.timedelta(days=1), datetime.min.time())
            }
        }))
        
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
        calories_per_remaining_meal = meals_remaining > 0 ? calories_remaining // meals_remaining : 0
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

@app.route('/analyze-nutrition', methods=['POST'])
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
        pregnancy_week = data.get('pregnancy_week', 1)
        
        if not food_input:
            return jsonify({
                'success': False,
                'message': 'Food input is required'
            }), 400
        
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
        portion_recommendations = "Consider this as a moderate portion. For pregnancy week {pregnancy_week}, aim for balanced meals with adequate protein and fiber."
        
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

if __name__ == '__main__':
    print("🚀 Starting Nutrition Backend...")
    print("🍎 API will be available at: http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
