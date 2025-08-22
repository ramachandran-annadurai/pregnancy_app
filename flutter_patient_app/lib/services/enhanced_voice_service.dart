import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:html' as html;
import '../utils/constants.dart';

class EnhancedVoiceService {
  html.MediaRecorder? _mediaRecorder;
  List<html.Blob> _audioChunks = [];
  bool _isRecording = false;
  String _workingBackendUrl = '';
  String _googleApiKey = '';

  bool get isSupported {
    return html.window.navigator.mediaDevices != null &&
           html.MediaRecorder != null;
  }

  Future<bool> startRecording() async {
    try {
      if (!isSupported) {
        print('❌ MediaRecorder not supported in this browser');
        return false;
      }
      print('🎤 Starting voice recording...');
      
      final stream = await html.window.navigator.mediaDevices!.getUserMedia({
        'audio': {
          'sampleRate': 44100, // Higher sample rate for better quality
          'channelCount': 1,
          'echoCancellation': true,
          'noiseSuppression': true,
          'autoGainControl': true,
          'latency': 0.01, // Lower latency for better responsiveness
        }
      });
      
      // Try to use WebM with Opus codec for best compatibility
      String mimeType = 'audio/webm;codecs=opus';
      if (!html.MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm';
        if (!html.MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = 'audio/mp4';
        }
      }
      
      print('🎤 Using MIME type: $mimeType');
      
      _mediaRecorder = html.MediaRecorder(stream, {
        'mimeType': mimeType,
        'audioBitsPerSecond': 128000, // Higher bitrate for better quality
      });
      
      _audioChunks.clear();
      _isRecording = true;
      
      // Use proper event handling for Flutter web
      _mediaRecorder!.addEventListener('dataavailable', (html.Event event) {
        final blobEvent = event as html.BlobEvent;
        if (blobEvent.data != null) {
          _audioChunks.add(blobEvent.data!);
          print('📹 Audio chunk received: ${blobEvent.data!.size} bytes');
        }
      });
      
      _mediaRecorder!.addEventListener('stop', (html.Event event) {
        print('⏹️ Recording stopped. Total chunks: ${_audioChunks.length}');
        _isRecording = false;
      });
      
      // Start recording with optimal time slices for better chunk collection
      _mediaRecorder!.start(50); // Collect data every 50ms for better quality
      
      // Wait a moment to ensure recording has started
      await Future.delayed(Duration(milliseconds: 200));
      
      print('✅ Recording started successfully');
      print('🔍 MediaRecorder state: ${_mediaRecorder!.state}');
      return true;
    } catch (e) {
      print('❌ Error starting recording: $e');
      _isRecording = false;
      return false;
    }
  }

  Future<bool> stopRecording() async {
    try {
      if (_mediaRecorder == null || !_isRecording) {
        print('⚠️ No active recording to stop');
        return false;
      }
      
      print('⏹️ Stopping recording...');
      print('🔍 Audio chunks before stop: ${_audioChunks.length}');
      
      // Request final data chunk
      _mediaRecorder!.requestData();
      
      // Stop recording
      _mediaRecorder!.stop();
      
      // Wait longer to ensure all data is collected
      await Future.delayed(Duration(milliseconds: 1000));
      
      print('✅ Recording stopped. Processing audio...');
      print('🔍 Final audio chunks: ${_audioChunks.length}');
      
      // Check if we have any audio data
      if (_audioChunks.isEmpty) {
        print('⚠️ No audio chunks collected!');
        return false;
      }
      
      // Calculate total size
      int totalSize = 0;
      for (var chunk in _audioChunks) {
        totalSize += chunk.size;
      }
      print('🔍 Total audio size: $totalSize bytes');
      
      return totalSize > 0;
    } catch (e) {
      print('❌ Error stopping recording: $e');
      return false;
    }
  }

  bool get isRecording => _isRecording;

