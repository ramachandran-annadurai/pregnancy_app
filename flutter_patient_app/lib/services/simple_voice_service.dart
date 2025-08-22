import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:html' as html;
import '../utils/constants.dart';

class SimpleVoiceService {
  html.MediaRecorder? _mediaRecorder;
  List<html.Blob> _audioChunks = [];
  bool _isRecording = false;

  // Check if browser supports MediaRecorder
  bool get isSupported {
    return html.window.navigator.mediaDevices != null &&
           html.MediaRecorder != null;
  }

  // Start recording
  Future<bool> startRecording() async {
    try {
      if (!isSupported) {
        print('❌ MediaRecorder not supported in this browser');
        return false;
      }

      print('🎤 Starting voice recording...');
      
      // Get microphone access
      final stream = await html.window.navigator.mediaDevices!.getUserMedia({
        'audio': {
          'sampleRate': 44100,
          'channelCount': 1,
          'echoCancellation': true,
          'noiseSuppression': true,
        }
      });

      // Create MediaRecorder with WebM format (widely supported)
      _mediaRecorder = html.MediaRecorder(stream, {
        'mimeType': 'audio/webm;codecs=opus',
        'audioBitsPerSecond': 128000,
      });

      _audioChunks.clear();
      _isRecording = true;

      // Handle data available event
      _mediaRecorder!.addEventListener('dataavailable', (html.Event event) {
        final blobEvent = event as html.BlobEvent;
        if (blobEvent.data != null) {
          _audioChunks.add(blobEvent.data!);
          print('📹 Audio chunk received: ${blobEvent.data!.size} bytes');
        }
      });

      // Handle recording stop
      _mediaRecorder!.addEventListener('stop', (html.Event event) {
        print('⏹️ Recording stopped. Total chunks: ${_audioChunks.length}');
        _isRecording = false;
      });

      // Start recording
      _mediaRecorder!.start(1000); // Collect data every 1 second
      print('✅ Recording started successfully');
      
      return true;
    } catch (e) {
      print('❌ Error starting recording: $e');
      _isRecording = false;
      return false;
    }
  }

  // Stop recording
  Future<bool> stopRecording() async {
    try {
      if (_mediaRecorder == null || !_isRecording) {
        print('⚠️ No active recording to stop');
        return false;
      }

      print('⏹️ Stopping recording...');
      _mediaRecorder!.stop();
      
      // Wait a bit for the last chunk
      await Future.delayed(Duration(milliseconds: 500));
      
      print('✅ Recording stopped. Processing audio...');
      return true;
    } catch (e) {
      print('❌ Error stopping recording: $e');
      return false;
    }
  }

  // Get recording status
  bool get isRecording => _isRecording;

  // Transcribe audio using the backend
  Future<String?> transcribeAudio() async {
    try {
      if (_audioChunks.isEmpty) {
        print('⚠️ No audio data to transcribe');
        return null;
      }

      print('🎤 Transcribing audio...');
      print('🔍 Audio chunks: ${_audioChunks.length}');
      
      // Combine all audio chunks into one blob
      final combinedBlob = html.Blob(_audioChunks, 'audio/webm');
      print('🔍 Combined audio size: ${combinedBlob.size} bytes');

      // Convert blob to base64
      final reader = html.FileReader();
      reader.readAsDataUrl(combinedBlob);
      
      await reader.onLoad.first;
      
      // Extract base64 data (remove data:audio/webm;base64, prefix)
      String base64Data = reader.result as String;
      base64Data = base64Data.split(',')[1];
      
      print('✅ Audio converted to base64');
      print('🔍 Base64 length: ${base64Data.length}');

      // Send to backend for transcription
      final response = await http.post(
        Uri.parse('${ApiConfig.nutritionBaseUrl}/nutrition/transcribe'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: json.encode({
          'audio': base64Data,
          'language': 'en',
          'method': 'whisper',
        }),
      ).timeout(Duration(seconds: 60));

      print('📡 Backend response: ${response.statusCode}');
      print('📡 Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          final transcription = data['transcription'];
          print('✅ Transcription successful: $transcription');
          return transcription;
        } else {
          print('❌ Transcription failed: ${data['message']}');
          return null;
        }
      } else {
        print('❌ HTTP error: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('❌ Error transcribing audio: $e');
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
}
