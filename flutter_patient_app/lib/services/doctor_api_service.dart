import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';

class DoctorApiService {
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

  static final DoctorApiService _instance = DoctorApiService._internal();
  factory DoctorApiService() => _instance;
  DoctorApiService._internal();

  // Doctor signup - stores in doctor_v2 collection
  Future<Map<String, dynamic>> signup({
    required String username,
    required String email,
    required String mobile,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.doctorBaseUrl}/doctor-signup'),
        headers: _headers,
        body: json.encode({
          'username': username,
          'email': email,
          'mobile': mobile,
          'password': password,
          'role': 'doctor',
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  // Doctor login - authenticates against doctor_v2 collection
  Future<Map<String, dynamic>> login({
    required String loginIdentifier,
    required String password,
    required String role,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.doctorBaseUrl}/doctor-login'),
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

  // Doctor OTP verification
  Future<Map<String, dynamic>> verifyOtp({
    required String email,
    required String otp,
    required String role,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.doctorBaseUrl}/doctor-verify-otp'),
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

  // Complete doctor profile
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

  // Doctor forgot password
  Future<Map<String, dynamic>> forgotPassword({
    required String loginIdentifier,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.doctorBaseUrl}/doctor-forgot-password'),
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

  // Doctor reset password
  Future<Map<String, dynamic>> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.doctorBaseUrl}/doctor-reset-password'),
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

  // Get doctor profile
  Future<Map<String, dynamic>> getDoctorProfile({
    required String doctorId,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.doctorBaseUrl}/doctor-profile/$doctorId'),
        headers: _headers,
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }

  // Send OTP for doctor
  Future<Map<String, dynamic>> sendOtp({
    required String email,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.doctorBaseUrl}/doctor-send-otp'),
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

  // Send OTP for doctor signup
  Future<Map<String, dynamic>> sendSignupOtp({
    required String username,
    required String email,
    required String mobile,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.doctorBaseUrl}/doctor-signup'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'username': username,
          'email': email,
          'mobile': mobile,
          'password': password,
          'role': 'doctor',
        }),
      );

      return json.decode(response.body);
    } catch (e) {
      return {'error': 'Network error: $e'};
    }
  }
} 