  // Enhanced transcription with retry logic and better error handling
  Future<String?> transcribeAudio() async {
    try {
      if (_audioChunks.isEmpty) {
        print('⚠️ No audio data to transcribe');
        return null;
      }

      print('🎤 Transcribing audio...');
      print('🔍 Audio chunks: ${_audioChunks.length}');
      
      // Combine all audio chunks into one blob with proper MIME type
      final combinedBlob = html.Blob(_audioChunks, 'audio/webm;codecs=opus');
      print('🔍 Combined audio size: ${combinedBlob.size} bytes');
      print('🔍 Audio MIME type: ${combinedBlob.type}');

      // Validate audio size (must be at least 100 bytes for valid audio)
      if (combinedBlob.size < 100) {
        print('⚠️ Audio too small (${combinedBlob.size} bytes), may be invalid');
        return null;
      }

      // Convert blob to base64
      final reader = html.FileReader();
      reader.readAsDataUrl(combinedBlob);
      
      await reader.onLoad.first;
      
      // Extract base64 data (remove data:audio/webm;codecs=opus;base64, prefix)
      String base64Data = reader.result as String;
      if (base64Data.contains(',')) {
        base64Data = base64Data.split(',')[1];
      }
      
      print('✅ Audio converted to base64');
      print('🔍 Base64 length: ${base64Data.length}');

      // Validate base64 data
      if (base64Data.isEmpty || base64Data.length < 50) {
        print('⚠️ Base64 data too short, may be invalid');
        return null;
      }

      // Priority 1: Try backend Whisper AI first (most reliable)
      print('🎤 Trying backend Whisper AI...');
      final backendResult = await _tryBackendWhisper(base64Data);
      if (backendResult != null) {
        return backendResult;
      }

      print('❌ All transcription services failed');
      return null;
      
    } catch (e) {
      print('❌ Error transcribing audio: $e');
      return null;
    }
  }

  // Try backend Whisper AI transcription with improved language handling
  Future<String?> _tryBackendWhisper(String audioData) async {
    try {
      print('🎤 Trying backend Whisper AI transcription...');
      
      final backendUrl = ApiConfig.nutritionBaseUrl;
      final transcribeUrl = '$backendUrl/nutrition/transcribe';
      
      print('📡 Calling backend: $transcribeUrl');
      
      // Try English first for better accuracy, then auto-detect
      final languageConfigs = ['en', 'auto'];
      
      for (final lang in languageConfigs) {
        try {
          print('🌐 Trying backend Whisper with language: $lang');
          
          final response = await http.post(
            Uri.parse(transcribeUrl),
            headers: {
              'Content-Type': 'application/json',
            },
            body: json.encode({
              'audio': audioData,
              'language': lang,
              'method': 'whisper',
              'prompt': 'I eat food, breakfast, lunch, dinner, snack, apple, banana, rice, bread, vegetables, fruits, meat, fish, eggs, milk, yogurt, cheese, nuts, seeds, grains, pasta, soup, salad, juice, water, tea, coffee, I am eating, I ate, I will eat, I want to eat, I need to eat, I like to eat, I love to eat, I hate to eat, I cannot eat, I should eat, I must eat, I have eaten, I had eaten, I will have eaten, I am going to eat, I was eating, I will be eating, I have been eating, I had been eating, I will have been eating', // Comprehensive English food context
            }),
          ).timeout(Duration(seconds: 60));
          
          print('📡 Backend response with $lang: ${response.statusCode}');
          
          if (response.statusCode == 200) {
            final data = json.decode(response.body);
            print('📡 Backend data with $lang: $data');
            
            if (data['success'] == true && data['transcription'] != null) {
              final transcription = data['transcription'];
              print('✅ Backend Whisper transcription successful with $lang: "$transcription"');
              
              // Check if it's Tamil and translate to English
              if (_isTamilText(transcription)) {
                print('🔤 Tamil detected, translating to English...');
                final translatedText = await translateTamilToEnglish(transcription);
                if (translatedText != null && translatedText != transcription) {
                  print('✅ Tamil to English translation successful: "$translatedText"');
                  return translatedText;
                } else {
                  print('⚠️ Translation failed, returning Tamil text');
                  return transcription;
                }
              } else {
                print('🔤 English text detected, returning as-is');
                print('✅ Transcription result: "$transcription"');
                return transcription;
              }
            }
          }
        } catch (e) {
          print('⚠️ Failed with language $lang: $e');
          continue;
        }
      }
      
      print('❌ All language configurations failed');
      return null;
      
    } catch (e) {
      print('❌ Backend Whisper error: $e');
      return null;
    }
  }

