import 'package:flutter/material.dart';
import '../services/api_service.dart';

class UserProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  bool _isLoading = false;
  Map<String, dynamic>? _userProfile;
  String? _error;

  bool get isLoading => _isLoading;
  Map<String, dynamic>? get userProfile => _userProfile;
  String? get error => _error;

  Future<bool> completeProfile({
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
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.completeProfile(
        patientId: patientId,
        firstName: firstName,
        lastName: lastName,
        dateOfBirth: dateOfBirth,
        bloodType: bloodType,
        weight: weight,
        height: height,
        isPregnant: isPregnant,
        lastPeriodDate: lastPeriodDate,
        pregnancyWeek: pregnancyWeek,
        expectedDeliveryDate: expectedDeliveryDate,
        emergencyName: emergencyName,
        emergencyRelationship: emergencyRelationship,
        emergencyPhone: emergencyPhone,
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

  Future<bool> getProfile({required String patientId}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.getProfile(patientId: patientId);

      if (response.containsKey('error')) {
        _error = response['error'];
        _isLoading = false;
        notifyListeners();
        return false;
      }

      _userProfile = response;
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

  Map<String, dynamic> calculatePregnancyDates({
    required String lastPeriodDate,
  }) {
    try {
      final lastPeriod = DateTime.parse(lastPeriodDate);
      final today = DateTime.now();
      
      // Validate that last period date is not in the future
      if (lastPeriod.isAfter(today)) {
        return {
          'error': 'Last period date cannot be in the future',
          'pregnancyWeek': null,
          'expectedDeliveryDate': null,
        };
      }
      
      // Calculate pregnancy week (gestational age)
      final daysDiff = today.difference(lastPeriod).inDays;
      int pregnancyWeek = (daysDiff / 7).floor();
      
      // Ensure pregnancy week is within valid range (1-42 weeks)
      if (pregnancyWeek < 1) {
        pregnancyWeek = 1;
      } else if (pregnancyWeek > 42) {
        pregnancyWeek = 42;
      }
      
      // Calculate expected delivery date (40 weeks from last period)
      final expectedDelivery = lastPeriod.add(Duration(days: 40 * 7));
      final expectedDeliveryDate = expectedDelivery.toIso8601String().split('T')[0];
      
      return {
        'pregnancyWeek': pregnancyWeek.toString(),
        'expectedDeliveryDate': expectedDeliveryDate,
        'error': null,
      };
    } catch (e) {
      return {
        'error': 'Error calculating pregnancy dates: $e',
        'pregnancyWeek': null,
        'expectedDeliveryDate': null,
      };
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  void clearProfile() {
    _userProfile = null;
    notifyListeners();
  }
} 