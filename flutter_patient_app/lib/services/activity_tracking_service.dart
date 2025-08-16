import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';

class ActivityTrackingService {
  static String? _sessionId;
  static String? _userEmail;
  
  // Initialize tracking for a user session
  static void initializeSession(String sessionId, String userEmail) {
    _sessionId = sessionId;
    _userEmail = userEmail;
    print('🔍 Activity Tracking initialized for user: $userEmail');
  }
  
  // Clear session data
  static void clearSession() {
    _sessionId = null;
    _userEmail = null;
    print('🔍 Activity Tracking session cleared');
  }
  
  // Track a user activity
  static Future<bool> trackActivity({
    required String activityType,
    required Map<String, dynamic> activityData,
  }) async {
    if (_userEmail == null) {
      print('⚠️ Cannot track activity: No user email set');
      return false;
    }
    
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/track-activity'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'email': _userEmail,
          'activity_type': activityType,
          'activity_data': activityData,
          'session_id': _sessionId,
        }),
      );
      
      if (response.statusCode == 200) {
        print('✅ Activity tracked: $activityType');
        return true;
      } else {
        print('❌ Failed to track activity: ${response.body}');
        return false;
      }
    } catch (e) {
      print('❌ Error tracking activity: $e');
      return false;
    }
  }
  
  // Track page navigation
  static Future<bool> trackPageNavigation(String pageName, {String? action}) async {
    return await trackActivity(
      activityType: 'page_navigation',
      activityData: {
        'page': pageName,
        'action': action ?? 'viewed',
        'timestamp': DateTime.now().toIso8601String(),
      },
    );
  }
  
  // Track button clicks
  static Future<bool> trackButtonClick(String buttonName, {String? page, String? context}) async {
    return await trackActivity(
      activityType: 'button_click',
      activityData: {
        'button': buttonName,
        'page': page,
        'context': context,
        'timestamp': DateTime.now().toIso8601String(),
      },
    );
  }
  
  // Track form interactions
  static Future<bool> trackFormInteraction(String formName, String action, {Map<String, dynamic>? additionalData}) async {
    final Map<String, dynamic> data = {
      'form': formName,
      'action': action,
      'timestamp': DateTime.now().toIso8601String(),
    };
    
    if (additionalData != null) {
      data.addAll(additionalData);
    }
    
    return await trackActivity(
      activityType: 'form_interaction',
      activityData: data,
    );
  }
  
  // Track feature usage
  static Future<bool> trackFeatureUsage(String featureName, {String? action, Map<String, dynamic>? metadata}) async {
    final Map<String, dynamic> data = {
      'feature': featureName,
      'action': action ?? 'used',
      'timestamp': DateTime.now().toIso8601String(),
    };
    
    if (metadata != null) {
      data.addAll(metadata);
    }
    
    return await trackActivity(
      activityType: 'feature_usage',
      activityData: data,
    );
  }
  
  // Track errors
  static Future<bool> trackError(String errorType, String errorMessage, {String? page, String? context}) async {
    return await trackActivity(
      activityType: 'error',
      activityData: {
        'error_type': errorType,
        'error_message': errorMessage,
        'page': page,
        'context': context,
        'timestamp': DateTime.now().toIso8601String(),
      },
    );
  }
  
  // Track performance metrics
  static Future<bool> trackPerformance(String metricName, dynamic value, {String? unit, String? context}) async {
    return await trackActivity(
      activityType: 'performance',
      activityData: {
        'metric': metricName,
        'value': value,
        'unit': unit,
        'context': context,
        'timestamp': DateTime.now().toIso8601String(),
      },
    );
  }
  
  // Get current session info
  static Map<String, dynamic> getSessionInfo() {
    return {
      'session_id': _sessionId,
      'user_email': _userEmail,
    };
  }
} 