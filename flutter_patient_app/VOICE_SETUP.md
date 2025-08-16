# 🎤 Voice Recording Setup Guide

## Overview
The patient food tracking app now includes **real voice recording** with OpenAI Whisper API integration for automatic speech-to-text conversion.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
flutter pub get
```

### 2. Platform-Specific Setup

#### Android
Add these permissions to `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

#### iOS
Add these permissions to `ios/Runner/Info.plist`:
```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access to record voice for food descriptions.</string>
```

### 3. Test Voice Recording
1. Run the Flutter app
2. Navigate to Patient → Daily Log → Food & Nutrition
3. Tap "Start Voice Recording"
4. Speak your food description
5. Tap "Stop Recording"
6. Wait for transcription and nutrition analysis

## 🔧 How It Works

### Voice Recording Flow
1. **Permission Check**: App requests microphone permission
2. **Start Recording**: Audio recorded in WAV format
3. **Stop Recording**: Audio file saved temporarily
4. **Transcription**: Audio sent to Whisper API as base64
5. **Text Extraction**: Transcribed text appears in food name field
6. **Nutrition Analysis**: Text analyzed for nutrition information

### Technical Details
- **Audio Format**: WAV, 44.1kHz, 128kbps
- **Encoding**: Base64 for API transmission
- **API Endpoint**: `http://localhost:5002/transcribe`
- **Transcription Model**: OpenAI Whisper-1

## 🐛 Troubleshooting

### Common Issues

#### 1. Microphone Permission Denied
**Problem**: App can't access microphone
**Solution**: 
- Go to device Settings → Apps → Your App → Permissions
- Enable Microphone permission
- Restart the app

#### 2. Recording Not Starting
**Problem**: Voice recording button doesn't work
**Solution**:
- Check microphone permission
- Ensure device has microphone
- Restart the app

#### 3. Transcription Fails
**Problem**: Voice recorded but no text appears
**Solution**:
- Check if nutrition API is running on port 5002
- Verify OpenAI API key is set in environment
- Check internet connection

#### 4. Audio Quality Issues
**Problem**: Poor transcription accuracy
**Solution**:
- Speak clearly and slowly
- Reduce background noise
- Ensure microphone is close to mouth

### API Testing
Run the test script to verify API functionality:
```bash
python test_voice_api.py
```

## 📱 User Experience

### Recording States
- **Idle**: Blue "Start Voice Recording" button
- **Recording**: Red "Stop Recording" button with visual indicator
- **Transcribing**: Orange progress indicator
- **Complete**: Success message with transcribed text

### Visual Feedback
- **Recording Indicator**: Red microphone icon with "Recording..." text
- **Amplitude Visualization**: Real-time audio level display
- **Progress Indicators**: Clear status messages for each step

## 🔒 Security & Privacy

### Data Handling
- Audio files are **not stored permanently** on device
- Audio is **temporarily cached** during recording
- **Base64 encoding** ensures secure API transmission
- **No audio data** is stored in local database

### API Security
- OpenAI API key required for transcription
- API endpoints are **not publicly accessible**
- All requests include proper headers and validation

## 🚀 Future Enhancements

### Planned Features
1. **Offline Transcription**: Local Whisper model integration
2. **Voice Commands**: "Add apple" voice shortcuts
3. **Multi-language**: Support for different languages
4. **Audio Quality**: Adjustable recording settings
5. **Voice Profiles**: Personalized voice recognition

### Performance Optimizations
1. **Streaming Transcription**: Real-time text display
2. **Audio Compression**: Smaller file sizes
3. **Batch Processing**: Multiple food items in one recording
4. **Caching**: Store common transcriptions locally

## 📞 Support

If you encounter issues:
1. Check this troubleshooting guide
2. Verify API server is running
3. Test with the provided test script
4. Check device permissions
5. Review console logs for errors

---

**Happy Voice Recording! 🎤✨** 