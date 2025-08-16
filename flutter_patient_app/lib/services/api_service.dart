import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';

class ApiService {
  static String? _authToken;

  static void setAuthToken(String token) {
    _authToken = token;
  }

  static void clearAuthToken() {
    _authToken = null;
  }

  static Map<String, String> get _headers {
    Map<String, String> headers = {
      'Content-Type': 'application/json',
    };
    
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    
    return headers;
  }

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  Future<Map<String, dynamic>> signup({
    required String username,
    required String email,
    required String mobile,
    required String password,
    required String role,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.signupEndpoint}'),
        headers: _headers,
        body: json.encode({
          'username': username,
          'email': email,
          'mobile': mobile,
          'password': password,
          'role': role,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> verifyOtp({
    required String email,
    required String otp,
    required String role,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.verifyOtpEndpoint}'),
        headers: _headers,
        body: json.encode({
          'email': email,
          'otp': otp,
          'role': role,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> login({
    required String loginIdentifier,
    required String password,
    required String role,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.loginEndpoint}'),
        headers: _headers,
        body: json.encode({
          'login_identifier': loginIdentifier,
          'password': password,
          'role': role,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> forgotPassword({
    required String loginIdentifier,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.forgotPasswordEndpoint}'),
        headers: _headers,
        body: json.encode({
          'login_identifier': loginIdentifier,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.resetPasswordEndpoint}'),
        headers: _headers,
        body: json.encode({
          'email': email,
          'otp': otp,
          'new_password': newPassword,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> completeProfile({
    required String patientId,
    required String firstName,
    required String lastName,
    required String dateOfBirth,
    required String bloodType,
    required String weight,
    required String height,
    required bool isPregnant,
    String? lastPeriodDate,
    String? pregnancyWeek,
    String? expectedDeliveryDate,
    required String emergencyName,
    required String emergencyRelationship,
    required String emergencyPhone,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.completeProfileEndpoint}'),
        headers: _headers,
        body: json.encode({
          'first_name': firstName,
          'last_name': lastName,
          'date_of_birth': dateOfBirth,
          'blood_type': bloodType,
          'weight': weight,
          'height': height,
          'is_pregnant': isPregnant,
          'last_period_date': lastPeriodDate,
          'pregnancy_week': pregnancyWeek,
          'expected_delivery_date': expectedDeliveryDate,
          'emergency_name': emergencyName,
          'emergency_relationship': emergencyRelationship,
          'emergency_phone': emergencyPhone,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> getProfile({
    required String patientId,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.getProfileEndpoint}/$patientId'),
        headers: _headers,
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> completeDoctorProfile({
    required String firstName,
    required String lastName,
    required String qualification,
    required String specialization,
    required String workingHospital,
    required String doctorId,
    required String licenseNumber,
    required String phone,
    required String address,
    required String city,
    required String state,
    required String zipCode,
    required String experienceYears,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.doctorBaseUrl}${ApiConfig.completeDoctorProfileEndpoint}'),
        headers: _headers,
        body: json.encode({
          'first_name': firstName,
          'last_name': lastName,
          'qualification': qualification,
          'specialization': specialization,
          'working_hospital': workingHospital,
          'doctor_id': doctorId,
          'license_number': licenseNumber,
          'phone': phone,
          'address': address,
          'city': city,
          'state': state,
          'zip_code': zipCode,
          'experience_years': experienceYears,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> sendOtp({
    required String email,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.sendOtpEndpoint}'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'email': email,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> verifyToken({
    required String token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/verify-token'),
        headers: _headers,
        body: json.encode({
          'token': token,
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> saveSleepLog(Map<String, dynamic> sleepData) async {
    try {
      // DEBUG LOGGING - See exactly what's being sent
      print('🔍 ===== API SERVICE DEBUG START =====');
      print('🔍 URL: ${ApiConfig.baseUrl}/save-sleep-log');
      print('🔍 Headers: $_headers');
      print('🔍 Sleep Data Received: $sleepData');
      print('🔍 Email Field: ${sleepData['email']}');
      print('🔍 JSON Encoded: ${json.encode(sleepData)}');
      print('🔍 ===== API SERVICE DEBUG END =====');
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/save-sleep-log'),
        headers: _headers,
        body: json.encode(sleepData),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to save sleep log');
      }
    } catch (e) {
      throw Exception('Error saving sleep log: $e');
    }
  }

  // Save kick session data
  Future<Map<String, dynamic>> saveKickSession(Map<String, dynamic> kickData) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/save-kick-session'),
        headers: _headers,
        body: json.encode(kickData),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to save kick session');
      }
    } catch (e) {
      throw Exception('Error saving kick session: $e');
    }
  }

  // Get kick history for a patient
  Future<Map<String, dynamic>> getKickHistory(String patientId) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/get-kick-history/$patientId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get kick history');
      }
    } catch (e) {
      throw Exception('Error getting kick history: $e');
    }
  }
} 