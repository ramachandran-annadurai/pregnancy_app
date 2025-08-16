# Nutrition API Setup Guide

## Overview
The Patient Food Tracking feature integrates with the existing Food and Nutrition API to provide automatic nutrition analysis when patients log their food entries.

## Prerequisites
1. Python 3.7+ installed
2. The "Food and nutriance" folder from the project root

## Setup Steps

### 1. Install Dependencies
Navigate to the "Food and nutriance" folder and install requirements:
```bash
cd "Food and nutriance"
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file in the "Food and nutriance" folder:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Start the Nutrition API Server
```bash
cd "Food and nutriance"
python app.py
```

The API will start on `http://localhost:5002`

### 4. Available Endpoints
- `POST /complete-nutrition` - Complete nutrition analysis
- `POST /pregnancy-nutrition` - Pregnancy nutrition needs
- `POST /nutrition-comparison` - Nutrition comparison
- `POST /transcribe` - Audio transcription (if OpenAI key is set)

## Features Integrated

### Real Voice Recording with Whisper API
- **Microphone Integration**: Real-time voice recording using device microphone
- **Whisper Transcription**: OpenAI Whisper API converts speech to text
- **Audio Processing**: WAV format with optimal quality settings
- **Permission Handling**: Automatic microphone permission requests
- **Visual Feedback**: Recording indicators and amplitude visualization
- **Error Handling**: Graceful fallback for recording failures

### Meal Type Selection
- Breakfast, Lunch, Dinner, Snack options
- Visual selection with color-coded buttons
- Context-aware voice transcription samples

### Nutrition Analysis
- Automatic nutrition calculation using the API
- Protein, Carbs, Fat, Fiber breakdown
- Calorie estimation
- Fallback to sample data if API is unavailable

### Food Entry Management
- Add/remove food entries
- Track calories per meal
- View nutrition summary
- Historical data tracking

## API Integration Points

### 1. Nutrition Analysis
```dart
// Calls the complete-nutrition endpoint
final response = await http.post(
      Uri.parse('http://localhost:5002/complete-nutrition'),
  headers: {'Content-Type': 'application/json'},
  body: json.encode({
    'food_description': foodDescription,
    'age': 25,
    'activity_level': 'moderate',
  }),
);
```

### 2. Voice Transcription
```dart
// Real voice recording with Whisper API integration
final VoiceRecordingService _voiceService = VoiceRecordingService();

// Start recording
await _voiceService.startRecording();

// Stop recording and transcribe
String? audioFilePath = await _voiceService.stopRecording();
String? transcribedText = await _voiceService.transcribeAudio(audioFilePath);

// Update UI with transcribed text
_foodNameController.text = transcribedText ?? '';
```

## Troubleshooting

### API Connection Issues
- Ensure the nutrition API server is running on port 8000
- Check if the port is not blocked by firewall
- Verify Python dependencies are installed correctly

### Voice Recording
- **Real voice recording** is now fully integrated
- Uses `record` package for audio recording
- Uses `permission_handler` for microphone permissions
- Integrates with OpenAI Whisper API for transcription
- Audio is recorded in WAV format and sent to API as base64

### Nutrition Data
- If API is unavailable, the app falls back to sample nutrition data
- Sample data provides realistic nutrition values for demonstration

## Next Steps

1. **Real Voice Recording**: Integrate actual voice recording packages
2. **API Authentication**: Add proper authentication to the nutrition API
3. **Data Persistence**: Store nutrition data in local database
4. **Offline Mode**: Cache nutrition data for offline use
5. **Personalization**: Use patient's actual age, weight, and activity level

## File Structure
```
flutter_patient_app/
├── lib/
│   ├── screens/
│   │   ├── patient_food_tracking_screen.dart  # Main food tracking screen
│   │   └── patient_daily_log_screen.dart      # Daily log overview
│   └── utils/
│       └── constants.dart                     # API configuration
└── NUTRITION_API_SETUP.md                     # This file

Food and nutriance/
├── app.py                                     # Main nutrition API
├── complete_nutrition_analyzer.py             # Nutrition analysis logic
├── requirements.txt                           # Python dependencies
└── .env                                      # Environment variables
```

## Testing the Integration

1. Start the nutrition API server
2. Run the Flutter app
3. Navigate to Patient → Daily Log → Food & Nutrition
4. Select a meal type
5. Use voice recording (simulated)
6. Verify nutrition analysis appears
7. Add food entry and check the summary

The integration provides a seamless experience for patients to log their food using voice commands and get instant nutrition analysis! 