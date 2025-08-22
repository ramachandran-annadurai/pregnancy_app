#!/usr/bin/env python3
"""
New Simplified Nutrition Backend
Focused on reliability and simplicity
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pymongo
import os
import base64
import tempfile
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['*'], methods=['GET', 'POST', 'PUT', 'DELETE'], allow_headers=['Content-Type'])

# Database connection
class SimpleDatabase:
    def __init__(self):
        self.client = None
        self.patients_collection = None
        self.connect()
    
    def connect(self):
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            db_name = os.getenv("DB_NAME", "patients_db")
            
            self.client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            
            db = self.client[db_name]
            self.patients_collection = db["patients_v2"]
            
            print("✅ Connected to MongoDB successfully")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.patients_collection = None
    
    def close(self):
        if self.client:
            self.client.close()

# Initialize database
db = SimpleDatabase()

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Nutrition Backend is running',
        'timestamp': datetime.now().isoformat(),
        'database_connected': db.patients_collection is not None
    })

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio using Whisper AI with Tamil language support"""
    try:
        print("🎤 Transcription request received")
        
        # Get OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key not configured'
            }), 500
        
        try:
            from openai import OpenAI
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'OpenAI package not installed. Run: pip install openai'
            }), 500
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        audio_data = data.get('audio')
        language = data.get('language', 'auto')  # Default to auto-detect
        method = data.get('method', 'whisper')
        
        if not audio_data:
            return jsonify({
                'success': False,
                'message': 'No audio data provided'
            }), 400
        
        print(f"🔍 Audio data length: {len(audio_data)}")
        
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_data)
            print(f"✅ Audio decoded: {len(audio_bytes)} bytes")
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Invalid audio data: {str(e)}'
            }), 400
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
            print(f"📁 Temporary file created: {temp_file_path}")
        
        try:
            # Transcribe with Whisper
            if method == 'whisper':
                # Auto-detect language if not specified
                if language == 'auto':
                    # Try Tamil first, then English
                    try:
                        # First attempt with Tamil
                        result = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=open(temp_file_path, "rb"),
                            language="ta",  # Tamil
                            response_format="text"
                        )
                        transcription = result
                        detected_language = "ta"
                        print("🔤 Detected Tamil language")
                    except Exception as tamil_error:
                        print(f"⚠️ Tamil detection failed, trying English: {tamil_error}")
                        # Fallback to English
                        result = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=open(temp_file_path, "rb"),
                            language="en",  # English
                            response_format="text"
                        )
                        transcription = result
                        detected_language = "en"
                        print("🔤 Detected English language")
                else:
                    # Use specified language
                    result = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=open(temp_file_path, "rb"),
                        language=language,
                        response_format="text"
                    )
                    transcription = result
                    detected_language = language
                
                print(f"✅ Transcription successful: {transcription}")
                
                # If Tamil detected, provide translation info
                translation_note = ""
                if detected_language == "ta":
                    translation_note = " (Tamil detected - will be translated to English in the app)"
                
                return jsonify({
                    'success': True,
                    'transcription': transcription,
                    'language': detected_language,
                    'method': method,
                    'translation_note': translation_note,
                    'timestamp': datetime.now().isoformat()
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': f'Unsupported method: {method}'
                }), 400
                
        except Exception as e:
            print(f"❌ Error in transcription: {e}")
            return jsonify({
                'success': False,
                'message': f'Transcription failed: {str(e)}'
            }), 500
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
                print(f"🧹 Temporary file cleaned up: {temp_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to clean up temp file: {cleanup_error}")
                
    except Exception as e:
        print(f"❌ Error in transcription: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/analyze-with-gpt4', methods=['POST'])
def analyze_food_with_gpt4():
    """Analyze food using GPT-4"""
    try:
        print("🍎 GPT-4 analysis request received")
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        food_input = data.get('food_input', '')
        pregnancy_week = data.get('pregnancy_week', 1)
        user_id = data.get('userId', '')
        
        if not food_input:
            return jsonify({
                'success': False,
                'message': 'Food input is required'
            }), 400
        
        # Get OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key not configured'
            }), 500
        
        try:
            from openai import OpenAI
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'OpenAI package not installed. Run: pip install openai'
            }), 500
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Create GPT-4 prompt
        prompt = f"""
        Analyze this food item for a pregnant woman at week {pregnancy_week}:
        
        Food: {food_input}
        
        Provide a detailed analysis in JSON format with the following structure:
        {{
            "nutritional_breakdown": {{
                "estimated_calories": <number>,
                "protein_grams": <number>,
                "carbohydrates_grams": <number>,
                "fat_grams": <number>,
                "fiber_grams": <number>
            }},
            "pregnancy_benefits": {{
                "nutrients_for_fetal_development": ["list of specific nutrients"],
                "benefits_for_mother": ["list of benefits"],
                "week_specific_advice": "specific advice for week {pregnancy_week}"
            }},
            "safety_considerations": {{
                "food_safety_tips": ["list of safety tips"],
                "cooking_recommendations": ["cooking guidelines"]
            }},
            "smart_recommendations": {{
                "next_meal_suggestions": ["suggestions for next meal"],
                "hydration_tips": "water intake advice"
            }}
        }}
        
        Focus on pregnancy-specific nutrition needs.
        """
        
        # Call GPT-4
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a nutrition expert specializing in pregnancy nutrition. Provide accurate, detailed analysis in the exact JSON format requested."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        # Extract response
        gpt_response = response.choices[0].message.content
        print(f"✅ GPT-4 response received: {len(gpt_response)} characters")
        print(f"🔍 Raw GPT response: {gpt_response[:200]}...")
        
        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = gpt_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            # Parse JSON response
            analysis_data = json.loads(cleaned_response)
            print(f"✅ JSON parsed successfully")
            
            # Store in database if user_id provided
            if user_id and db.patients_collection is not None:
                food_data_entry = {
                    'food_input': food_input,
                    'pregnancy_week': pregnancy_week,
                    'gpt4_analysis': analysis_data,
                    'timestamp': datetime.now().isoformat(),
                    'created_at': datetime.now(),
                    'entry_type': 'gpt4_analyzed',
                    'meal_type': 'analyzed',
                    'analysis_status': 'success'
                }
                
                result = db.patients_collection.update_one(
                    {"patient_id": user_id},
                    {
                        "$push": {"food_data": food_data_entry},
                        "$set": {"last_updated": datetime.now()}
                    }
                )
                
                if result.modified_count > 0:
                    print(f"✅ Analysis stored for user: {user_id}")
                else:
                    print(f"⚠️ User not found: {user_id}")
            
            return jsonify({
                'success': True,
                'message': 'GPT-4 analysis completed successfully',
                'analysis': analysis_data,
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"🔍 Failed to parse: {cleaned_response[:300]}...")
            
            # Create a more robust fallback analysis
            fallback_analysis = {
                'nutritional_breakdown': {
                    'estimated_calories': max(100, len(food_input) * 15),
                    'protein_grams': max(8, len(food_input) * 2),
                    'carbohydrates_grams': max(25, len(food_input) * 3),
                    'fat_grams': max(5, len(food_input)),
                    'fiber_grams': max(3, len(food_input))
                },
                'pregnancy_benefits': {
                    'nutrients_for_fetal_development': ['vitamins', 'minerals', 'protein'],
                    'benefits_for_mother': ['energy', 'nutrients', 'satisfaction'],
                    'week_specific_advice': f'At week {pregnancy_week}, focus on balanced nutrition with {food_input}'
                },
                'safety_considerations': {
                    'food_safety_tips': ['wash thoroughly', 'cook properly', 'store safely'],
                    'cooking_recommendations': ['ensure proper cooking', 'avoid raw consumption']
                },
                'smart_recommendations': {
                    'next_meal_suggestions': ['balanced meal', 'include vegetables', 'stay hydrated'],
                    'hydration_tips': 'Drink 8-10 glasses of water daily'
                },
                'analysis_note': 'Fallback analysis due to parsing error'
            }
            
            # Store fallback analysis in database
            if user_id and db.patients_collection is not None:
                food_data_entry = {
                    'food_input': food_input,
                    'pregnancy_week': pregnancy_week,
                    'gpt4_analysis': fallback_analysis,
                    'timestamp': datetime.now().isoformat(),
                    'created_at': datetime.now(),
                    'entry_type': 'gpt4_analyzed_fallback',
                    'meal_type': 'analyzed',
                    'analysis_status': 'fallback',
                    'original_response': gpt_response[:500]  # Store first 500 chars for debugging
                }
                
                result = db.patients_collection.update_one(
                    {"patient_id": user_id},
                    {
                        "$push": {"food_data": food_data_entry},
                        "$set": {"last_updated": datetime.now()}
                    }
                )
                
                if result.modified_count > 0:
                    print(f"✅ Fallback analysis stored for user: {user_id}")
                else:
                    print(f"⚠️ User not found: {user_id}")
            
            return jsonify({
                'success': True,
                'message': 'Analysis completed with fallback data due to parsing error',
                'analysis': fallback_analysis,
                'timestamp': datetime.now().isoformat(),
                'note': 'Fallback analysis used due to GPT-4 response parsing issue'
            }), 200
        
    except Exception as e:
        print(f"❌ Error in GPT-4 analysis: {e}")
        return jsonify({
            'success': False,
            'message': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/nutrition/save-food-entry', methods=['POST'])
def save_food_entry():
    """Save basic food entry"""
    try:
        print("🍽️ Food entry save request received")
        
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
        
        # Validate required fields
        required_fields = ['userId', 'food_details', 'meal_type', 'pregnancy_week']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Create food entry
        food_entry = {
            'food_details': data['food_details'],
            'meal_type': data['meal_type'],
            'pregnancy_week': data['pregnancy_week'],
            'notes': data.get('notes', ''),
            'transcribed_text': data.get('transcribed_text', ''),
            'nutritional_breakdown': data.get('nutritional_breakdown', {}),
            'gpt4_analysis': data.get('gpt4_analysis', None),
            'timestamp': datetime.now().isoformat(),
            'created_at': datetime.now(),
            'entry_type': 'basic',
            'analysis_status': 'basic_entry'
        }
        
        # Save to database
        result = db.patients_collection.update_one(
            {"patient_id": data['userId']},
            {
                "$push": {"food_data": food_entry},
                "$set": {"last_updated": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Food entry saved for user: {data['userId']}")
            return jsonify({
                'success': True,
                'message': 'Food entry saved successfully',
                'entry_id': f"entry_{datetime.now().timestamp()}",
                'timestamp': food_entry['timestamp']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'User not found or failed to save'
            }), 500
        
    except Exception as e:
        print(f"❌ Error saving food entry: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/get-food-entries/<user_id>', methods=['GET'])
def get_food_entries(user_id):
    """Get food entries for a user"""
    try:
        if db.patients_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database not available'
            }), 500
        
        # Find patient
        patient = db.patients_collection.find_one({"patient_id": user_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get food data
        food_data = patient.get('food_data', [])
        
        # Count different types of entries
        entry_counts = {
            'total_entries': len(food_data),
            'basic_entries': len([e for e in food_data if e.get('entry_type') == 'basic']),
            'gpt4_analyzed': len([e for e in food_data if e.get('entry_type') == 'gpt4_analyzed']),
            'gpt4_fallback': len([e for e in food_data if e.get('entry_type') == 'gpt4_analyzed_fallback'])
        }
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'entry_counts': entry_counts,
            'food_data': food_data,
            'total_entries': len(food_data)
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting food entries: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/debug-food-data/<user_id>', methods=['GET'])
def debug_food_data(user_id):
    """Debug endpoint to view food data structure"""
    try:
        if db.patients_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database not available'
            }), 500
        
        # Find patient
        patient = db.patients_collection.find_one({"patient_id": user_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get food data
        food_data = patient.get('food_data', [])
        
        # Analyze structure
        structure_analysis = {
            'total_entries': len(food_data),
            'entry_types': {},
            'analysis_statuses': {},
            'sample_entries': []
        }
        
        for entry in food_data:
            entry_type = entry.get('entry_type', 'unknown')
            analysis_status = entry.get('analysis_status', 'unknown')
            
            structure_analysis['entry_types'][entry_type] = structure_analysis['entry_types'].get(entry_type, 0) + 1
            structure_analysis['analysis_statuses'][analysis_status] = structure_analysis['analysis_statuses'].get(analysis_status, 0) + 1
            
            # Store sample entries (first 3 of each type)
            if entry_type not in [e['entry_type'] for e in structure_analysis['sample_entries'] if e['entry_type'] == entry_type]:
                structure_analysis['sample_entries'].append({
                    'entry_type': entry_type,
                    'timestamp': entry.get('timestamp'),
                    'food_details': entry.get('food_details', entry.get('food_input', 'N/A')),
                    'has_gpt4_analysis': 'gpt4_analysis' in entry and entry['gpt4_analysis'] is not None
                })
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'structure_analysis': structure_analysis,
            'raw_food_data': food_data
        }), 200
        
    except Exception as e:
        print(f"❌ Error debugging food data: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting NEW Nutrition Backend...")
    print("🍎 API will be available at: http://127.0.0.1:8001")
    print("🔧 Database connected:", db.patients_collection is not None)
    
    try:
        # Simple Flask configuration
        app.run(
            host='127.0.0.1',
            port=8002,
            debug=False,
            threaded=True,
            use_reloader=False  # Disable auto-reload to prevent issues
        )
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        print("🔄 Trying alternative configuration...")
        try:
            app.run(host='localhost', port=8002, debug=False)
        except Exception as e2:
            print(f"❌ Alternative configuration failed: {e2}")
            print("💡 Please check if port 8002 is available")
