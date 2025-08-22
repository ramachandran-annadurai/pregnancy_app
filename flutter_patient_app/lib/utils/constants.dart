import 'package:flutter/material.dart';

class AppColors {
  static const Color primary = Color(0xFFBC77E4); // Blue
  static const Color secondary = Color(0xFFBC77E4); // Darker Blue
  static const Color background = Color(0xFFF8F9FA);
  static const Color border = Color(0xFFE1E5E9);
  static const Color textPrimary = Color(0xFF333333);
  static const Color textSecondary = Color(0xFF666666);
  static const Color success = Color(0xFF28A745);
  static const Color error = Color(0xFFDC3545);
  static const Color warning = Color(0xFFFFC107);
  static const Color info = Color(0xFFBC77E4);
  static const Color purple = Color(0xFFBC77E4); // Purple
}

class ApiConfig {
  // Backend server URLs - updated to match actual running server
  static const String baseUrl = 'http://127.0.0.1:5000';  // Main backend server
  static const String doctorBaseUrl = 'http://127.0.0.1:5001';
  // IMPORTANT: Nutrition backend is now integrated into main backend
  static const String nutritionBaseUrl = 'http://127.0.0.1:5000';  // Now uses main backend
  
  // Alternative URLs for different platforms
  static const String baseUrlAlt = 'http://localhost:5000';
  static const String baseUrlLocal = 'http://0.0.0.0:5000';
  
  // Platform-specific URLs
  static const String androidEmulatorUrl = 'http://10.0.2.2:5000';  // Android emulator
  static const String iosSimulatorUrl = 'http://127.0.0.1:5000';     // iOS simulator
  
  // Get the best URL for the current platform
  static String getBestBaseUrl() {
    // For now, return the main URL
    // You can add platform detection logic here if needed
    return baseUrl;
  }
  
  // Get alternative URLs for testing
  static List<String> getAlternativeUrls() {
    return [
      baseUrl,
      baseUrlAlt,
      androidEmulatorUrl,
      iosSimulatorUrl,
    ];
  }
  
  // Voice transcription endpoint - MUST use nutritionBaseUrl (port 5000)
  static const String transcribeEndpoint = '/nutrition/transcribe';
  static const String signupEndpoint = '/signup';
  static const String verifyOtpEndpoint = '/verify-otp';
  static const String loginEndpoint = '/login';
  static const String forgotPasswordEndpoint = '/forgot-password';
  static const String resetPasswordEndpoint = '/reset-password';
  static const String completeProfileEndpoint = '/complete-profile';
  static const String completeDoctorProfileEndpoint = '/complete-doctor-profile';
  static const String getProfileEndpoint = '/profile';
  static const String sendOtpEndpoint = '/send-otp';
  static const String completeNutritionEndpoint = '/complete-nutrition';
  static const String transcriptsEndpoint = '/transcripts';
}

class AppStrings {
  static const String appName = 'Patient Alert System';
  static const String loginTitle = 'Welcome Back';
  static const String signupTitle = 'Create Account';
  static const String forgotPasswordTitle = 'Reset Password';
  static const String profileTitle = 'Complete Profile';
  
  // Login
  static const String loginSubtitle = 'Sign in to your account';
  static const String patientIdOrEmail = 'Patient ID or Email';
  static const String password = 'Password';
  static const String login = 'Login';
  static const String dontHaveAccount = "Don't have an account?";
  static const String signup = 'Sign Up';
  static const String forgotPassword = 'Forgot Password?';
  
  // Signup
  static const String signupSubtitle = 'Create your patient account';
  static const String username = 'Username';
  static const String email = 'Email';
  static const String mobile = 'Mobile Number';
  static const String confirmPassword = 'Confirm Password';
  static const String createAccount = 'Create Account';
  static const String alreadyHaveAccount = 'Already have an account?';
  
  // OTP
  static const String otpTitle = 'Verify OTP';
  static const String otpSubtitle = 'Enter the 6-digit code sent to your email';
  static const String otpCode = 'OTP Code';
  static const String verifyOtp = 'Verify OTP';
  static const String resendOtp = 'Resend OTP';
  
  // Profile
  static const String profileSubtitle = 'Complete your profile information';
  static const String firstName = 'First Name';
  static const String lastName = 'Last Name';
  static const String dateOfBirth = 'Date of Birth';
  static const String bloodType = 'Blood Type';
  static const String isPregnant = 'Are you pregnant?';
  static const String lastPeriodDate = 'Last Period Date';
  static const String pregnancyWeek = 'Pregnancy Week';
  static const String expectedDelivery = 'Expected Delivery Date';
  static const String emergencyContact = 'Emergency Contact';
  static const String emergencyName = 'Emergency Contact Name';
  static const String emergencyRelationship = 'Relationship';
  static const String emergencyPhone = 'Emergency Contact Phone';
  static const String completeProfile = 'Complete Profile';
  
  // Messages
  static const String loading = 'Loading...';
  static const String success = 'Success!';
  static const String error = 'Error';
  static const String networkError = 'Network error. Please check your connection.';
  static const String invalidCredentials = 'Invalid credentials';
  static const String accountCreated = 'Account created successfully!';
  static const String profileCompleted = 'Profile completed successfully!';
  static const String otpSent = 'OTP sent to your email';
  static const String otpVerified = 'OTP verified successfully!';
  static const String passwordReset = 'Password reset successfully!';
}

class AppSizes {
  static const double paddingSmall = 8.0;
  static const double paddingMedium = 16.0;
  static const double paddingLarge = 24.0;
  static const double radiusSmall = 4.0;
  static const double radiusMedium = 8.0;
  static const double radiusLarge = 12.0;
  static const double iconSize = 24.0;
  static const double buttonHeight = 48.0;
} 