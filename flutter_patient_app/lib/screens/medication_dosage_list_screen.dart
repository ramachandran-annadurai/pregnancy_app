import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';

class MedicationDosageListScreen extends StatefulWidget {
  const MedicationDosageListScreen({super.key});

  @override
  State<MedicationDosageListScreen> createState() => _MedicationDosageListScreenState();
}

class _MedicationDosageListScreenState extends State<MedicationDosageListScreen> {
  bool _isLoading = true;
  String _errorMessage = '';
  List<dynamic> _upcomingDosages = [];
  List<dynamic> _prescriptionMedications = [];
  int _totalUpcoming = 0;
  int _totalPrescriptions = 0;
  String _currentTime = '';

  @override
  void initState() {
    super.initState();
    _loadUpcomingDosages();
  }

  Future<void> _loadUpcomingDosages() async {
    try {
      setState(() {
        _isLoading = true;
        _errorMessage = '';
      });

      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] == null) {
        setState(() {
          _errorMessage = 'User not authenticated';
          _isLoading = false;
        });
        return;
      }

      final apiService = ApiService();
      final result = await apiService.getUpcomingDosages(userInfo['userId']!);

      if (result.containsKey('success') && result['success'] == true) {
        setState(() {
          _upcomingDosages = result['upcoming_dosages'] ?? [];
          _prescriptionMedications = result['prescription_medications'] ?? [];
          _totalUpcoming = result['total_upcoming'] ?? 0;
          _totalPrescriptions = result['total_prescriptions'] ?? 0;
          _currentTime = result['current_time'] ?? '';
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = result['message'] ?? 'Failed to load upcoming dosages';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Error loading upcoming dosages: $e';
        _isLoading = false;
      });
    }
  }

  String _formatTime(String isoTime) {
    try {
      final dateTime = DateTime.parse(isoTime);
      return '${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return isoTime;
    }
  }

  String _getTimeUntil(String isoTime) {
    try {
      final dateTime = DateTime.parse(isoTime);
      final now = DateTime.now();
      final difference = dateTime.difference(now);
      
      if (difference.isNegative) {
        return 'Overdue';
      }
      
      final hours = difference.inHours;
      final minutes = difference.inMinutes % 60;
      
      if (hours > 0) {
        return '${hours}h ${minutes}m';
      } else {
        return '${minutes}m';
      }
    } catch (e) {
      return 'Unknown';
    }
  }

  Color _getUrgencyColor(String urgencyLevel) {
    switch (urgencyLevel.toLowerCase()) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.yellow;
      default:
        return Colors.green;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Medication Schedule'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadUpcomingDosages,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage.isNotEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error, color: Colors.red, size: 64),
                      const SizedBox(height: 16),
                      Text(
                        _errorMessage,
                        style: const TextStyle(fontSize: 16, color: Colors.red),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadUpcomingDosages,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadUpcomingDosages,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Current Time Display
                        if (_currentTime.isNotEmpty)
                          Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Row(
                                children: [
                                  Icon(Icons.access_time, color: AppColors.primary),
                                  const SizedBox(width: 12),
                                  Text(
                                    'Current Time: ${_formatTime(_currentTime)}',
                                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        
                        const SizedBox(height: 16),
                        
                        // Upcoming Dosages Section
                        if (_upcomingDosages.isNotEmpty) ...[
                          _buildSectionHeader(
                            'Upcoming Dosages',
                            _totalUpcoming,
                            Icons.schedule,
                            Colors.blue,
                          ),
                          const SizedBox(height: 8),
                          ..._upcomingDosages.map((dosage) => _buildDosageCard(dosage)),
                          const SizedBox(height: 24),
                        ],
                        
                        // Prescription Medications Section
                        if (_prescriptionMedications.isNotEmpty) ...[
                          _buildSectionHeader(
                            'Prescription Medications',
                            _totalPrescriptions,
                            Icons.medication,
                            Colors.green,
                          ),
                          const SizedBox(height: 8),
                          ..._prescriptionMedications.map((med) => _buildPrescriptionCard(med)),
                          const SizedBox(height: 24),
                        ],
                        
                        // Empty State
                        if (_upcomingDosages.isEmpty && _prescriptionMedications.isEmpty)
                          Center(
                            child: Column(
                              children: [
                                Icon(
                                  Icons.medication_outlined,
                                  size: 64,
                                  color: Colors.grey.shade400,
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  'No upcoming dosages or medications',
                                  style: TextStyle(
                                    fontSize: 18,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  'Add medications with reminders to see them here',
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: Colors.grey.shade500,
                                  ),
                                  textAlign: TextAlign.center,
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

  Widget _buildSectionHeader(String title, int count, IconData icon, Color color) {
    return Row(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(width: 12),
        Text(
          title,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        const Spacer(),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: color),
          ),
          child: Text(
            '$count',
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDosageCard(Map<String, dynamic> dosage) {
    final nextDoseTime = dosage['next_dose_time'] ?? '';
    final timeUntil = _getTimeUntil(nextDoseTime);
    final isOverdue = timeUntil == 'Overdue';
    
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    dosage['medication_name'] ?? 'Unknown Medication',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isOverdue ? Colors.red : Colors.green,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    timeUntil,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            
            Row(
              children: [
                Icon(Icons.schedule, size: 16, color: Colors.grey.shade600),
                const SizedBox(width: 8),
                Text(
                  'Time: ${dosage['time'] ?? 'Unknown'}',
                  style: TextStyle(color: Colors.grey.shade600),
                ),
                const SizedBox(width: 16),
                Icon(Icons.medication, size: 16, color: Colors.grey.shade600),
                const SizedBox(width: 8),
                Text(
                  'Dose: ${dosage['dosage'] ?? 'Unknown'}',
                  style: TextStyle(color: Colors.grey.shade600),
                ),
              ],
            ),
            
            if (dosage['frequency']?.isNotEmpty == true) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(Icons.repeat, size: 16, color: Colors.grey.shade600),
                  const SizedBox(width: 8),
                  Text(
                    'Frequency: ${dosage['frequency']}',
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                ],
              ),
            ],
            
            if (dosage['special_instructions']?.isNotEmpty == true) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info, size: 16, color: Colors.blue.shade700),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        dosage['special_instructions'],
                        style: TextStyle(
                          color: Colors.blue.shade700,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            
            if (dosage['notes']?.isNotEmpty == true) ...[
              const SizedBox(height: 8),
              Text(
                'Notes: ${dosage['notes']}',
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
            
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.person, size: 16, color: Colors.grey.shade600),
                const SizedBox(width: 8),
                Text(
                  'Prescribed by: ${dosage['prescribed_by'] ?? 'Unknown'}',
                  style: TextStyle(
                    color: Colors.grey.shade600,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPrescriptionCard(Map<String, dynamic> medication) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.medication, color: Colors.green, size: 20),
                const SizedBox(width: 8),
                Text(
                  medication['medication_name'] ?? 'Unknown Medication',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'Prescription',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.green.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.description, size: 16, color: Colors.green.shade700),
                      const SizedBox(width: 8),
                      Text(
                        'Prescription Details:',
                        style: TextStyle(
                          color: Colors.green.shade700,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    medication['details'] ?? 'No details provided',
                    style: TextStyle(
                      color: Colors.green.shade700,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            
            if (medication['notes']?.isNotEmpty == true) ...[
              const SizedBox(height: 8),
              Text(
                'Notes: ${medication['notes']}',
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
            
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.person, size: 16, color: Colors.grey.shade600),
                const SizedBox(width: 8),
                Text(
                  'Prescribed by: ${medication['prescribed_by'] ?? 'Unknown'}',
                  style: TextStyle(
                    color: Colors.grey.shade600,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