  // Check if text is Tamil with improved accuracy
  bool _isTamilText(String text) {
    // Check for actual Tamil characters first
    final tamilPattern = RegExp(r'[஀-௿]');
    
    // If no Tamil characters found, it's likely English
    if (!tamilPattern.hasMatch(text)) {
      return false;
    }
    
    // Extended list of common Tamil words for verification
    final commonTamilWords = [
      'வணக்கம்', 'நன்றி', 'சரி', 'இல்லை', 'ஆம்', 'போகலாம்', 'வரலாம்',
      'சாப்பிட', 'குடிக்க', 'நடக்க', 'படுக்க', 'எழுந்திருக்க', 'வருகிறேன்',
      'போகிறேன்', 'சாப்பிடுகிறேன்', 'குடிக்கிறேன்', 'நடக்கிறேன்', 'படுக்கிறேன்',
      'சாப்பிட்டேன்', 'குடித்தேன்', 'நடந்தேன்', 'படுத்தேன்', 'வந்தேன்', 'போனேன்',
      'நான்', 'நீ', 'அவர்', 'அவள்', 'அது', 'இது', 'அங்கே', 'இங்கே',
      'எப்படி', 'எப்போது', 'எங்கே', 'ஏன்', 'என்ன', 'யார்', 'எந்த',
      'மிகவும்', 'சிறிது', 'பெரிய', 'சிறிய', 'நல்ல', 'கெட்ட', 'வேகமாக',
      'மெதுவாக', 'முன்', 'பின்', 'மேல்', 'கீழ்', 'உள்ளே', 'வெளியே'
    ];
    
    // Only consider it Tamil if it contains actual Tamil characters
    bool isLikelyTamil = tamilPattern.hasMatch(text) && 
                         commonTamilWords.any((word) => text.toLowerCase().contains(word.toLowerCase()));
    
    return isLikelyTamil;
  }

  // Local Tamil to English translation using comprehensive dictionary
  Future<String?> translateTamilToEnglish(String tamilText) async {
    try {
      final displayText = tamilText.length > 50 ? '${tamilText.substring(0, 50)}...' : tamilText;
      print('🏠 Using local Tamil to English translation: $displayText');
      
      // Clean the Tamil text for better translation
      String cleanTamilText = tamilText.trim();
      if (cleanTamilText.isEmpty) {
        print('⚠️ Empty text, nothing to translate');
        return tamilText;
      }
      
      // Try local translation first
      final localTranslation = await _localTamilTranslation(cleanTamilText);
      if (localTranslation != null && localTranslation != cleanTamilText) {
        print('✅ Local translation successful: "$localTranslation"');
        return localTranslation;
      }
      
      // Fallback to Google Translate API if local translation fails
      print('🔄 Local translation failed, trying Google Translate API...');
      return await _googleTranslateFallback(cleanTamilText);
      
    } catch (e) {
      print('❌ Translation error: $e');
      return tamilText; // Return original text if translation fails
    }
  }

