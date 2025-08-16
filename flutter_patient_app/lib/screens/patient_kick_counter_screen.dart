import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import 'dart:convert';

class PatientKickCounterScreen extends StatefulWidget {
  final String userId;
  final String userRole;
  final String username;
  final String email;

  const PatientKickCounterScreen({
    Key? key,
    required this.userId,
    required this.userRole,
    required this.username,
    required this.email,
  }) : super(key: key);

  @override
  State<PatientKickCounterScreen> createState() => _PatientKickCounterScreenState();
}

class _PatientKickCounterScreenState extends State<PatientKickCounterScreen> {
  int _kickCount = 0;
  DateTime? _sessionStartTime;
  bool _isSessionActive = false;
  bool _isLoading = false;
  List<Map<String, dynamic>> _kickLogs = [];

  @override
  void initState() {
    super.initState();
    _loadKickHistory();
  }

  void _startSession() {
    setState(() {
      _isSessionActive = true;
      _sessionStartTime = DateTime.now();
      _kickCount = 0;
    });
  }

  void _stopSession() {
    if (_isSessionActive && _kickCount > 0) {
      _saveKickSession();
    }
    setState(() {
      _isSessionActive = false;
      _sessionStartTime = null;
    });
  }

  void _logKick() {
    if (_isSessionActive) {
      setState(() {
        _kickCount++;
      });
    }
  }

  void _resetSession() {
    setState(() {
      _kickCount = 0;
      _sessionStartTime = null;
      _isSessionActive = false;
    });
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    String hours = twoDigits(duration.inHours);
    String minutes = twoDigits(duration.inMinutes.remainder(60));
    String seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$hours:$minutes:$seconds';
  }

  Duration _getSessionDuration() {
    if (_sessionStartTime == null) return Duration.zero;
    return DateTime.now().difference(_sessionStartTime!);
  }

  Future<void> _saveKickSession() async {
    if (_kickCount == 0) return;

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

      final kickData = {
        'userId': patientId,
        'userRole': widget.userRole,
        'username': widget.username,
        'kickCount': _kickCount,
        'sessionDuration': _getSessionDuration().inSeconds,
        'sessionStartTime': _sessionStartTime?.toIso8601String(),
        'sessionEndTime': DateTime.now().toIso8601String(),
        'averageKicksPerMinute': _kickCount / (_getSessionDuration().inMinutes > 0 ? _getSessionDuration().inMinutes : 1),
        'notes': 'Kick counting session',
        'timestamp': DateTime.now().toIso8601String(),
      };

      // Debug logging
      print('🔍 ===== KICK COUNTER DEBUG START =====');
      print('🔍 Patient ID: $patientId');
      print('🔍 Kick Data Map:');
      print('  - userId: ${kickData['userId']}');
      print('  - userRole: ${kickData['userRole']}');
      print('  - username: ${kickData['username']}');
      print('  - kickCount: ${kickData['kickCount']}');
      print('  - sessionDuration: ${kickData['sessionDuration']} seconds');
      print('🔍 Full JSON Data: ${json.encode(kickData)}');
      print('🔍 ===== KICK COUNTER DEBUG END =====');

      // Save kick session data
      final response = await ApiService().saveKickSession(kickData);
      
      if (response['success'] == true) {
        // Add to local kick logs
        setState(() {
          _kickLogs.add({
            'kickCount': _kickCount,
            'sessionDuration': _getSessionDuration().inSeconds,
            'timestamp': DateTime.now().toIso8601String(),
          });
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Kick session saved successfully!'),
            backgroundColor: Colors.green,
          ),
        );

        // Reset for next session
        _resetSession();
      } else {
        throw Exception('Failed to save kick session');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error saving kick session: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadKickHistory() async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      final String? patientId = userInfo['userId'];
      if (patientId != null) {
        // Load kick history from API
        final response = await ApiService().getKickHistory(patientId);
        if (response['success'] == true) {
          setState(() {
            _kickLogs = List<Map<String, dynamic>>.from(response['kick_logs'] ?? []);
          });
        }
      }
    } catch (e) {
      print('Error loading kick history: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final sessionDuration = _getSessionDuration();
    
    return Scaffold(
      appBar: AppBar(
        title: Text('Kick Counter'),
        backgroundColor: Colors.purple,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            // Instructions
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.purple.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                'Tap the button each time you feel your baby move.',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.purple[800],
                  fontWeight: FontWeight.w500,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            
            SizedBox(height: 30),
            
            // Timer Display
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildTimeBox(
                  'Hours',
                  sessionDuration.inHours.toString().padLeft(2, '0'),
                ),
                _buildTimeBox(
                  'Minutes',
                  sessionDuration.inMinutes.remainder(60).toString().padLeft(2, '0'),
                ),
                _buildTimeBox(
                  'Seconds',
                  sessionDuration.inSeconds.remainder(60).toString().padLeft(2, '0'),
                ),
              ],
            ),
            
            SizedBox(height: 30),
            
            // Log Kick Button
            Container(
              width: double.infinity,
              height: 60,
              child: ElevatedButton(
                onPressed: _isSessionActive ? _logKick : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  elevation: 0,
                ),
                child: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Colors.pink, Colors.purple],
                      begin: Alignment.centerLeft,
                      end: Alignment.centerRight,
                    ),
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: Center(
                    child: Text(
                      'Log Kick',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ),
            
            SizedBox(height: 20),
            
            // Kick Count Display
            Text(
              'Kick Count: $_kickCount',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.purple[800],
              ),
            ),
            
            SizedBox(height: 30),
            
            // Session Control Buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton(
                  onPressed: !_isSessionActive ? _startSession : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                  child: Text('Start Session'),
                ),
                ElevatedButton(
                  onPressed: _isSessionActive ? _stopSession : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                  child: Text('Stop Session'),
                ),
                ElevatedButton(
                  onPressed: _resetSession,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.orange,
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                  child: Text('Reset'),
                ),
              ],
            ),
            
            SizedBox(height: 30),
            
            // Loading indicator
            if (_isLoading)
              CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(Colors.purple),
              ),
            
            SizedBox(height: 20),
            
            // Kick History
            if (_kickLogs.isNotEmpty) ...[
              Text(
                'Recent Sessions',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.purple[800],
                ),
              ),
              SizedBox(height: 10),
              Expanded(
                child: ListView.builder(
                  itemCount: _kickLogs.length,
                  itemBuilder: (context, index) {
                    final log = _kickLogs[index];
                    final timestamp = DateTime.tryParse(log['timestamp'] ?? '');
                    return Card(
                      margin: EdgeInsets.symmetric(vertical: 4),
                      child: ListTile(
                        leading: Icon(Icons.child_care, color: Colors.purple),
                        title: Text('${log['kickCount']} kicks'),
                        subtitle: Text(
                          timestamp != null 
                            ? '${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')} - ${log['sessionDuration']} seconds'
                            : 'Session completed',
                        ),
                        trailing: Icon(Icons.check_circle, color: Colors.green),
                      ),
                    );
                  },
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildTimeBox(String label, String value) {
    return Column(
      children: [
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(
            color: Colors.purple.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.purple.withOpacity(0.3)),
          ),
          child: Center(
            child: Text(
              value,
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.purple[800],
              ),
            ),
          ),
        ),
        SizedBox(height: 8),
        Text(
          label,
          style: TextStyle(
            fontSize: 14,
            color: Colors.grey[600],
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
} 