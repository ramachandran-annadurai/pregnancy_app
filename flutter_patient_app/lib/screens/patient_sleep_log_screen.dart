import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import 'dart:convert'; // Added for json.encode

class PatientSleepLogScreen extends StatefulWidget {
  final String userId;
  final String userRole;
  final String username;
  final String email;

  const PatientSleepLogScreen({
    Key? key,
    required this.userId,
    required this.userRole,
    required this.username,
    required this.email,
  }) : super(key: key);

  @override
  State<PatientSleepLogScreen> createState() => _PatientSleepLogScreenState();
}

class _PatientSleepLogScreenState extends State<PatientSleepLogScreen> {
  TimeOfDay _startTime = TimeOfDay(hour: 22, minute: 0); // 10:00 PM
  TimeOfDay _endTime = TimeOfDay(hour: 6, minute: 0); // 6:00 AM
  bool _smartAlarmEnabled = false;
  String? _selectedSleepRating;
  final TextEditingController _notesController = TextEditingController();
  bool _isLoading = false;

  // Sleep rating options
  final List<String> _sleepRatings = ['Poor', 'Fair', 'Good', 'Excellent'];

  @override
  void initState() {
    super.initState();
    _calculateTotalSleep();
    
    // Debug logging to see what arguments were received
    print('🔍 Sleep Log Screen Debug - Received Arguments:');
    print('  Email: ${widget.email}');
    print('  Username: ${widget.username}');
    print('  UserId: ${widget.userId}');
    print('  UserRole: ${widget.userRole}');
  }

  void _calculateTotalSleep() {
    setState(() {});
  }

  Duration get _totalSleepDuration {
    final start = DateTime(2024, 1, 1, _startTime.hour, _startTime.minute);
    final end = DateTime(2024, 1, 1, _startTime.hour, _startTime.minute);
    
    Duration duration;
    if (_endTime.hour < _startTime.hour) {
      // Sleep crosses midnight
      final nextDay = DateTime(2024, 1, 2, _endTime.hour, _endTime.minute);
      duration = nextDay.difference(start);
    } else {
      duration = end.difference(start);
    }
    
    return duration;
  }

  String get _totalSleepText {
    final hours = _totalSleepDuration.inHours;
    final minutes = _totalSleepDuration.inMinutes % 60;
    if (minutes == 0) {
      return '$hours hours';
    }
    return '$hours hours $minutes minutes';
  }

  TimeOfDay get _optimalWakeUpTime {
    // Simple calculation: wake up 15 minutes after end time
    final optimalHour = _endTime.hour;
    final optimalMinute = (_endTime.minute + 15) % 60;
    return TimeOfDay(hour: optimalHour, minute: optimalMinute);
  }