  // Local Tamil translation using comprehensive dictionary
  Future<String?> _localTamilTranslation(String tamilText) async {
    try {
      print('🏠 Starting local Tamil translation...');
      
      // Comprehensive Tamil-English dictionary
      final tamilEnglishDict = {
        // Basic greetings and common words
        'வணக்கம்': 'Hello',
        'நன்றி': 'Thank you',
        'சரி': 'Okay/Correct',
        'இல்லை': 'No',
        'ஆம்': 'Yes',
        'போகலாம்': 'Let\'s go',
        'வரலாம்': 'Let\'s come',
        
        // Pronouns
        'நான்': 'I',
        'நீ': 'You',
        'அவர்': 'He',
        'அவள்': 'She',
        'அது': 'That',
        'இது': 'This',
        'அங்கே': 'There',
        'இங்கே': 'Here',
        
        // Food and eating related
        'சாப்பிட': 'Eat',
        'குடிக்க': 'Drink',
        'சாப்பிடுகிறேன்': 'I am eating',
        'சாப்பிட்டேன்': 'I ate',
        'சாப்பிடலாம்': 'Let\'s eat',
        'சாப்பிட வேண்டும்': 'Must eat',
        'குடிக்கிறேன்': 'I am drinking',
        
        // Common food items
        'சாதம்': 'Rice',
        'ரொட்டி': 'Bread',
        'தோசை': 'Dosa',
        'இட்லி': 'Idli',
        'காய்கறிகள்': 'Vegetables',
        'மீன்': 'Fish',
        'முட்டை': 'Egg',
        'பருப்பு': 'Dal/Lentils',
        'தயிர்': 'Curd/Yogurt',
        'கறி': 'Curry',
        'சாம்பார்': 'Sambar',
        'ரசம்': 'Rasam',
        
        // Time and actions
        'இன்று': 'Today',
        'நேற்று': 'Yesterday',
        'நாளை': 'Tomorrow',
        'வருகிறேன்': 'I am coming',
        'போகிறேன்': 'I am going',
        'நடக்கிறேன்': 'I am walking',
        'படுக்கிறேன்': 'I am sleeping',
        'எழுந்திருக்கிறேன்': 'I am getting up',
        
        // Past tense
        'சாப்பிட்டேன்': 'I ate',
        'குடித்தேன்': 'I drank',
        'நடந்தேன்': 'I walked',
        'படுத்தேன்': 'I slept',
        'வந்தேன்': 'I came',
        'போனேன்': 'I went',
        
        // Question words
        'எப்படி': 'How',
        'எப்போது': 'When',
        'எங்கே': 'Where',
        'ஏன்': 'Why',
        'என்ன': 'What',
        'யார்': 'Who',
        'எந்த': 'Which',
        
        // Adjectives and adverbs
        'மிகவும்': 'Very',
        'சிறிது': 'Little',
        'பெரிய': 'Big',
        'சிறிய': 'Small',
        'நல்ல': 'Good',
        'கெட்ட': 'Bad',
        'வேகமாக': 'Fast',
        'மெதுவாக': 'Slow',
        
        // Prepositions and directions
        'முன்': 'Before',
        'பின்': 'After',
        'மேல்': 'Above',
        'கீழ்': 'Below',
        'உள்ளே': 'Inside',
        'வெளியே': 'Outside',
        
        // Common phrases
        'நான் இன்று சாப்பிட்டது': 'What I ate today',
        'நான் இன்று சாப்பிட்டது சாதம்': 'I ate rice today',
        'நான் இன்று சாப்பிட்டது ரொட்டி': 'I ate bread today',
        'நான் இன்று சாப்பிட்டது தோசை': 'I ate dosa today',
        'நான் இன்று சாப்பிட்டது இட்லி': 'I ate idli today',
        
        // Complex food phrases
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் காய்கறிகள்': 'I ate rice and vegetables today',
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் மீன்': 'I ate rice and fish today',
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் முட்டை': 'I ate rice and egg today',
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் பருப்பு': 'I ate rice and dal today',
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் தயிர்': 'I ate rice and curd today',
        
        // Very detailed meals
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் காய்கறிகள் மற்றும் மீன்': 'I ate rice, vegetables and fish today',
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் காய்கறிகள் மற்றும் முட்டை': 'I ate rice, vegetables and egg today',
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் காய்கறிகள் மற்றும் பருப்பு': 'I ate rice, vegetables and dal today',
        'நான் இன்று சாப்பிட்டது சாதம் மற்றும் காய்கறிகள் மற்றும் தயிர்': 'I ate rice, vegetables and curd today',
        
        // Additional food items
        'அப்பளம்': 'Papad',
        'வடை': 'Vada',
        'பூரி': 'Puri',
        'பரோட்டா': 'Parotta',
        'சப்பாத்தி': 'Chapati',
        'மற்றும்': 'And',
        
        // Vegetables and ingredients
        'தக்காளி': 'Tomato',
        'வெங்காயம்': 'Onion',
        'பூண்டு': 'Garlic',
        'மிளகு': 'Pepper',
        'மிளகாய்': 'Chili',
        'மஞ்சள்': 'Turmeric',
        'கொத்தமல்லி': 'Coriander',
        'மென்தூள்': 'Ginger powder',
        'உப்பு': 'Salt',
        'எண்ணெய்': 'Oil',
        'வெண்ணெய்': 'Butter',
        
        // Chutneys and side dishes
        'சட்னி': 'Chutney',
        'தக்காளி சட்னி': 'Tomato Chutney',
        'மாங்காய் சட்னி': 'Mango Chutney',
        'தேங்காய் சட்னி': 'Coconut Chutney',
        'பச்சை மிளகாய் சட்னி': 'Green Chili Chutney',
        'வெங்காய சட்னி': 'Onion Chutney',
        
        // Additional Tamil food words
        'குழம்பு': 'Gravy',
        'கறி': 'Curry',
        'பொரியல்': 'Stir-fry',
        'குழம்பு': 'Sauce',
        'மசாலா': 'Spice mix',
        'ரசம்': 'Rasam',
        'சாம்பார்': 'Sambar',
        'தயிர்': 'Curd',
        'பால்': 'Milk',
        'தேன்': 'Honey',
        'சர்க்கரை': 'Sugar',
        'மாவு': 'Flour',
        'அரிசி': 'Rice grain',
        'கோதுமை': 'Wheat',
        'பருப்பு': 'Lentils',
        'கடலை': 'Peanut',
        'பாதாம்': 'Almond',
        'கொட்டை': 'Cashew'
      };
      
      // Direct word translation
      if (tamilEnglishDict.containsKey(tamilText)) {
        print('✅ Direct translation found: ${tamilEnglishDict[tamilText]}');
        return tamilEnglishDict[tamilText];
      }
      
      // Word-by-word translation
      final wordByWordTranslation = await _wordByWordTranslation(tamilText, tamilEnglishDict);
      if (wordByWordTranslation != null) {
        print('✅ Word-by-word translation successful: "$wordByWordTranslation"');
        return wordByWordTranslation;
      }
      
      print('⚠️ Local translation not found');
      return null;
      
    } catch (e) {
      print('❌ Local translation error: $e');
      return null;
    }
  }

