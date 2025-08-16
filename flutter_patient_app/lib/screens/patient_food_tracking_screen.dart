import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/foundation.dart';
import '../utils/constants.dart';
import '../services/api_service.dart';
import 'detailed_food_entry_screen.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class PatientFoodTrackingScreen extends StatefulWidget {
  final DateTime date;
  final String userRole; // Add this

  const PatientFoodTrackingScreen({
    Key? key,
    required this.date,
    this.userRole = 'patient', // Default value
  }) : super(key: key);

  @override
  State<PatientFoodTrackingScreen> createState() => _PatientFoodTrackingScreenState();
}

class _PatientFoodTrackingScreenState extends State<PatientFoodTrackingScreen> {
  final TextEditingController _foodController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  
  // Remove voice recording related variables
  // final VoiceRecordingService _voiceService = VoiceRecordingService();
  // bool _isRecording = false;
  // bool _isLoading = false;
  // String _transcribedText = '';
  
  bool _isAnalyzing = false;
  bool _isSaving = false;
  bool _isLoadingUserData = true;
  
  String _selectedMealType = 'breakfast';
  int _pregnancyWeek = 1;
  String _username = '';
  String _email = '';
  String _userId = '';
  String _userRole = 'patient';
  
  Map<String, dynamic>? _nutritionAnalysis;
  Map<String, dynamic>? _userProfile;
  Map<String, dynamic>? _dailyCalorieSummary;

  // Add these variables to store profile data
  String _expectedDeliveryDate = '';
  String _lastPeriodDate = '';
  String _bloodType = '';
  String _height = '';
  String _weight = '';