  Future<void> _selectTime(BuildContext context, bool isStartTime) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: isStartTime ? _startTime : _endTime,
      builder: (BuildContext context, Widget? child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: Colors.purple,
              onPrimary: Colors.white,
              surface: Colors.white,
              onSurface: Colors.black,
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() {
        if (isStartTime) {
          _startTime = picked;
        } else {
          _endTime = picked;
        }
        _calculateTotalSleep();
      });
    }
  }

  Future<void> _saveSleepLog() async {
    if (_selectedSleepRating == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a sleep rating'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Get Patient ID from user info for precise patient linking
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      final String? patientId = userInfo['userId'];
      if (patientId == null) {
        throw Exception('Patient ID not found. Please ensure you are logged in.');
      }
      
      final sleepData = {
        'userId': patientId, // Use Patient ID for precise linking
        'userRole': widget.userRole,
        'username': widget.username,
        'startTime': '${_startTime.hour.toString().padLeft(2, '0')}:${_startTime.minute.toString().padLeft(2, '0')}',
        'endTime': '${_endTime.hour.toString().padLeft(2, '0')}:${_endTime.minute.toString().padLeft(2, '0')}',
        'totalSleep': _totalSleepText,
        'smartAlarmEnabled': _smartAlarmEnabled,
        'optimalWakeUpTime': '${_optimalWakeUpTime.hour.toString().padLeft(2, '0')}:${_optimalWakeUpTime.minute.toString().padLeft(2, '0')}',
        'sleepRating': _selectedSleepRating,
        'notes': _notesController.text.trim(),
        'timestamp': DateTime.now().toIso8601String(),
      };

      // EXTENSIVE DEBUG LOGGING
      print('🔍 ===== SLEEP LOG DEBUG START =====');
      print('🔍 Patient ID: $patientId');
      print('🔍 Sleep Data Map:');
      print('  - userId: ${sleepData['userId']}');
      print('  - userRole: ${sleepData['userRole']}');
      print('  - username: ${sleepData['username']}');
      print('  - startTime: ${sleepData['startTime']}');
      print('  - endTime: ${sleepData['endTime']}');
      print('  - totalSleep: ${sleepData['totalSleep']}');
      print('  - sleepRating: ${sleepData['sleepRating']}');
      print('🔍 Full JSON Data: ${json.encode(sleepData)}');
      print('🔍 ===== SLEEP LOG DEBUG END =====');

      final apiService = ApiService();
      final response = await apiService.saveSleepLog(sleepData);

      if (response['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Sleep log saved successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        
        // Navigate back to daily log page
        Navigator.pop(context);
      } else {
        throw Exception(response['message'] ?? 'Failed to save sleep log');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Sleep Log',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: Colors.purple,
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Sleep Time Input Section
            _buildSectionTitle('Sleep Time'),
            const SizedBox(height: 15),
            
            // Start Time
            _buildTimeInput(
              label: 'Start Time',
              time: _startTime,
              onTap: () => _selectTime(context, true),
            ),
            const SizedBox(height: 15),
            
            // End Time
            _buildTimeInput(
              label: 'End Time',
              time: _endTime,
              onTap: () => _selectTime(context, false),
            ),
            const SizedBox(height: 10),
            
            // Total Sleep Display
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: Text(
                'Total Sleep: $_totalSleepText',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[700],
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            
            const SizedBox(height: 30),
            
            // Smart Alarm Section
            _buildSectionTitle('Smart Alarm'),
            const SizedBox(height: 15),
            
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue[200]!),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.access_time,
                    color: Colors.blue[600],
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Optimal Wake-Up Time: ${_optimalWakeUpTime.format(context)}',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.blue[800],
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Wake up during a light sleep phase',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.blue[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 15),
            
            // Smart Alarm Toggle
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Enable Smart Alarm',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Switch(
                  value: _smartAlarmEnabled,
                  onChanged: (value) {
                    setState(() {
                      _smartAlarmEnabled = value;
                    });
                  },
                  activeColor: Colors.purple,
                ),
              ],
            ),
            
            const SizedBox(height: 30),
            
            // Sleep Rating Section
            _buildSectionTitle('Rate Your Sleep'),
            const SizedBox(height: 15),
            
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: _sleepRatings.map((rating) {
                final isSelected = _selectedSleepRating == rating;
                return GestureDetector(
                  onTap: () {
                    setState(() {
                      _selectedSleepRating = rating;
                    });
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    decoration: BoxDecoration(
                      color: isSelected ? Colors.purple : Colors.transparent,
                      borderRadius: BorderRadius.circular(25),
                      border: Border.all(
                        color: isSelected ? Colors.purple : Colors.grey[400]!,
                        width: 2,
                      ),
                    ),
                    child: Text(
                      rating,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: isSelected ? Colors.white : Colors.grey[700],
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            
            const SizedBox(height: 30),
            
            // Notes Section
            _buildSectionTitle('Notes'),
            const SizedBox(height: 15),
            
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: TextField(
                controller: _notesController,
                maxLines: 4,
                decoration: const InputDecoration(
                  hintText: 'Add any additional notes about your sleep...',
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(16),
                ),
                style: const TextStyle(fontSize: 16),
              ),
            ),
            
            const SizedBox(height: 40),
            
            // Save Button
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _saveSleepLog,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purple,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  elevation: 0,
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 24,
                        width: 24,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text(
                        'Save Sleep Log',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.bold,
        color: Colors.black87,
      ),
    );
  }

  Widget _buildTimeInput({
    required String label,
    required TimeOfDay time,
    required VoidCallback onTap,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.black87,
          ),
        ),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: Text(
              time.format(context),
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[700],
              ),
            ),
          ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }
} 