  // Word-by-word translation
  Future<String?> _wordByWordTranslation(String tamilText, Map<String, String> dictionary) async {
    try {
      // Split Tamil text into words (Tamil words are space-separated)
      final words = tamilText.split(' ');
      final translatedWords = <String>[];
      
      for (final word in words) {
        if (dictionary.containsKey(word)) {
          translatedWords.add(dictionary[word]!);
        } else {
          // Keep untranslated words as-is
          translatedWords.add(word);
        }
      }
      
      if (translatedWords.isNotEmpty) {
        final result = translatedWords.join(' ');
        print('✅ Word-by-word translation: "$result"');
        return result;
      }
      
      return null;
    } catch (e) {
      print('❌ Word-by-word translation error: $e');
      return null;
    }
  }

    // Google Translate API fallback - Fixed implementation
  Future<String?> _googleTranslateFallback(String tamilText) async {
    return await _googleTranslateWithRetry(tamilText, 0);
  }

  // Google Translate with retry logic
  Future<String?> _googleTranslateWithRetry(String tamilText, int attempt) async {
    if (attempt >= 3) {
      print('❌ Google Translate failed after 3 attempts');
      return null;
    }
    
    try {
      print('🌐 Google Translate attempt ${attempt + 1}/3...');
      
             // Use the correct Google Translate endpoint
       final response = await http.post(
         Uri.parse('https://translate.googleapis.com/translate_a/single'),
         headers: {
           'Content-Type': 'application/x-www-form-urlencoded',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
         },
         body: {
           'client': 'gtx',
           'sl': 'ta', // Tamil language code
           'tl': 'en', // English language code
           'dt': 't',
           'q': tamilText,
         },
       ).timeout(const Duration(seconds: 30));

      print('📡 Translation API response: ${response.statusCode}');
      
      if (response.statusCode == 200) {
        try {
          final data = json.decode(response.body);
          print('📡 Translation API data: $data');
          
          if (data is List && data.isNotEmpty && data[0] is List) {
            final translations = data[0] as List;
            final translatedText = translations.map((t) => t[0]).join('').trim();
            
            if (translatedText.isNotEmpty && translatedText != tamilText) {
              print('✅ Google API translation successful: "$translatedText"');
              return translatedText;
            } else {
              print('⚠️ Google API returned empty or same text');
              return null;
            }
          } else {
            print('⚠️ Unexpected Google API response format: $data');
            return null;
          }
        } catch (parseError) {
          print('❌ Error parsing Google API response: $parseError');
          print('📡 Raw response: ${response.body}');
          return null;
        }
             } else if (response.statusCode == 429) {
         print('⚠️ Google API rate limited, waiting before retry...');
         await Future.delayed(Duration(seconds: 2));
         return await _googleTranslateWithRetry(tamilText, attempt + 1);
       } else {
        print('❌ Google API error: ${response.statusCode} - ${response.body}');
        return null;
      }
      
    } catch (e) {
      print('❌ Google API fallback error: $e');
      return null;
    }
  }

