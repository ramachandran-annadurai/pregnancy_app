import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  bool _isLoading = false;
  bool _isLoggedIn = false;
  String? _patientId;
  String? _email;
  String? _username;
  String? _token;
  String? _error;
  String? _role;
  String? _objectId; // Add Object ID

  bool get isLoading => _isLoading;
  bool get isLoggedIn => _isLoggedIn;
  String? get patientId => _patientId;
  String? get email => _email;
  String? get username => _username;
  String? get token => _token;
  String? get error => _error;
  String? get role => _role;

  // Get current user information for data storage
  Future<Map<String, String?>> getCurrentUserInfo() async {
    try {
      // Ensure we have the latest data from SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      _email = prefs.getString('email') ?? "";
      _username = prefs.getString('username') ?? "";
      _patientId = prefs.getString('patientId') ?? "";
      _role = prefs.getString('role') ?? "";
      _objectId = prefs.getString('objectId') ?? ""; // Add Object ID
      
      // Debug logging
      print('🔍 AuthProvider Debug - getCurrentUserInfo:');
      print('  Email: $_email');
      print('  Username: $_username');
      print('  PatientId: $_patientId');
      print('  Role: $_role');
      print('  ObjectId: $_objectId');
      
      // Validate that we have the minimum required data
      if ((_email?.isEmpty ?? true) || (_username?.isEmpty ?? true) || (_patientId?.isEmpty ?? true)) {
        print('⚠️  WARNING: Missing required user data in SharedPreferences');
        print('   This might cause null value errors in the dashboard');
        
        // Try to get from memory if SharedPreferences is empty
        if ((_email?.isEmpty ?? true) && (_username?.isNotEmpty ?? false) && (_patientId?.isNotEmpty ?? false)) {
          print('   Using in-memory data as fallback');
        }
      }
      
      return {
        'userId': (_patientId?.isNotEmpty ?? false) ? _patientId : null,
        'userRole': (_role?.isNotEmpty ?? false) ? _role : null,
        'username': (_username?.isNotEmpty ?? false) ? _username : null,
        'email': (_email?.isNotEmpty ?? false) ? _email : null,
        'objectId': (_objectId?.isNotEmpty ?? false) ? _objectId : null,
      };
    } catch (e) {
      print('❌ ERROR in getCurrentUserInfo: $e');
      // Return safe defaults instead of throwing
      return {
        'userId': null,
        'userRole': null,
        'username': null,
        'email': null,
        'objectId': null,
      };
    }
  }

  // Helper method to load user data from SharedPreferences
  void _loadUserDataFromPrefs() {
    SharedPreferences.getInstance().then((prefs) {
      _email = prefs.getString('email');
      _username = prefs.getString('username');
      _patientId = prefs.getString('patientId');
      _role = prefs.getString('role');
      notifyListeners();
    });
  }

  Future<void> checkLoginStatus() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token');
    _role = prefs.getString('role');
    
    if (_token != null) {
      // Verify token with patient server
      try {
        final response = await _apiService.verifyToken(token: _token!);
        
        if (response.containsKey('valid') && response['valid'] == true) {
          _isLoggedIn = true;
          _patientId = prefs.getString('patientId');
          _email = prefs.getString('email');
          _username = prefs.getString('username');
          
          // Set token in API service
          ApiService.setAuthToken(_token!);
        } else {
          // Token is invalid, clear everything
          await logout();
        }
      } catch (e) {
        print('❌ Token verification failed: $e');
        await logout();
      }
    } else {
      _isLoggedIn = false;
    }
    
    notifyListeners();
  }

  Future<bool> login({
    required String loginIdentifier,
    required String password,
    required String role,
  }) async {
    _isLoading = true;
    _error = null;
    _role = role;
    notifyListeners();

    try {
      // Use regular ApiService for patient login
      final response = await _apiService.login(
        loginIdentifier: loginIdentifier,
        password: password,
        role: role,
      );

      if (response.containsKey('error')) {
        _error = response['error'];
        _isLoading = false;
        notifyListeners();
        return false;
      }

      if (response['patient_id'] != null) {
        _isLoggedIn = true;
        _patientId = response['patient_id'] ?? "";
        _email = response['email'] ?? "";
        _username = response['username'] ?? "";
        _token = response['token'] ?? "";
        _objectId = response['object_id'] ?? response['objectId'] ?? ""; // Handle both field names

        // Debug logging to see what we received
        print('🔍 AuthProvider Debug - Login Response:');
        print('  patient_id: $_patientId');
        print('  email: $_email');
        print('  username: $_username');
        print('  token: $_token');
        print('  object_id: $_objectId');

        // Validate required fields
        if (_patientId!.isEmpty || _email!.isEmpty || _username!.isEmpty || _token!.isEmpty) {
          _error = 'Login response missing required fields';
          _isLoading = false;
          notifyListeners();
          return false;
        }

        // Save to SharedPreferences
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('isLoggedIn', true);
        await prefs.setString('patientId', _patientId!);
        await prefs.setString('email', _email!);
        await prefs.setString('username', _username!);
        await prefs.setString('auth_token', _token!);
        await prefs.setString('role', _role!);
        await prefs.setString('objectId', _objectId ?? ""); // Save Object ID (can be empty string)

        // Debug logging for SharedPreferences
        print('🔍 AuthProvider Debug - SharedPreferences Saved:');
        print('  isLoggedIn: true');
        print('  patientId: $_patientId');
        print('  email: $_email');
        print('  username: $_username');
        print('  token: $_token');
        print('  role: $_role');
        print('  objectId: $_objectId');

        // Set token in API service
        ApiService.setAuthToken(_token!);

        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = 'Login failed - missing patient_id';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> signup({
    required String username,
    required String email,
    required String mobile,
    required String password,
    required String role,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Use regular ApiService for patient signup
      final response = await _apiService.signup(
        username: username,
        email: email,
        mobile: mobile,
        password: password,
        role: role,
      );

      if (response.containsKey('error')) {
        _error = response['error'];
        _isLoading = false;
        notifyListeners();
        return false;
      }

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> verifyOtp({
    required String email,
    required String otp,
    required String role,
  }) async {
    _isLoading = true;
    _error = null;
    _role = role;
    notifyListeners();

    try {
      // Use regular ApiService for patient OTP verification
      final response = await _apiService.verifyOtp(
        email: email,
        otp: otp,
        role: role,
      );

      if (response.containsKey('error')) {
        _error = response['error'];
        _isLoading = false;
        notifyListeners();
        return false;
      }

      if (response['patient_id'] != null) {
        _isLoggedIn = true;
        _patientId = response['patient_id'];
        _email = response['email'];
        _username = response['username'];
        _token = response['token'];
        _objectId = response['objectId']; // Store Object ID

        // Save to SharedPreferences
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('isLoggedIn', true);
        await prefs.setString('patientId', _patientId!);
        await prefs.setString('email', _email!);
        await prefs.setString('username', _username!);
        await prefs.setString('auth_token', _token!);
        await prefs.setString('role', _role!);
        await prefs.setString('objectId', _objectId!); // Save Object ID

        // Set token in API service
        ApiService.setAuthToken(_token!);

        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = 'OTP verification failed';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> forgotPassword({
    required String loginIdentifier,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.forgotPassword(
        loginIdentifier: loginIdentifier,
      );

      if (response.containsKey('error')) {
        _error = response['error'];
        _isLoading = false;
        notifyListeners();
        return false;
      }

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.resetPassword(
        email: email,
        otp: otp,
        newPassword: newPassword,
      );

      if (response.containsKey('error')) {
        _error = response['error'];
        _isLoading = false;
        notifyListeners();
        return false;
      }

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = 'Network error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }



  Future<void> logout() async {
    _isLoggedIn = false;
    _patientId = null;
    _email = null;
    _username = null;
    _token = null;
    _error = null;
    _role = null;
    _objectId = null; // Clear Object ID on logout

    // Clear SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();

    // Clear token from API service
    ApiService.clearAuthToken();

    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
} 