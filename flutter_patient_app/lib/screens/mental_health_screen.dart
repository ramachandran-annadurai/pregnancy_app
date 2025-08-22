import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import '../providers/auth_provider.dart';
import '../utils/constants.dart';
import '../utils/date_utils.dart';

class MentalHealthScreen extends StatefulWidget {
  final String? selectedDate;
  
  const MentalHealthScreen({super.key, this.selectedDate});

  @override
  State<MentalHealthScreen> createState() => _MentalHealthScreenState();
}

class _MentalHealthScreenState extends State<MentalHealthScreen>
    with TickerProviderStateMixin {
  late TabController _tabController;
  
  // Mood tracking
  String? _selectedMood;
  final TextEditingController _moodNoteController = TextEditingController();
  final List<Map<String, dynamic>> _moodOptions = [
    {'name': 'Happy', 'emoji': '😊', 'color': Colors.green},
    {'name': 'Calm', 'emoji': '😌', 'color': Colors.blue},
    {'name': 'Anxious', 'emoji': '😰', 'color': Colors.orange},
    {'name': 'Sad', 'emoji': '😢', 'color': Colors.indigo},
    {'name': 'Angry', 'emoji': '😠', 'color': Colors.red},
    {'name': 'Tired', 'emoji': '😴', 'color': Colors.grey},
    {'name': 'Overwhelmed', 'emoji': '😵', 'color': Colors.purple},
    {'name': 'Excited', 'emoji': '🤩', 'color': Colors.yellow},
  ];

  // Daily check-in
  bool _hasCheckedInToday = false;
  DateTime? _lastCheckInDate;
  
  // Mental health score
  double _mentalHealthScore = 7.0;
  final List<Map<String, dynamic>> _assessmentQuestions = [
    {
      'question': 'How would you rate your overall mood today?',
      'type': 'scale',
      'min': 1,
      'max': 10,
      'labels': ['Very Poor', 'Excellent']
    },
    {
      'question': 'How well did you sleep last night?',
      'type': 'scale',
      'min': 1,
      'max': 10,
      'labels': ['Very Poor', 'Excellent']
    },
    {
      'question': 'How stressed do you feel today?',
      'type': 'scale',
      'min': 1,
      'max': 10,
      'labels': ['Not Stressed', 'Very Stressed']
    },
    {
      'question': 'How motivated do you feel?',
      'type': 'scale',
      'min': 1,
      'max': 10,
      'labels': ['Not Motivated', 'Very Motivated']
    },
  ];

  // Progress tracking
  List<Map<String, dynamic>> _moodHistory = [];
  List<Map<String, dynamic>> _assessmentHistory = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadData();
    // Also load data from backend
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadDataFromBackend();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _moodNoteController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    final prefs = await SharedPreferences.getInstance();
    final lastCheckIn = prefs.getString('last_mood_checkin');
    
    if (lastCheckIn != null) {
      _lastCheckInDate = DateTime.parse(lastCheckIn);
      _hasCheckedInToday = _isSameDay(
        _lastCheckInDate!,
        DateTime.now(),
      );
    }

    // Load mood history
    final moodHistoryJson = prefs.getStringList('mood_history') ?? [];
    _moodHistory = moodHistoryJson
        .map((json) => Map<String, dynamic>.from(
            _parseJson(json)))
        .toList();

    // Load assessment history
    final assessmentHistoryJson = prefs.getStringList('assessment_history') ?? [];
    _assessmentHistory = assessmentHistoryJson
        .map((json) => Map<String, dynamic>.from(
            _parseJson(json)))
        .toList();

    setState(() {});
  }

  Future<void> _loadDataFromBackend() async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] == null) {
        return;
      }

      final patientId = userInfo['userId']!;
      
      // Get mental health history from backend
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/mental-health/history/$patientId'),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final responseData = json.decode(response.body);
        
        if (responseData['success'] == true) {
          final backendMoodHistory = responseData['data']['mood_history'] as List;
          final backendAssessmentHistory = responseData['data']['assessment_history'] as List;
          
          // Update local mood history with backend data
          setState(() {
            _moodHistory = backendMoodHistory.map((entry) => {
              'date': entry['date'],
              'mood': entry['mood'],
              'note': entry['note'] ?? '',
              'timestamp': DateTime.parse(entry['timestamp']).millisecondsSinceEpoch,
            }).toList();
            
            _assessmentHistory = backendAssessmentHistory.map((entry) => {
              'date': entry['date'],
              'score': entry['score'],
              'timestamp': DateTime.parse(entry['timestamp']).millisecondsSinceEpoch,
            }).toList();
          });

          // Save to local storage
          final prefs = await SharedPreferences.getInstance();
          final moodHistoryJson = _moodHistory
              .map((entry) => _toJson(entry))
              .toList();
          await prefs.setStringList('mood_history', moodHistoryJson);
          
          final assessmentHistoryJson = _assessmentHistory
              .map((entry) => _toJson(entry))
              .toList();
          await prefs.setStringList('assessment_history', assessmentHistoryJson);
        }
      }
    } catch (e) {
      print('❌ Error loading data from backend: $e');
    }
  }

  bool _isSameDay(DateTime date1, DateTime date2) {
    return date1.year == date2.year &&
           date1.month == date2.month &&
           date1.day == date2.day;
  }

  Map<String, dynamic> _parseJson(String jsonString) {
    try {
      return Map<String, dynamic>.from(
        json.decode(jsonString) as Map<String, dynamic>
      );
    } catch (e) {
      return {};
    }
  }

  String _toJson(Map<String, dynamic> data) {
    try {
      return json.encode(data);
    } catch (e) {
      return '{}';
    }
  }

  Future<void> _saveMoodCheckIn() async {
    if (_selectedMood == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a mood first')),
      );
      return;
    }

    try {
      // Get current user info
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('User not authenticated. Please login again.')),
        );
        return;
      }

      final patientId = userInfo['userId']!;
      final selectedDate = widget.selectedDate ?? "${DateTime.now().day}/${DateTime.now().month}/${DateTime.now().year}";
      
      // Prepare data for backend
      final moodData = {
        'patient_id': patientId,
        'mood': _selectedMood,
        'note': _moodNoteController.text.trim(),
        'date': selectedDate,
      };

      // Send to backend
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/mental-health/mood-checkin'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: json.encode(moodData),
      ).timeout(const Duration(seconds: 30));

      final responseData = json.decode(response.body);

      if (response.statusCode == 201 && responseData['success'] == true) {
        // Success - save locally and update UI
        final prefs = await SharedPreferences.getInstance();
        final now = DateTime.now();
        
        // Save check-in locally
        await prefs.setString('last_mood_checkin', now.toIso8601String());
        
        // Save mood entry locally
        final moodEntry = {
          'date': now.toIso8601String(),
          'mood': _selectedMood,
          'note': _moodNoteController.text.trim(),
          'timestamp': now.millisecondsSinceEpoch,
        };

        _moodHistory.add(moodEntry);
        final moodHistoryJson = _moodHistory
            .map((entry) => _toJson(entry))
            .toList();
        await prefs.setStringList('mood_history', moodHistoryJson);

        setState(() {
          _hasCheckedInToday = true;
          _lastCheckInDate = now;
          _moodNoteController.clear();
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Mood check-in saved successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        
        // Refresh data from backend
        _loadDataFromBackend();
        
      } else {
        // Handle backend errors
        String errorMessage = 'Failed to save mood check-in';
        if (responseData['message'] != null) {
          errorMessage = responseData['message'];
        }
        
        if (response.statusCode == 409) {
          // Already checked in today
          setState(() {
            _hasCheckedInToday = true;
            _lastCheckInDate = DateTime.now();
          });
          errorMessage = 'Already checked in for today';
        }
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage),
            backgroundColor: Colors.orange,
          ),
        );
      }
      
    } catch (e) {
      print('❌ Error saving mood check-in: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Network error. Please check your connection and try again.'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _saveAssessment() async {
    try {
      // Get current user info
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('User not authenticated. Please login again.')),
        );
        return;
      }

      final patientId = userInfo['userId']!;
      final selectedDate = widget.selectedDate ?? "${DateTime.now().day}/${DateTime.now().month}/${DateTime.now().year}";
      
      // Prepare data for backend
      final assessmentData = {
        'patient_id': patientId,
        'score': _mentalHealthScore,
        'date': selectedDate,
      };

      // Send to backend
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/mental-health/assessment'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: json.encode(assessmentData),
      ).timeout(const Duration(seconds: 30));

      final responseData = json.decode(response.body);

      if (response.statusCode == 201 && responseData['success'] == true) {
        // Success - save locally and update UI
        final prefs = await SharedPreferences.getInstance();
        final now = DateTime.now();
        
        final assessmentEntry = {
          'date': now.toIso8601String(),
          'score': _mentalHealthScore,
          'timestamp': now.millisecondsSinceEpoch,
        };

        _assessmentHistory.add(assessmentEntry);
        final assessmentHistoryJson = _assessmentHistory
            .map((entry) => _toJson(entry))
            .toList();
        await prefs.setStringList('assessment_history', assessmentHistoryJson);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Mental health assessment saved successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        
      } else {
        // Handle backend errors
        String errorMessage = 'Failed to save assessment';
        if (responseData['message'] != null) {
          errorMessage = responseData['message'];
        }
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage),
            backgroundColor: Colors.orange,
          ),
        );
      }
      
    } catch (e) {
      print('❌ Error saving assessment: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Network error. Please check your connection and try again.'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Widget _buildMoodCheckInTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 25,
                        backgroundColor: AppColors.primary,
                        child: const Icon(
                          Icons.psychology,
                          size: 30,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                                                         Text(
                               'Mental Health Check-in',
                               style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                 fontWeight: FontWeight.bold,
                                 color: AppColors.primary,
                               ),
                             ),
                             if (widget.selectedDate != null) ...[
                               Text(
                                 'Date: ${widget.selectedDate}',
                                 style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                   color: AppColors.primary,
                                   fontWeight: FontWeight.w500,
                                 ),
                               ),
                               const SizedBox(height: 4),
                             ],
                             Text(
                               'Track your daily mood and mental well-being',
                               style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                 color: Colors.grey[600],
                               ),
                             ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Mood Selection
          Text(
            'How are you feeling today?',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),

          // Mood Grid
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 1.2,
            ),
            itemCount: _moodOptions.length,
            itemBuilder: (context, index) {
              final mood = _moodOptions[index];
              final isSelected = _selectedMood == mood['name'];
              
              return GestureDetector(
                onTap: () {
                  setState(() {
                    _selectedMood = mood['name'];
                  });
                },
                child: Container(
                  decoration: BoxDecoration(
                    color: isSelected ? mood['color'].withOpacity(0.2) : Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isSelected ? mood['color'] : Colors.grey.shade300,
                      width: isSelected ? 2 : 1,
                    ),
                    boxShadow: isSelected ? [
                      BoxShadow(
                        color: mood['color'].withOpacity(0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ] : null,
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        mood['emoji'],
                        style: const TextStyle(fontSize: 24),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        mood['name'],
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: isSelected ? mood['color'] : Colors.grey[700],
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              );
            },
          ),

          const SizedBox(height: 24),

          // Mood Note
          Text(
            'Add a note (optional)',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _moodNoteController,
            maxLines: 3,
            decoration: InputDecoration(
              hintText: 'How was your day? What\'s on your mind?',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Colors.grey.shade50,
            ),
          ),

          const SizedBox(height: 24),

          // Submit Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _hasCheckedInToday ? null : _saveMoodCheckIn,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 2,
              ),
              child: Text(
                _hasCheckedInToday ? 'Already Checked In Today' : 'Submit Mood Check-in',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),

          if (_hasCheckedInToday) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.green.shade200),
              ),
              child: Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.green.shade600),
                  const SizedBox(width: 8),
                  Text(
                    'You\'ve already checked in today!',
                    style: TextStyle(
                      color: Colors.green.shade700,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 24),

          // Recent Mood History
          if (_moodHistory.isNotEmpty) ...[
            Text(
              'Recent Mood History',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _moodHistory.take(5).length,
              itemBuilder: (context, index) {
                final entry = _moodHistory[index];
                final mood = _moodOptions.firstWhere(
                  (m) => m['name'] == entry['mood'],
                  orElse: () => {'emoji': '😐', 'color': Colors.grey},
                );
                
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: Text(
                      mood['emoji'],
                      style: const TextStyle(fontSize: 24),
                    ),
                    title: Text(
                      entry['mood'],
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          AppDateUtils.formatDate(DateTime.parse(entry['date'])),
                          style: TextStyle(color: Colors.grey[600]),
                        ),
                        if (entry['note']?.isNotEmpty == true) ...[
                          const SizedBox(height: 4),
                          Text(
                            entry['note'],
                            style: TextStyle(
                              color: Colors.grey[700],
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ],
                      ],
                    ),
                    trailing: Icon(
                      Icons.arrow_forward_ios,
                      size: 16,
                      color: Colors.grey[400],
                    ),
                  ),
                );
              },
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAssessmentTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 25,
                        backgroundColor: Colors.blue,
                        child: const Icon(
                          Icons.assessment,
                          size: 30,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Mental Health Assessment',
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: Colors.blue,
                              ),
                            ),
                            Text(
                              'Rate your mental well-being on a scale of 1-10',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Assessment Questions
          Text(
            'Daily Mental Health Assessment',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),

          // Overall Score
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Overall Mental Health Score',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: Slider(
                          value: _mentalHealthScore,
                          min: 1.0,
                          max: 10.0,
                          divisions: 9,
                          activeColor: AppColors.primary,
                          inactiveColor: Colors.grey.shade300,
                          onChanged: (value) {
                            setState(() {
                              _mentalHealthScore = value;
                            });
                          },
                        ),
                      ),
                      const SizedBox(width: 16),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          _mentalHealthScore.toStringAsFixed(1),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '1 - Poor',
                        style: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 12,
                        ),
                      ),
                      Text(
                        '10 - Excellent',
                        style: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Submit Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _saveAssessment,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 2,
              ),
              child: const Text(
                'Save Assessment',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Assessment History
          if (_assessmentHistory.isNotEmpty) ...[
            Text(
              'Assessment History',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _assessmentHistory.take(7).length,
              itemBuilder: (context, index) {
                final entry = _assessmentHistory[index];
                final score = entry['score'] as double;
                Color scoreColor;
                
                if (score >= 8) scoreColor = Colors.green;
                else if (score >= 6) scoreColor = Colors.orange;
                else scoreColor = Colors.red;
                
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: scoreColor.withOpacity(0.2),
                      child: Text(
                        score.toStringAsFixed(1),
                        style: TextStyle(
                          color: scoreColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    title: Text(
                      'Mental Health Score',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Text(
                      AppDateUtils.formatDate(DateTime.parse(entry['date'])),
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                    trailing: Icon(
                      Icons.arrow_forward_ios,
                      size: 16,
                      color: Colors.grey[400],
                    ),
                  ),
                );
              },
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTipsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 25,
                        backgroundColor: Colors.green,
                        child: const Icon(
                          Icons.lightbulb,
                          size: 30,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Mental Health Tips',
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: Colors.green,
                              ),
                            ),
                            Text(
                              'Practical tips for better mental well-being',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Pregnancy Mental Health Overview
          Card(
            color: Colors.pink.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.favorite, color: Colors.pink.shade600, size: 24),
                      const SizedBox(width: 12),
                      Text(
                        'Pregnancy Mental Health',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: Colors.pink.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Pregnancy brings many emotional changes. It\'s normal to feel a mix of joy, anxiety, excitement, and worry. These tips help you maintain mental well-being during this special time.',
                    style: TextStyle(
                      color: Colors.pink.shade700,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Pregnancy Mental Health Tips
          Text(
            'Pregnancy Mental Health Tips',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),

          _buildTipCard(
            'Accept Your Feelings',
            'It\'s normal to feel anxious, excited, overwhelmed, or scared. All emotions are valid during pregnancy.',
            Icons.favorite,
            Colors.pink,
          ),
          _buildTipCard(
            'Practice Pregnancy Breathing',
            'Deep breathing helps with anxiety and prepares you for labor. Breathe in for 4, hold for 4, out for 6.',
            Icons.air,
            Colors.blue,
          ),
          _buildTipCard(
            'Stay Connected',
            'Talk to your partner, family, or friends about your pregnancy journey and feelings.',
            Icons.people,
            Colors.green,
          ),
          _buildTipCard(
            'Gentle Exercise',
            'Prenatal yoga or walking can reduce stress and improve mood. Always consult your doctor first.',
            Icons.fitness_center,
            Colors.teal,
          ),
          _buildTipCard(
            'Mindful Pregnancy',
            'Take time each day to connect with your baby. Talk, sing, or gently touch your belly.',
            Icons.psychology,
            Colors.purple,
          ),

          const SizedBox(height: 24),

          // Daily Wellness Tips
          Text(
            'Daily Wellness Tips',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),

          _buildTipCard(
            'Take Screen Breaks',
            'Every 20 minutes, look at something 20 feet away for 20 seconds to reduce eye strain.',
            Icons.visibility,
            Colors.orange,
          ),
          _buildTipCard(
            'Stay Hydrated',
            'Drink water throughout the day. Dehydration can affect mood and energy levels.',
            Icons.water_drop,
            Colors.cyan,
          ),
          _buildTipCard(
            'Practice Gratitude',
            'Write down 3 things you\'re grateful for each day to improve positive thinking.',
            Icons.favorite,
            Colors.pink,
          ),

          const SizedBox(height: 24),

          // Pregnancy Stress Management
          Text(
            'Pregnancy Stress Management',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),

          _buildTipCard(
            'Pregnancy-Safe Relaxation',
            'Practice gentle stretching and meditation techniques that are safe for pregnancy.',
            Icons.accessibility_new,
            Colors.purple,
          ),
          _buildTipCard(
            'Mindful Pregnancy Moments',
            'Take 2 minutes to focus on your baby\'s movements and connect with your pregnancy journey.',
            Icons.psychology,
            Colors.indigo,
          ),
          _buildTipCard(
            'Nature Walks',
            'Gentle outdoor walks can reduce pregnancy stress and improve mood.',
            Icons.nature,
            Colors.teal,
          ),
          _buildTipCard(
            'Pregnancy Journaling',
            'Write about your pregnancy experience, fears, and joys to process emotions.',
            Icons.edit,
            Colors.orange,
          ),

          const SizedBox(height: 24),

          // Pregnancy Sleep & Recovery
          Text(
            'Pregnancy Sleep & Recovery',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),

          _buildTipCard(
            'Pregnancy Sleep Positions',
            'Sleep on your left side with pillows for support. This improves blood flow to your baby.',
            Icons.bedtime,
            Colors.deepPurple,
          ),
          _buildTipCard(
            'Pregnancy Bedtime Routine',
            'Create a relaxing routine: warm bath, gentle stretching, or reading pregnancy books.',
            Icons.nightlight,
            Colors.indigo,
          ),
          _buildTipCard(
            'Comfortable Sleep Environment',
            'Use pregnancy pillows and keep your bedroom cool and dark for better sleep.',
            Icons.hotel,
            Colors.blue,
          ),
          _buildTipCard(
            'Rest When Needed',
            'Listen to your body and take naps when you feel tired. Your body is working hard!',
            Icons.bed,
            Colors.grey,
          ),

          const SizedBox(height: 24),

          // Pregnancy Social Support
          Text(
            'Pregnancy Social Support',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),

          _buildTipCard(
            'Join Pregnancy Groups',
            'Connect with other expecting mothers for support and shared experiences.',
            Icons.people,
            Colors.blue,
          ),
          _buildTipCard(
            'Share with Partner',
            'Keep your partner involved in your pregnancy journey and share your feelings openly.',
            Icons.favorite,
            Colors.pink,
          ),
          _buildTipCard(
            'Family Support',
            'Let family members help with daily tasks and emotional support during pregnancy.',
            Icons.family_restroom,
            Colors.orange,
          ),
          _buildTipCard(
            'Professional Support',
            'Consider talking to a pregnancy counselor or therapist if you need extra support.',
            Icons.psychology,
            Colors.green,
          ),

          const SizedBox(height: 24),

          // Emergency Resources (Simplified)
          Card(
            color: Colors.red.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.emergency, color: Colors.red.shade600, size: 24),
                      const SizedBox(width: 12),
                      Text(
                        'Need Immediate Help?',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: Colors.red.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'If you\'re experiencing a mental health crisis, call:',
                    style: TextStyle(color: Colors.red.shade700),
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.phone, color: Colors.red.shade600),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '988',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.red.shade700,
                              ),
                            ),
                            Text(
                              'Suicide Prevention Lifeline',
                              style: TextStyle(
                                color: Colors.red.shade600,
                                fontSize: 12,
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
      ),
    );
  }



  Widget _buildTipCard(String title, String description, IconData icon, Color color) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                icon,
                color: color,
                size: 24,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTipItem(String tip) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.check_circle,
            color: Colors.green.shade600,
            size: 20,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              tip,
              style: TextStyle(
                color: Colors.green.shade700,
                fontSize: 14,
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
        title: const Text('Mental Health'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(
              icon: Icon(Icons.mood),
              text: 'Mood Check-in',
            ),
            Tab(
              icon: Icon(Icons.assessment),
              text: 'Assessment',
            ),
            Tab(
              icon: Icon(Icons.lightbulb),
              text: 'Tips',
            ),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildMoodCheckInTab(),
          _buildAssessmentTab(),
          _buildTipsTab(),
        ],
      ),
    );
  }
}