  // Clear audio data
  void clearAudio() {
    _audioChunks.clear();
    _mediaRecorder = null;
    _isRecording = false;
    print('🧹 Audio data cleared');
  }

  // Get recording duration (approximate)
  String getRecordingInfo() {
    if (_audioChunks.isEmpty) return 'No audio recorded';
    
    final totalSize = _audioChunks.fold<int>(0, (sum, chunk) => sum + chunk.size);
    final duration = totalSize / 16000; // Rough estimate: 16kbps
    
    return '${_audioChunks.length} chunks, ~${duration.toStringAsFixed(1)}s, ${(totalSize / 1024).toStringAsFixed(1)}KB';
  }

  // Test audio recording functionality
  Future<String?> testAudioRecording() async {
    try {
      print('🧪 Testing audio recording functionality...');
      
      // Start recording
      final startSuccess = await startRecording();
      if (!startSuccess) {
        return '❌ Failed to start recording';
      }
      
      // Wait for 3 seconds to record some audio
      await Future.delayed(Duration(seconds: 3));
      
      // Stop recording
      final stopSuccess = await stopRecording();
      if (!stopSuccess) {
        return '❌ Failed to stop recording or no audio collected';
      }
      
      // Check audio data
      if (_audioChunks.isEmpty) {
        return '❌ No audio chunks collected';
      }
      
      int totalSize = 0;
      for (var chunk in _audioChunks) {
        totalSize += chunk.size;
      }
      
      if (totalSize < 100) {
        return '⚠️ Audio too small: $totalSize bytes (expected >100 bytes)';
      }
      
      return '✅ Audio recording test successful: ${_audioChunks.length} chunks, $totalSize bytes';
    } catch (e) {
      return '❌ Audio recording test failed: $e';
    }
  }

  // Get detailed connection info
  String getConnectionInfo() {
    return 'Backend URL: ${ApiConfig.nutritionBaseUrl}\n'
           'Transcribe Endpoint: ${ApiConfig.transcribeEndpoint}\n'
           'Full URL: ${ApiConfig.nutritionBaseUrl}${ApiConfig.transcribeEndpoint}';
  }

  // Set Google Cloud API key for Speech-to-Text
  void setGoogleApiKey(String apiKey) {
    _googleApiKey = apiKey;
    print('🔑 Google API key configured: ${apiKey.isNotEmpty ? 'Set' : 'Not set'}');
  }

  // Get Google API key status
  bool get hasGoogleApiKey => _googleApiKey.isNotEmpty;
}
