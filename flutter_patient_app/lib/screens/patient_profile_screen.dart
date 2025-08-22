import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../utils/constants.dart';

class PatientProfileScreen extends StatefulWidget {
  const PatientProfileScreen({Key? key}) : super(key: key);

  @override
  State<PatientProfileScreen> createState() => _PatientProfileScreenState();
}

class _PatientProfileScreenState extends State<PatientProfileScreen> {
  bool _isLoading = true;
  Map<String, dynamic>? _profileData;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchCurrentUserProfile();
  }

  Future<void> _fetchCurrentUserProfile() async {
    try {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });

      print('🔍 Fetching current user profile...');
      
      // Get current login user info from AuthProvider
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      print('🔍 User info received: ${json.encode(userInfo)}');
      
      // Fix: Use the correct key from getCurrentUserInfo
      final String? patientId = userInfo['userId'];
      if (patientId == null || patientId.isEmpty) {
        throw Exception('Patient ID not found. Please ensure you are logged in.');
      }

      print('🔍 Found patient ID: $patientId');
      print('🔍 Using API URL: ${ApiConfig.baseUrl}/get-patient-profile/$patientId');
      
      // Fetch profile from backend
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/get-patient-profile/$patientId'),
        headers: {'Content-Type': 'application/json'},
      );

      print('🔍 HTTP Response Status: ${response.statusCode}');
      print('🔍 HTTP Response Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('✅ Profile response: ${json.encode(data)}');
        
        if (data['success'] == true) {
          // Handle different response formats
          Map<String, dynamic> profileData;
          if (data.containsKey('profile')) {
            profileData = data['profile'];
          } else if (data.containsKey('data')) {
            profileData = data['data'];
          } else {
            // If no specific profile wrapper, use the data directly
            profileData = Map<String, dynamic>.from(data);
            // Remove success and message fields
            profileData.remove('success');
            profileData.remove('message');
          }
          
          setState(() {
            _profileData = profileData;
            _isLoading = false;
          });
          
          print('✅ Profile loaded successfully');
          print('✅ Profile data keys: ${_profileData!.keys.toList()}');
          print('✅ Sample data:');
          print('   Username: ${_profileData!['username']}');
          print('   Email: ${_profileData!['email']}');
          print('   Blood Type: ${_profileData!['blood_type']}');
          print('   Height: ${_profileData!['height']}');
          print('   Weight: ${_profileData!['weight']}');
          print('   Pregnancy Week: ${_profileData!['pregnancy_week']}');
        } else {
          throw Exception(data['message'] ?? 'Failed to fetch profile');
        }
      } else if (response.statusCode == 404) {
        throw Exception('Patient profile not found. Please complete your profile first.');
      } else {
        throw Exception('HTTP Error: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      print('❌ Error fetching profile: $e');
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Complete Profile'),
        backgroundColor: Colors.purple,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            onPressed: _fetchCurrentUserProfile,
            icon: Icon(Icons.refresh),
            tooltip: 'Refresh Profile',
          ),
          IconButton(
            onPressed: () async {
              // Test API connection
              try {
                print('🧪 Testing API connection...');
                final response = await http.get(
                  Uri.parse('${ApiConfig.baseUrl}/'),
                  headers: {'Content-Type': 'application/json'},
                );
                print('🧪 API test response: ${response.statusCode}');
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('API Status: ${response.statusCode}'),
                    backgroundColor: response.statusCode == 200 ? Colors.green : Colors.orange,
                  ),
                );
              } catch (e) {
                print('🧪 API test error: $e');
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('API Error: $e'),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            icon: Icon(Icons.bug_report),
            tooltip: 'Test API Connection',
          ),
        ],
      ),
      body: _isLoading
          ? _buildLoadingWidget()
          : _errorMessage != null
              ? _buildErrorWidget()
              : _profileData == null
                  ? _buildEmptyProfileWidget()
                  : _buildProfileContent(),
    );
  }

  Widget _buildLoadingWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: Colors.purple),
          SizedBox(height: 16),
          Text('Loading profile...', style: TextStyle(fontSize: 16, color: Colors.grey[600])),
          SizedBox(height: 8),
          Text(
            'Please wait while we fetch your information',
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  bool _isProfileDataValid() {
    if (_profileData == null) return false;
    
    // Check if we have at least basic user information
    final hasBasicInfo = _profileData!['username'] != null && 
                         _profileData!['username'].toString().isNotEmpty &&
                         _profileData!['email'] != null && 
                         _profileData!['email'].toString().isNotEmpty;
    
    print('🔍 Profile validation:');
    print('   Has basic info: $hasBasicInfo');
    print('   Username: ${_profileData!['username']}');
    print('   Email: ${_profileData!['email']}');
    print('   Data keys: ${_profileData!.keys.toList()}');
    
    return hasBasicInfo;
  }

  Widget _buildProfileContent() {
    if (_profileData == null || !_isProfileDataValid()) {
      return _buildEmptyProfileWidget();
    }

    // Check if profile is complete
    final bool isProfileComplete = _profileData!['first_name'] != null && 
                                 _profileData!['first_name'].toString().isNotEmpty &&
                                 _profileData!['last_name'] != null && 
                                 _profileData!['last_name'].toString().isNotEmpty;

    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Profile Header
          _buildProfileHeader(),
          SizedBox(height: 24),
          
          // Profile Completion Notice
          if (!isProfileComplete) ...[
            Card(
              elevation: 3,
              color: Colors.orange[50],
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: EdgeInsets.all(20),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Icon(Icons.warning_amber, color: Colors.orange[700], size: 24),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Profile Incomplete',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.orange[700],
                              fontSize: 16,
                            ),
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 12),
                    Text(
                      'Your profile information is incomplete. Please complete your profile to access all features.',
                      style: TextStyle(color: Colors.orange[600]),
                    ),
                    SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {
                          // Navigate to profile completion screen
                          Navigator.pushNamed(context, '/complete-profile');
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.orange[600],
                          foregroundColor: Colors.white,
                          padding: EdgeInsets.symmetric(vertical: 12),
                        ),
                        child: Text('Complete Profile'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(height: 16),
          ],
          
          // Personal Information
          _buildProfileSection(
            '👤 Personal Information',
            Icons.person,
            Colors.blue,
            [
              _buildInfoRow('Full Name', '${_formatValue(_profileData!['first_name'])} ${_formatValue(_profileData!['last_name'])}'),
              _buildInfoRow('Username', _formatValue(_profileData!['username'])),
              _buildInfoRow('Email', _formatValue(_profileData!['email'])),
              _buildInfoRow('Mobile', _formatValue(_profileData!['mobile'])),
              _buildInfoRow('Age', _formatValue(_profileData!['age'], suffix: ' years')),
              _buildInfoRow('Date of Birth', _formatDate(_profileData!['date_of_birth'])),
            ],
          ),
          
          SizedBox(height: 16),
          
          // Health Information
          _buildProfileSection(
            '🏥 Health Information',
            Icons.health_and_safety,
            Colors.pink,
            [
              _buildInfoRow('Blood Type', _formatValue(_profileData!['blood_type'])),
              _buildInfoRow('Height', _formatValue(_profileData!['height'], suffix: ' cm')),
              _buildInfoRow('Weight', _formatValue(_profileData!['weight'], suffix: ' kg')),
              _buildInfoRow('Pregnancy Status', _profileData!['is_pregnant'] == true ? 'Yes' : 'No'),
              if (_profileData!['is_pregnant'] == true) ...[
                _buildInfoRow('Pregnancy Week', 'Week ${_formatValue(_profileData!['pregnancy_week'])}'),
                _buildInfoRow('Last Period Date', _formatDate(_profileData!['last_period_date'])),
                _buildInfoRow('Expected Delivery', _formatDate(_profileData!['expected_delivery_date'])),
              ],
            ],
          ),
          
          SizedBox(height: 16),
          
          // Account Information
          _buildProfileSection(
            '🔐 Account Information',
            Icons.account_circle,
            Colors.purple,
            [
              _buildInfoRow('Patient ID', _formatValue(_profileData!['patient_id'])),
              _buildInfoRow('Status', _formatValue(_profileData!['status'])),
              _buildInfoRow('Email Verified', _profileData!['email_verified'] == true ? 'Yes' : 'No'),
              _buildInfoRow('Profile Completed', _formatDate(_profileData!['profile_completed_at'])),
              _buildInfoRow('Last Updated', _formatDate(_profileData!['last_updated'])),
            ],
          ),
          
          SizedBox(height: 16),
          
          // Emergency Contact
          if (_profileData!['emergency_contact'] != null && 
              _profileData!['emergency_contact']['name'] != null &&
              _profileData!['emergency_contact']['name'].toString().isNotEmpty) ...[
            _buildProfileSection(
              '🚨 Emergency Contact',
              Icons.emergency,
              Colors.red,
              [
                _buildInfoRow('Name', _formatValue(_profileData!['emergency_contact']['name'])),
                _buildInfoRow('Phone', _formatValue(_profileData!['emergency_contact']['phone'])),
                _buildInfoRow('Relationship', _formatValue(_profileData!['emergency_contact']['relationship'])),
              ],
            ),
            SizedBox(height: 16),
          ],
          
          // Edit Profile Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                // Navigate to profile editing screen
                Navigator.pushNamed(context, '/complete-profile');
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.purple,
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: Text(
                isProfileComplete ? 'Edit Profile' : 'Complete Profile',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileHeader() {
    final String firstName = _formatValue(_profileData!['first_name']);
    final String lastName = _formatValue(_profileData!['last_name']);
    final String fullName = '${firstName} ${lastName}'.trim();
    final String displayName = fullName.isNotEmpty && fullName != 'Not set Not set' ? fullName : 'Complete Your Profile';
    
    return Card(
      elevation: 6,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Colors.purple[400]!, Colors.purple[600]!],
          ),
        ),
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Column(
            children: [
              Container(
                padding: EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
                child: CircleAvatar(
                  radius: 50,
                  backgroundColor: Colors.purple[100],
                  child: Icon(Icons.person, size: 50, color: Colors.purple[600]),
                ),
              ),
              SizedBox(height: 16),
              Text(
                displayName,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 8),
              Text(
                _formatValue(_profileData!['username'], fallback: 'Username not set'),
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: Colors.white70,
                ),
              ),
              SizedBox(height: 16),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white.withOpacity(0.3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _profileData!['is_pregnant'] == true ? Icons.pregnant_woman : Icons.person,
                      color: Colors.white,
                      size: 20,
                    ),
                    SizedBox(width: 8),
                    Text(
                      _profileData!['is_pregnant'] == true ? 'Pregnant' : 'Patient',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileSection(String title, IconData icon, Color color, List<Widget> children) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: color, size: 24),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 20),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.only(bottom: 16),
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
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
          SizedBox(height: 16),
          Text('Error loading profile', style: Theme.of(context).textTheme.titleLarge),
          SizedBox(height: 8),
          Text(
            _errorMessage ?? 'Unknown error occurred',
            textAlign: TextAlign.center, 
            style: TextStyle(color: Colors.grey[600])
          ),
          SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ElevatedButton.icon(
                onPressed: _fetchCurrentUserProfile,
                icon: Icon(Icons.refresh),
                label: Text('Retry'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purple,
                  foregroundColor: Colors.white,
                ),
              ),
              ElevatedButton.icon(
                onPressed: () {
                  // Navigate to profile completion screen
                  Navigator.pushNamed(context, '/complete-profile');
                },
                icon: Icon(Icons.edit),
                label: Text('Complete Profile'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange[600],
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyProfileWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.person_add, size: 64, color: Colors.purple[300]),
          SizedBox(height: 16),
          Text(
            'No Profile Data Found',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: Colors.grey[700],
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'It looks like your profile hasn\'t been created yet or there was an issue loading it.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[600],
            ),
          ),
          SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () {
                // Navigate to profile completion screen
                Navigator.pushNamed(context, '/complete-profile');
              },
              icon: Icon(Icons.add),
              label: Text('Create Profile'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.purple,
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
          SizedBox(height: 16),
          TextButton.icon(
            onPressed: _fetchCurrentUserProfile,
            icon: Icon(Icons.refresh),
            label: Text('Try Again'),
            style: TextButton.styleFrom(
              foregroundColor: Colors.purple,
            ),
          ),
        ],
      ),
    );
  }

  String _formatValue(dynamic value, {String suffix = '', String fallback = 'Not set'}) {
    if (value == null || value.toString().isEmpty) {
      return fallback;
    }
    
    if (suffix.isNotEmpty) {
      return '$value$suffix';
    }
    
    return value.toString();
  }

  String _formatDate(dynamic dateValue) {
    if (dateValue == null || dateValue.toString().isEmpty) {
      return 'Not set';
    }
    
    try {
      // Try to parse the date if it's a string
      if (dateValue is String) {
        // Check if it's already in DD/MM/YYYY format
        if (dateValue.contains('/') && dateValue.split('/').length == 3) {
          final parts = dateValue.split('/');
          if (parts.length == 3) {
            final day = int.parse(parts[0]);
            final month = int.parse(parts[1]);
            final year = int.parse(parts[2]);
            return '${day.toString().padLeft(2, '0')}/${month.toString().padLeft(2, '0')}/${year}';
          }
        }
        
        // Try to parse as ISO format
        try {
          final date = DateTime.parse(dateValue);
          return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
        } catch (e) {
          // If ISO parsing fails, return the original string
          return dateValue;
        }
      }
      return dateValue.toString();
    } catch (e) {
      return dateValue.toString();
    }
  }
}