  @override
  void initState() {
    super.initState();
    
    // Set default values
    _selectedMealType = 'breakfast';
    _pregnancyWeek = 1;
    _userRole = 'patient';
    
    // Fetch user data from backend
    _fetchUserProfile();
    
    print('🚀 Food Tracking Screen initialized');
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Refresh user data when screen becomes visible
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _fetchUserProfile();
      }
    });
  }

  @override
  void dispose() {
    _foodController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  // Restore the method to fetch user profile from backend
  Future<void> _fetchUserProfile() async {
    try {
      setState(() {
        _isLoadingUserData = true;
      });

      print('🔍 Fetching current login user profile using AuthProvider...');
      
      // Get current login user info from AuthProvider (same as kick counter)
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      final String? patientId = userInfo['userId'];
      if (patientId == null) {
        throw Exception('Patient ID not found. Please ensure you are logged in.');
      }

      print('🔍 Found patient ID: $patientId');
      
      // Use the patient ID to fetch profile (same pattern as kick counter)
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/get-patient-profile/${patientId}'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('✅ Current user profile response: ${json.encode(data)}');
        
        if (data['success'] == true) {
          final profile = data['profile'];
          
          setState(() {
            _userId = profile['patient_id'] ?? '';
            _username = profile['username'] ?? '';
            _email = profile['email'] ?? '';
            _pregnancyWeek = profile['pregnancy_week'] ?? 1;
            
            // Get additional profile details
            _expectedDeliveryDate = profile['expected_delivery_date'] ?? 'Not specified';
            _lastPeriodDate = profile['last_period_date'] ?? 'Not specified';
            _bloodType = profile['blood_type'] ?? 'Not specified';
            _height = profile['height'] ?? 'Not specified';
            _weight = profile['weight'] ?? 'Not specified';
            
            _isLoadingUserData = false;
          });
          
          print('✅ Profile data fetched successfully:');
          print('🆔 User ID: $_userId');
          print('👤 Username: $_username');
          print(' Email: $_email');
          print(' Pregnancy Week: $_pregnancyWeek');
          print(' Expected Delivery: $_expectedDeliveryDate');
          print(' Last Period: $_lastPeriodDate');
          print(' Blood Type: $_bloodType');
          print(' Height: $_height');
          print(' Weight: $_weight');
          
          // Show success message
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Profile loaded: ${_username} - Week $_pregnancyWeek'),
              backgroundColor: Colors.green,
              duration: Duration(seconds: 2),
            ),
          );
        } else {
          throw Exception(data['message'] ?? 'Failed to fetch profile');
        }
      } else {
        throw Exception('HTTP Error: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Error fetching current user profile: $e');
      setState(() {
        _isLoadingUserData = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to get current user: $e'),
          backgroundColor: Colors.red,
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  // Add method to get current login user from your auth system
  Future<Map<String, dynamic>?> _getCurrentLoginUser() async {
    try {
      print('🔍 Getting current login user from AuthProvider...');
      
      // Use the same method as kick counter screen
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo != null && userInfo['userId'] != null) {
        print('✅ Got current user from AuthProvider: ${userInfo['userId']}');
        return {
          'email': userInfo['email'] ?? '',
          'id': userInfo['userId'],
          'username': userInfo['username'] ?? ''
        };
      } else {
        print('❌ No current user found in AuthProvider');
        return null;
      }
      
    } catch (e) {
      print('❌ Error getting current login user from AuthProvider: $e');
      return null;
    }
  }

  // Restore the method to update pregnancy info
  Future<void> _updatePregnancyInfo() async {
    try {
      setState(() {
        _isLoadingUserData = true;
      });

      print('🔍 Updating pregnancy info for user: $_userId');
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/nutrition/update-pregnancy-info'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'patient_id': _userId,
          'is_pregnant': true,
          'last_period_date': '2025-05-02',
        }),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('✅ Pregnancy info update response: ${json.encode(data)}');
        
        if (data['success'] == true) {
          // Refresh user profile
          await _fetchUserProfile();
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Pregnancy information updated successfully!'),
              backgroundColor: Colors.green,
              duration: Duration(seconds: 3),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to update pregnancy info: ${data['message']}'),
              backgroundColor: Colors.red,
              duration: Duration(seconds: 3),
            ),
          );
        }
      } else {
        throw Exception('HTTP Error: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Error updating pregnancy info: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error updating pregnancy information: $e'),
          backgroundColor: Colors.red,
          duration: Duration(seconds: 3),
        ),
      );
    } finally {
      setState(() {
        _isLoadingUserData = false;
      });
    }
  }

  Future<void> _analyzeNutrition() async {
    try {
      print('🔍 Starting nutrition analysis...');
      
      // Get food input with null safety
      final foodInput = _foodController.text.trim();
      if (foodInput.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please enter food details first'),
            backgroundColor: Colors.orange,
          ),
        );
        return;
      }

      setState(() {
        _isAnalyzing = true;
        _nutritionAnalysis = null;
      });

      print('🍎 Analyzing nutrition for: $foodInput');
      // print('📅 Pregnancy week: $_pregnancyWeek'); // Removed as per edit hint

      // Call the Flask nutrition analysis API
      final response = await http.post(
        Uri.parse('${ApiConfig.nutritionBaseUrl}/nutrition/analyze-nutrition'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'food_input': foodInput,
          'user_id': _userId,  // Send user_id for auto-fetching pregnancy week
          'notes': _notesController.text.trim(),
        }),
      ).timeout(const Duration(seconds: 60));

      print('📡 API Response Status: ${response.statusCode}');
      print('📡 API Response Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data['success'] == true) {
          setState(() {
            _nutritionAnalysis = data;
          });
          
          // Show success message
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('✅ Nutrition analysis completed!'),
              backgroundColor: Colors.green,
            ),
          );
          
          print('✅ Nutrition analysis successful');
        } else {
          throw Exception(data['error'] ?? 'Unknown error in nutrition analysis');
        }
      } else {
        throw Exception('API returned status ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('❌ Error in nutrition analysis: $e');
      setState(() {
        _nutritionAnalysis = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isAnalyzing = false;
      });
    }
  }

  Future<void> _saveFoodEntry() async {
    try {
      print('💾 Starting to save food entry for current user...');
      
      final foodDetails = _foodController.text.trim();
      if (foodDetails.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please enter food details first'),
            backgroundColor: Colors.orange,
          ),
        );
        return;
      }

      // Get current user info from AuthProvider (same as kick counter)
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      final String? patientId = userInfo['userId'];
      if (patientId == null) {
        throw Exception('Patient ID not found. Please ensure you are logged in.');
      }

      // Ensure we have current user data
      if (_userId.isEmpty || _email.isEmpty) {
        print('❌ No current user data available, fetching profile first...');
        await _fetchUserProfile();
        
        if (_userId.isEmpty || _email.isEmpty) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('User not identified. Please ensure you are logged in.'),
              backgroundColor: Colors.red,
            ),
          );
          return;
        }
      }

      setState(() {
        _isSaving = true;
      });

      print('🍎 Saving food entry for current user:');
      print('🆔 User ID: $_userId');
      print(' Email: $_email');
      print('👤 Username: $_username');
      print('🍽️ Food: $foodDetails');
      print('🍽️ Meal type: $_selectedMealType');
      print(' Pregnancy week: $_pregnancyWeek');

      // Prepare food data with current user info (same structure as kick counter)
      final foodData = {
        'userId': patientId, // Use AuthProvider patient ID
        'userRole': 'patient', // Use default role
        'username': _username,
        'email': _email,
        'food_details': foodDetails,
        'meal_type': _selectedMealType,
        'pregnancy_week': _pregnancyWeek,
        'notes': _notesController.text.trim(),
        'transcribed_text': foodDetails,
        'nutritional_breakdown': {
          'estimated_calories': _nutritionAnalysis?['nutritional_breakdown']?['estimated_calories'] ?? 0,
          'protein_grams': _nutritionAnalysis?['nutritional_breakdown']?['protein_grams'] ?? 0,
          'carbohydrates_grams': _nutritionAnalysis?['nutritional_breakdown']?['carbohydrates_grams'] ?? 0,
          'fat_grams': _nutritionAnalysis?['nutritional_breakdown']?['fat_grams'] ?? 0,
          'fiber_grams': _nutritionAnalysis?['nutritional_breakdown']?['fiber_grams'] ?? 0,
        },
        'timestamp': DateTime.now().toIso8601String(),
      };

      print('📤 Sending food data for current user to backend: $foodData');

      // Save to backend with current user's ID
      final response = await http.post(
        Uri.parse('${ApiConfig.nutritionBaseUrl}/nutrition/save-food-entry'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(foodData),
      ).timeout(const Duration(seconds: 60));

      print('📡 Save API Response Status: ${response.statusCode}');
      print('📡 Save API Response Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ Food saved for ${_username}!'),
              backgroundColor: Colors.green,
            ),
          );
          
          // Clear form
          _foodController.clear();
          _notesController.clear();
          setState(() {
            _nutritionAnalysis = null;
          });
          
          print('✅ Food entry saved successfully for current user: $_username');
        } else {
          throw Exception(data['error'] ?? 'Unknown error saving food entry');
        }
      } else {
        throw Exception('Save API returned status ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('❌ Error saving food entry for current user: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error saving: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  // Future<void> _updatePregnancyInfo() async { // Removed as per edit hint
  //   try {
  //     setState(() {
  //       _isLoadingUserData = true;
  //     });

  //     print('🔍 Updating pregnancy info for patient ID: $_userId');
      
  //     final response = await http.post(
  //       Uri.parse('${ApiConfig.nutritionBaseUrl}/nutrition/update-pregnancy-info'),
  //       headers: {'Content-Type': 'application/json'},
  //       body: json.encode({
  //         'patient_id': _userId,
  //         'is_pregnant': true,
  //         'last_period_date': '2024-01-01', // This should come from user input
  //       }),
  //     );

  //     if (response.statusCode == 200) {
  //       final data = json.decode(response.body);
  //       print('✅ Pregnancy info update response: ${json.encode(data)}');
        
  //       if (data['success'] == true) {
  //         // Refresh pregnancy info
  //         await _fetchUserProfile();
          
  //         ScaffoldMessenger.of(context).showSnackBar(
  //           SnackBar(
  //             content: Text('Pregnancy information updated successfully!'),
  //             backgroundColor: Colors.green,
  //             duration: Duration(seconds: 3),
  //           ),
  //         );
  //       } else {
  //         ScaffoldMessenger.of(context).showSnackBar(
  //           SnackBar(
  //             content: Text('Failed to update pregnancy info: ${data['message']}'),
  //             backgroundColor: Colors.red,
  //             duration: Duration(seconds: 3),
  //           ),
  //         );
  //       }
  //     } else {
  //       print('❌ HTTP Error: ${response.statusCode}');
  //       print('❌ Response body: ${response.body}');
        
  //       ScaffoldMessenger.of(context).showSnackBar(
  //         SnackBar(
  //           content: Text('Failed to update pregnancy information'),
  //           backgroundColor: Colors.red,
  //           duration: Duration(seconds: 3),
  //         ),
  //       );
  //     }
  //   } catch (e) {
  //     print('❌ Error updating pregnancy info: $e');
  //     ScaffoldMessenger.of(context).showSnackBar(
  //       SnackBar(
  //         content: Text('Error updating pregnancy information: $e'),
  //         backgroundColor: Colors.red,
  //         duration: Duration(seconds: 3),
  //       ),
  //     );
  //   } finally {
  //     setState(() {
  //       _isLoadingUserData = false;
  //     });
  //   }
  // } // Removed as per edit hint

  Future<void> _fetchDailyCalorieSummary() async {
    try {
      setState(() {
        _isLoadingUserData = true;
      });

      print('🔍 Fetching daily calorie summary for patient ID: $_userId');
      
      final response = await http.get(
        Uri.parse('${ApiConfig.nutritionBaseUrl}/nutrition/daily-calorie-summary/$_userId'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('✅ Daily calorie summary response: ${json.encode(data)}');
        
        if (data['success'] == true) {
          setState(() {
            _dailyCalorieSummary = data;
          });
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Daily calorie summary fetched successfully!'),
              backgroundColor: Colors.green,
              duration: Duration(seconds: 3),
            ),
          );
        } else {
          throw Exception(data['error'] ?? 'Unknown error fetching daily calorie summary');
        }
      } else {
        throw Exception('API returned status ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('❌ Error fetching daily calorie summary: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error fetching daily calorie summary: $e'),
          backgroundColor: Colors.red,
          duration: Duration(seconds: 3),
        ),
      );
    } finally {
      setState(() {
        _isLoadingUserData = false;
      });
    }
  }

  // Add this method to show current user profile
  void _showCurrentUserProfile() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Row(
            children: [
              Icon(Icons.person, color: Colors.purple),
              SizedBox(width: 8),
              Text('Current User Profile'),
            ],
          ),
          content: Container(
            width: double.maxFinite,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // User Basic Information Section
                  _buildProfileSection(
                    '👤 User Information',
                    [
                      _buildProfileInfoRow('📧 Email ID', _email.isNotEmpty ? _email : 'Not available'),
                      _buildProfileInfoRow('🆔 Patient ID', _userId.isNotEmpty ? _userId : 'Not available'),
                      _buildProfileInfoRow('👤 Username', _username.isNotEmpty ? _username : 'Not available'),
                    ],
                    Colors.blue[700]!,
                  ),
                  
                  SizedBox(height: 16),
                  
                  // Pregnancy Information Section
                  _buildProfileSection(
                    '🤱 Pregnancy Information',
                    [
                      _buildProfileInfoRow('🤱 Pregnancy Week', 'Week $_pregnancyWeek'),
                      _buildProfileInfoRow('📅 Expected Delivery', _expectedDeliveryDate.isNotEmpty ? _expectedDeliveryDate : 'Not specified'),
                      _buildProfileInfoRow('📅 Last Period Date', _lastPeriodDate.isNotEmpty ? _lastPeriodDate : 'Not specified'),
                    ],
                    Colors.pink[700]!,
                  ),
                  
                  SizedBox(height: 16),
                  
                  // Status Section
                  Container(
                    width: double.infinity,
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.green[200]!),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.check_circle, color: Colors.green[600], size: 20),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Profile data loaded from backend',
                            style: TextStyle(
                              color: Colors.green[700],
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  SizedBox(height: 16),
                  
                  // Additional Information Section
                  _buildProfileSection(
                    ' Additional Details',
                    [
                      _buildProfileInfoRow('🩸 Blood Type', _bloodType.isNotEmpty ? _bloodType : 'Not specified'),
                      _buildProfileInfoRow('📏 Height', _height.isNotEmpty ? '$_height cm' : 'Not specified'),
                      _buildProfileInfoRow('⚖️ Weight', _weight.isNotEmpty ? '$_weight kg' : 'Not specified'),
                    ],
                    Colors.teal[700]!,
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: Text('Close'),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
                _fetchUserProfile(); // Refresh profile data
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.purple,
                foregroundColor: Colors.white,
              ),
              child: Text('Refresh'),
            ),
          ],
        );
      },
    );
  }

  // Helper method to build profile sections with headers
  Widget _buildProfileSection(String title, List<Widget> children, Color color) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
              color: color, // Use the color directly instead of color[700]
            ),
          ),
          SizedBox(height: 8),
          ...children,
        ],
      ),
    );
  }

  // Helper method to build profile info rows
  Widget _buildProfileInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
                fontSize: 14,
              ),
            ),
          ),
          SizedBox(width: 16),
          Expanded(
            flex: 3,
            child: Text(
              value,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 14,
                color: Colors.black87,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Food Tracking - ${_formatDate(widget.date)}'),
        backgroundColor: AppColors.primary,
        foregroundColor: const Color.fromARGB(255, 251, 241, 241),
        actions: [
          // Add profile button
          IconButton(
            onPressed: _showCurrentUserProfile,
            icon: Icon(Icons.person),
            tooltip: 'View Current User Profile',
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // User Profile Info Card
              if (_userProfile != null) ...[
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        Icon(
                          Icons.person,
                          color: Colors.blue[700],
                          size: 28,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Welcome, $_username',
                                style: Theme.of(context).textTheme.titleLarge,
                              ),
                              const SizedBox(height: 8),
                              // Pregnancy Week Display with Loading
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Colors.yellow[100],
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(color: Colors.yellow[300]!),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    if (_isLoadingUserData)
                                      SizedBox(
                                        width: 16,
                                        height: 16,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          valueColor: AlwaysStoppedAnimation<Color>(Colors.pink[600]!),
                                        ),
                                      )
                                    else
                                      Icon(Icons.pregnant_woman, size: 16, color: Colors.pink[600]),
                                    const SizedBox(width: 4),
                                    Text(
                                      _isLoadingUserData ? 'Loading...' : 'Week $_pregnancyWeek',
                                      style: TextStyle(
                                        color: Colors.yellow[800],
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 8),
                              
                              // Pregnancy Info Update Buttons
                              Row(
                                children: [
                                  ElevatedButton.icon(
                                    onPressed: _isLoadingUserData ? null : _updatePregnancyInfo,
                                    icon: Icon(Icons.update, size: 16),
                                    label: Text('Update', style: TextStyle(fontSize: 12)),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.pink[100],
                                      foregroundColor: Colors.pink[800],
                                      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                      minimumSize: Size(0, 32),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  ElevatedButton.icon(
                                    onPressed: _isLoadingUserData ? null : _fetchUserProfile,
                                    icon: Icon(Icons.refresh, size: 16),
                                    label: Text('Refresh', style: TextStyle(fontSize: 12)),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.blue[100],
                                      foregroundColor: Colors.blue[800],
                                      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                      minimumSize: Size(0, 32),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 16),
              // Simple and Reliable Food Input Section
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.grey.withOpacity(0.1),
                      spreadRadius: 1,
                      blurRadius: 5,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.restaurant, color: Colors.orange[600]),
                        const SizedBox(width: 8),
                        Text(
                          'Food Input & Analysis',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Describe what you ate in detail:',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _foodController,
                      maxLines: 3,
                      decoration: InputDecoration(
                        hintText: 'Example: I had a medium apple, 1 cup of yogurt with berries, and a slice of whole wheat toast with peanut butter for breakfast.',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: Colors.grey[300]!),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(color: Colors.blue[400]!),
                        ),
                        filled: true,
                        fillColor: Colors.grey[50],
                      ),
                    ),
                    const SizedBox(height: 16),
                                         Row(
                       children: [
                         Expanded(
                           child: ElevatedButton.icon(
                             onPressed: _analyzeNutrition,
                             icon: Icon(Icons.psychology, color: Colors.white),
                             label: Text('Analyze with AI'),
                             style: ElevatedButton.styleFrom(
                               backgroundColor: Colors.green[600],
                               foregroundColor: Colors.white,
                               padding: const EdgeInsets.symmetric(vertical: 12),
                               shape: RoundedRectangleBorder(
                                 borderRadius: BorderRadius.circular(8),
                               ),
                             ),
                           ),
                         ),
                       ],
                     ),
                     const SizedBox(height: 12),
                     Row(
                       children: [
                         Expanded(
                           child: ElevatedButton.icon(
                             onPressed: _openDetailedFoodEntry,
                             icon: Icon(Icons.add_circle, color: Colors.white),
                             label: Text('Add Detailed Food Entry'),
                             style: ElevatedButton.styleFrom(
                               backgroundColor: Colors.blue[600],
                               foregroundColor: Colors.white,
                               padding: const EdgeInsets.symmetric(vertical: 12),
                               shape: RoundedRectangleBorder(
                                 borderRadius: BorderRadius.circular(8),
                               ),
                             ),
                           ),
                         ),
                       ],
                     ),
                    if (_isAnalyzing) ...[
                      const SizedBox(height: 16),
                      Center(
                        child: Column(
                          children: [
                            CircularProgressIndicator(color: Colors.green[600]),
                            const SizedBox(height: 8),
                            Text(
                              'AI is analyzing your food...',
                              style: TextStyle(color: Colors.grey[600]),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Meal Type',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          SizedBox(
                            width: MediaQuery.of(context).size.width * 0.4,
                            child: _buildMealTypeButton('breakfast', 'Breakfast', Icons.wb_sunny),
                          ),
                          SizedBox(
                            width: MediaQuery.of(context).size.width * 0.4,
                            child: _buildMealTypeButton('lunch', 'Lunch', Icons.restaurant),
                          ),
                          SizedBox(
                            width: MediaQuery.of(context).size.width * 0.4,
                            child: _buildMealTypeButton('dinner', 'Dinner', Icons.nights_stay),
                          ),
                          SizedBox(
                            width: MediaQuery.of(context).size.width * 0.4,
                            child: _buildMealTypeButton('snack', 'Snack', Icons.coffee),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Column(
                        children: [
                          // Pregnancy Week Display (Auto-fetched from Backend)
                          Container(
                            width: double.infinity,
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Colors.pink[50],
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.pink[200]!),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Icon(Icons.pregnant_woman, color: Colors.pink[600], size: 20),
                                    const SizedBox(width: 8),
                                    Text(
                                      'Pregnancy Week',
                                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                        color: Colors.pink[800],
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                    const Spacer(),
                                    if (_isLoadingUserData)
                                      const SizedBox(
                                        width: 16,
                                        height: 16,
                                        child: CircularProgressIndicator(strokeWidth: 2),
                                      )
                                    else
                                      IconButton(
                                        onPressed: _fetchUserProfile,
                                        icon: Icon(Icons.refresh, color: Colors.blue[600], size: 18),
                                        tooltip: 'Refresh pregnancy info',
                                        padding: EdgeInsets.zero,
                                        constraints: const BoxConstraints(),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Row(
                                  children: [
                                    Text(
                                      'Current Week: ',
                                      style: TextStyle(
                                        color: Colors.pink[700],
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    Text(
                                      '$_pregnancyWeek',
                                      style: TextStyle(
                                        color: Colors.pink[800],
                                        fontWeight: FontWeight.bold,
                                        fontSize: 18,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '✅ Automatically fetched from backend',
                                  style: TextStyle(
                                    color: Colors.green[700],
                                    fontSize: 12,
                                    fontStyle: FontStyle.italic,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Based on your profile data',
                                  style: TextStyle(
                                    color: Colors.grey[600],
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),
                          TextField(
                            controller: _notesController,
                            decoration: const InputDecoration(
                              labelText: 'Additional Notes',
                              hintText: 'e.g., Portion size, time, how you felt...',
                              border: OutlineInputBorder(),
                            ),
                            maxLines: 2,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Column(
                        children: [
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: _isSaving ? null : _saveFoodEntry,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green,
                                foregroundColor: Colors.white,
                              ),
                              child: _isSaving
                                  ? const SizedBox(
                                      height: 20,
                                      width: 20,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                      ),
                                    )
                                  : const Text('Save Food Entry'),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              if (_foodController.text.isNotEmpty) ...[
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Transcribed Text',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.grey[100],
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(_foodController.text),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
              // Displaying Enhanced Nutrition Analysis with Daily Calorie Tracking
      if (_nutritionAnalysis != null) ...[
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.psychology, color: Colors.green[700], size: 24),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Enhanced Nutrition Analysis',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: Colors.green[700],
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                
                // Daily Calorie Tracking Section
                if (_nutritionAnalysis!['daily_calorie_tracking'] != null) ...[
                  Text(
                    '📊 Daily Calorie Tracking',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.blue[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.blue[200]!),
                    ),
                    child: Column(
                      children: [
                        _buildCalorieRow('Minimum Daily Calories', '${_nutritionAnalysis!['daily_calorie_tracking']['minimum_daily_calories'] ?? 0} kcal', Colors.blue),
                        _buildCalorieRow('Recommended Daily Calories', '${_nutritionAnalysis!['daily_calorie_tracking']['recommended_daily_calories'] ?? 0} kcal', Colors.green),
                        _buildCalorieRow('Calories Contributed', '${_nutritionAnalysis!['daily_calorie_tracking']['calories_contributed'] ?? 0} kcal', Colors.orange),
                        _buildCalorieRow('Percentage of Daily Needs', '${_nutritionAnalysis!['daily_calorie_tracking']['percentage_of_daily_needs'] ?? 0}%', Colors.purple),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                
                // Remaining Calories Section
                if (_nutritionAnalysis!['remaining_calories'] != null) ...[
                  Text(
                    '🍽️ Remaining Calories Today',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.orange[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.orange[200]!),
                    ),
                    child: Column(
                      children: [
                        _buildCalorieRow('Calories Remaining', '${_nutritionAnalysis!['remaining_calories']['calories_remaining'] ?? 0} kcal', Colors.orange),
                        _buildCalorieRow('Meals Remaining', '${_nutritionAnalysis!['remaining_calories']['meals_remaining'] ?? 0} meals', Colors.red),
                        _buildCalorieRow('Calories per Remaining Meal', '${_nutritionAnalysis!['remaining_calories']['calories_per_remaining_meal'] ?? 0} kcal', Colors.green),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                
                // Calculated nutrition values from GPT
                if (_nutritionAnalysis!['nutritional_breakdown'] != null) ...[
                  Text(
                    '🍎 Calculated Values from GPT-4:',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.green[800],
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  // Nutrition breakdown in a grid
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.green[200]!),
                    ),
                    child: Column(
                      children: [
                        _buildNutritionRow('Calories', '${_nutritionAnalysis!['nutritional_breakdown']['estimated_calories'] ?? 0} kcal', Colors.orange),
                        _buildNutritionRow('Protein', '${_nutritionAnalysis!['nutritional_breakdown']['protein_grams'] ?? 0} g', Colors.red),
                        _buildNutritionRow('Carbs', '${_nutritionAnalysis!['nutritional_breakdown']['carbohydrates_grams'] ?? 0} g', Colors.blue),
                        _buildNutritionRow('Fat', '${_nutritionAnalysis!['nutritional_breakdown']['fat_grams'] ?? 0} g', Colors.purple),
                        _buildNutritionRow('Fiber', '${_nutritionAnalysis!['nutritional_breakdown']['fiber_grams'] ?? 0} g', Colors.green),
                      ],
                    ),
                  ),
                ],
                
                const SizedBox(height: 16),
                
                // Smart Tips for Today Section
                if (_nutritionAnalysis!['smart_tips_for_today'] != null) ...[
                  Text(
                    '💡 Smart Tips for Today',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.teal[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.teal[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.teal[200]!),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (_nutritionAnalysis!['smart_tips_for_today']['next_meal_suggestions'] != null) ...[
                          _buildTipRow('🍽️ Next Meal Suggestions', _nutritionAnalysis!['smart_tips_for_today']['next_meal_suggestions']),
                          const SizedBox(height: 8),
                        ],
                        if (_nutritionAnalysis!['smart_tips_for_today']['best_combinations'] != null) ...[
                          _buildTipRow('🌟 Best Food Combinations', _nutritionAnalysis!['smart_tips_for_today']['best_combinations']),
                          const SizedBox(height: 8),
                        ],
                        if (_nutritionAnalysis!['smart_tips_for_today']['hydration_tips'] != null) ...[
                          _buildTipRow('💧 Hydration Tips', _nutritionAnalysis!['smart_tips_for_today']['hydration_tips']),
                          const SizedBox(height: 8),
                        ],
                        if (_nutritionAnalysis!['smart_tips_for_today']['pregnancy_week_specific_advice'] != null) ...[
                          _buildTipRow('👶 Week $_pregnancyWeek Specific Advice', _nutritionAnalysis!['smart_tips_for_today']['pregnancy_week_specific_advice']),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                
                // Pregnancy Benefits and Tips
                if (_nutritionAnalysis!['pregnancy_benefits'] != null && 
                    _nutritionAnalysis!['pregnancy_benefits'].toString().isNotEmpty) ...[
                  Text(
                    '🤱 Pregnancy Benefits & Tips:',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.pink[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.pink[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.pink[200]!),
                    ),
                    child: Text(
                      _nutritionAnalysis!['pregnancy_benefits'].toString(),
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        height: 1.4,
                        color: Colors.pink[800],
                      ),
                    ),
                  ),
                ],
                
                const SizedBox(height: 12),
                
                // Safety Considerations
                if (_nutritionAnalysis!['safety_considerations'] != null && 
                    _nutritionAnalysis!['safety_considerations'].toString().isNotEmpty) ...[
                  Text(
                    '⚠️ Safety Considerations:',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.orange[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.orange[200]!),
                    ),
                    child: Text(
                      _nutritionAnalysis!['safety_considerations'].toString(),
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        height: 1.4,
                        color: Colors.orange[800],
                      ),
                    ),
                  ),
                ],
                
                const SizedBox(height: 12),
                
                // Portion Recommendations
                if (_nutritionAnalysis!['portion_recommendations'] != null && 
                    _nutritionAnalysis!['portion_recommendations'].toString().isNotEmpty) ...[
                  Text(
                    '🍽️ Portion Recommendations:',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.blue[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.blue[200]!),
                    ),
                    child: Text(
                      _nutritionAnalysis!['portion_recommendations'].toString(),
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        height: 1.4,
                        color: Colors.blue[800],
                      ),
                    ),
                  ),
                ],
                
                const SizedBox(height: 12),
                
                // Alternative Suggestions
                if (_nutritionAnalysis!['alternative_suggestions'] != null && 
                    _nutritionAnalysis!['alternative_suggestions'].toString().isNotEmpty) ...[
                  Text(
                    '🔄 Alternative Suggestions:',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Colors.teal[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.teal[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.teal[200]!),
                    ),
                    child: Text(
                      _nutritionAnalysis!['alternative_suggestions'].toString(),
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        height: 1.4,
                        color: Colors.teal[800],
                      ),
                    ),
                  ),
                ],
                
                const SizedBox(height: 16),
                
                // Analysis Source
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.verified, color: Colors.green[600], size: 16),
                      const SizedBox(width: 8),
                      Text(
                        'Enhanced analysis provided by GPT-4',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
               ],
        
        // Daily Calorie Summary Button
        _buildDailyCalorieSummaryCard(),
      ],
    ),
  ),
),
);
}

  // Daily Calorie Summary Button
  Widget _buildDailyCalorieSummaryCard() {
    return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '📊 Daily Calorie Summary',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              
              ElevatedButton.icon(
                onPressed: _isLoadingUserData ? null : _fetchDailyCalorieSummary,
                icon: Icon(Icons.analytics, size: 18),
                label: Text('Get Today\'s Calorie Summary'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue[600],
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
              ),
              
              if (_dailyCalorieSummary != null) ...[
                const SizedBox(height: 16),
                
                // Today's Summary
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue[200]!),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Today\'s Summary (${_dailyCalorieSummary!['date']})',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Colors.blue[700],
                        ),
                      ),
                      const SizedBox(height: 8),
                      
                      _buildCalorieRow('Total Calories Today', '${_dailyCalorieSummary!['daily_summary']['total_calories_today']} kcal', Colors.blue),
                      _buildCalorieRow('Total Protein', '${_dailyCalorieSummary!['daily_summary']['total_protein_today']} g', Colors.red),
                      _buildCalorieRow('Total Carbs', '${_dailyCalorieSummary!['daily_summary']['total_carbs_today']} g', Colors.green),
                      _buildCalorieRow('Total Fat', '${_dailyCalorieSummary!['daily_summary']['total_fat_today']} g', Colors.orange),
                      _buildCalorieRow('Meals Eaten', '${_dailyCalorieSummary!['daily_summary']['meals_eaten_today']} meals', Colors.purple),
                    ],
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // Calorie Recommendations
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.green[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.green[200]!),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Calorie Recommendations',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Colors.green[700],
                        ),
                      ),
                      const SizedBox(height: 8),
                      
                      _buildCalorieRow('Recommended Daily Calories', '${_dailyCalorieSummary!['calorie_recommendations']['recommended_daily_calories']} kcal', Colors.green),
                      _buildCalorieRow('Calories Remaining', '${_dailyCalorieSummary!['calorie_recommendations']['calories_remaining']} kcal', Colors.orange),
                      _buildCalorieRow('Meals Remaining', '${_dailyCalorieSummary!['calorie_recommendations']['meals_remaining']} meals', Colors.red),
                      _buildCalorieRow('Calories per Remaining Meal', '${_dailyCalorieSummary!['calorie_recommendations']['calories_per_remaining_meal']} kcal', Colors.green),
                      _buildCalorieRow('Progress', '${_dailyCalorieSummary!['calorie_recommendations']['percentage_of_daily_needs']}%', Colors.blue),
                    ],
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // Smart Tips
                if (_dailyCalorieSummary!['smart_tips'] != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.teal[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.teal[200]!),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '💡 Smart Tips for Today',
                          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Colors.teal[700],
                          ),
                        ),
                        const SizedBox(height: 8),
                        
                        ...(_dailyCalorieSummary!['smart_tips'] as List<dynamic>).map<Widget>((tip) => Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Text(
                            '• $tip',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.teal[800],
                            ),
                          ),
                        )).toList(),
                      ],
                    ),
                  ),
                ],
              ],
            ],
          ),
        ),
      );
  }

  Widget _buildMealTypeButton(String mealType, String label, IconData icon) {
    final isSelected = _selectedMealType == mealType;
    return ElevatedButton(
      onPressed: () {
        setState(() {
          _selectedMealType = mealType;
        });
      },
      style: ElevatedButton.styleFrom(
        backgroundColor: isSelected ? Colors.orange : Colors.grey[300],
        foregroundColor: isSelected ? Colors.white : Colors.black87,
        padding: const EdgeInsets.symmetric(vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      child: Column(
        children: [
          Icon(icon, size: 20),
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Widget _buildNutritionRow(String label, String value, Color? color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: color)),
        Text(value, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }

  Widget _buildCalorieRow(String label, String value, Color? color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: color)),
          Text(value, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  Widget _buildTipRow(String title, String content) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(content, style: Theme.of(context).textTheme.bodyMedium),
      ],
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
  
  // Method to open detailed food entry window
  void _openDetailedFoodEntry() async {
    // Use the pregnancy week fetched from backend
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => DetailedFoodEntryScreen(
          userId: _userId,
          username: _username,
          email: _email,
          pregnancyWeek: _pregnancyWeek, // Use fetched value
          onFoodSaved: (foodData) {
            setState(() {
              // Refresh logic if needed
            });
          },
        ),
      ),
    );
  }
} 