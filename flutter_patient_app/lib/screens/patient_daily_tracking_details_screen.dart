import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../utils/date_utils.dart';

class PatientDailyTrackingDetailsScreen extends StatefulWidget {
  const PatientDailyTrackingDetailsScreen({super.key});

  @override
  State<PatientDailyTrackingDetailsScreen> createState() => _PatientDailyTrackingDetailsScreenState();
}

class _PatientDailyTrackingDetailsScreenState extends State<PatientDailyTrackingDetailsScreen> {
  final TextEditingController _tabletNameController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  
  bool _isLoading = true;
  bool _isSaving = false;
  bool _tabletTaken = false; // New field for tablet taken status
  bool _isPrescribed = false; // New field for prescription status
  List<Map<String, dynamic>> _tabletHistory = [];
  String _errorMessage = '';
  String _successMessage = '';

  @override
  void initState() {
    super.initState();
    _loadTabletHistory();
  }

  @override
  void dispose() {
    _tabletNameController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  // Check if tablet is prescribed
  Future<void> _checkPrescriptionStatus(String tabletName) async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] != null) {
        final apiService = ApiService();
        final response = await apiService.getPrescriptionDetails(userInfo['userId']!);
        
        if (response['success'] == true) {
          final prescriptions = response['prescriptions'] ?? [];
          
          // Check if tablet name matches any prescribed medication
          bool isPrescribed = prescriptions.any((prescription) {
            final medName = prescription['medication_name']?.toString().toLowerCase() ?? '';
            final tabletNameLower = tabletName.toLowerCase();
            return medName.contains(tabletNameLower) || tabletNameLower.contains(medName);
          });
          
          setState(() {
            _isPrescribed = isPrescribed;
          });
          
          if (isPrescribed) {
            setState(() {
              _successMessage = '✅ This tablet is prescribed for you';
            });
          } else {
            setState(() {
              _errorMessage = '⚠️ This tablet is not in your prescription list';
            });
          }
          
          // Clear messages after 3 seconds
          Future.delayed(const Duration(seconds: 3), () {
            if (mounted) {
              setState(() {
                _successMessage = '';
                _errorMessage = '';
              });
            }
          });
        }
      }
    } catch (e) {
      print('⚠️ Error checking prescription status: $e');
    }
  }

  Future<void> _loadTabletHistory() async {
    try {
      setState(() {
        _isLoading = true;
        _errorMessage = '';
      });

      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] != null) {
        final apiService = ApiService();
        final response = await apiService.getTabletTrackingHistory(userInfo['userId']!);
        
        if (response['success'] == true) {
          setState(() {
            _tabletHistory = List<Map<String, dynamic>>.from(response['tablet_tracking_history'] ?? []);
            _isLoading = false;
          });
        } else {
          setState(() {
            _errorMessage = response['message'] ?? 'Failed to load tablet tracking history';
            _isLoading = false;
          });
        }
      } else {
        setState(() {
          _errorMessage = 'User not authenticated';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Error loading medication history: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _saveTabletTaken() async {
    if (_tabletNameController.text.trim().isEmpty) {
      setState(() {
        _errorMessage = 'Please enter tablet name';
      });
      return;
    }

    try {
      setState(() {
        _isSaving = true;
        _errorMessage = '';
        _successMessage = '';
      });

      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] != null) {
        final apiService = ApiService();
        
        // Format data for tablet tracking (stored in medication_daily_tracking array)
        final tabletTrackingData = {
          'patient_id': userInfo['userId']!,
          'tablet_name': _tabletNameController.text.trim(),
          'tablet_taken_today': _tabletTaken, // New field for tablet taken today status
          'is_prescribed': _isPrescribed, // Prescription status
          'notes': _notesController.text.trim(),
          'date_taken': '${DateTime.now().day}/${DateTime.now().month}/${DateTime.now().year}', // Format: "19/8/2025"
          'time_taken': DateTime.now().toString().substring(0, 19), // Format: "2025-08-19 07:56:17.744"
          'type': 'daily_tracking', // Fixed type field
          'timestamp': DateTime.now().toIso8601String(), // Format: "2025-08-19T07:56:17.806125"
        };

        final response = await apiService.saveTabletTracking(tabletTrackingData);
        
        if (response['success'] == true) {
          setState(() {
            _successMessage = 'Tablet tracking saved successfully!';
            _tabletNameController.clear();
            _notesController.clear();
            _tabletTaken = false; // Reset tablet taken status
            _isPrescribed = false; // Reset prescription status
          });
          
          // Reload the history
          await _loadTabletHistory();
          
          // Clear success message after 3 seconds
          Future.delayed(const Duration(seconds: 3), () {
            if (mounted) {
              setState(() {
                _successMessage = '';
              });
            }
          });
        } else {
          setState(() {
            _errorMessage = response['message'] ?? 'Failed to save tablet tracking';
          });
        }
      } else {
        setState(() {
          _errorMessage = 'User not authenticated';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Error saving tablet tracking: $e';
      });
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  String _formatDateTime(String dateTimeString) {
    return AppDateUtils.formatDateTime(dateTimeString);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Daily Tracking Details'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Success/Error Messages
                  if (_successMessage.isNotEmpty)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        color: Colors.green.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.green.shade200),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.check_circle, color: Colors.green.shade700, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _successMessage,
                              style: TextStyle(color: Colors.green.shade700),
                            ),
                          ),
                        ],
                      ),
                    ),
                  
                  if (_errorMessage.isNotEmpty)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.red.shade200),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.error, color: Colors.red.shade700, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _errorMessage,
                              style: TextStyle(color: Colors.red.shade700),
                            ),
                          ),
                        ],
                      ),
                    ),

                  // Add New Tablet Entry Section
                  Card(
                    elevation: 2,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Add New Tablet Entry',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 16),
                          
                          // Tablet Taken Toggle
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Tablet Taken Today?',
                                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                  fontWeight: FontWeight.w600,
                                  color: Colors.grey.shade700,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: ElevatedButton(
                                      onPressed: () => setState(() => _tabletTaken = true),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: _tabletTaken ? AppColors.primary : Colors.grey.shade300,
                                        foregroundColor: _tabletTaken ? Colors.white : Colors.grey.shade600,
                                        elevation: _tabletTaken ? 2 : 0,
                                      ),
                                      child: const Text('Yes'),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: ElevatedButton(
                                      onPressed: () => setState(() => _tabletTaken = false),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: !_tabletTaken ? AppColors.primary : Colors.grey.shade300,
                                        foregroundColor: !_tabletTaken ? Colors.white : Colors.grey.shade600,
                                        elevation: !_tabletTaken ? 2 : 0,
                                      ),
                                      child: const Text('No'),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          
                          TextFormField(
                            controller: _tabletNameController,
                            decoration: const InputDecoration(
                              labelText: 'Tablet Name *',
                              hintText: 'Enter tablet name...',
                              border: OutlineInputBorder(),
                              prefixIcon: Icon(Icons.medication),
                            ),
                            onChanged: (value) {
                              _checkPrescriptionStatus(value);
                            },
                          ),
                          const SizedBox(height: 16),
                          
                          // Prescription Status Indicator
                          if (_tabletNameController.text.trim().isNotEmpty)
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: _isPrescribed ? Colors.green.shade50 : Colors.orange.shade50,
                                borderRadius: BorderRadius.circular(4),
                                border: Border.all(
                                  color: _isPrescribed ? Colors.green.shade200 : Colors.orange.shade200,
                                ),
                              ),
                              child: Row(
                                children: [
                                  Icon(
                                    _isPrescribed ? Icons.check_circle : Icons.info,
                                    color: _isPrescribed ? Colors.green.shade700 : Colors.orange.shade700,
                                    size: 16,
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      _isPrescribed 
                                        ? '✅ This tablet is prescribed for you'
                                        : '⚠️ This tablet is not in your prescription list',
                                      style: TextStyle(
                                        color: _isPrescribed ? Colors.green.shade700 : Colors.orange.shade700,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          
                          const SizedBox(height: 16),
                          
                          TextFormField(
                            controller: _notesController,
                            decoration: const InputDecoration(
                              labelText: 'Notes (Optional)',
                              hintText: 'Any additional notes...',
                              border: OutlineInputBorder(),
                              prefixIcon: Icon(Icons.note),
                            ),
                            maxLines: 2,
                          ),
                          const SizedBox(height: 16),
                          
                          SizedBox(
                            width: double.infinity,
                            height: 50,
                            child: ElevatedButton.icon(
                              onPressed: _isSaving ? null : _saveTabletTaken,
                              icon: _isSaving 
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : const Icon(Icons.save),
                              label: Text(_isSaving ? 'Saving...' : 'Save Tablet Entry'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.primary,
                                foregroundColor: Colors.white,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Medication History Section
                  Row(
                    children: [
                      Icon(Icons.history, color: AppColors.primary, size: 24),
                      const SizedBox(width: 8),
                      Text(
                        'Tablet History',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        'Total: ${_tabletHistory.length}',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  if (_tabletHistory.isEmpty)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(32),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        children: [
                          Icon(
                            Icons.medication_outlined,
                            size: 64,
                            color: Colors.grey.shade400,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No tablet entries yet',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: Colors.grey.shade600,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Start tracking your daily tablet intake above',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.grey.shade500,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    )
                  else
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: _tabletHistory.length,
                      itemBuilder: (context, index) {
                        final entry = _tabletHistory[index];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 8),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: AppColors.primary,
                              child: Icon(
                                Icons.medication,
                                color: Colors.white,
                                size: 20,
                              ),
                            ),
                            title: Text(
                              entry['tablet_name'] ?? 'Unknown Tablet',
                              style: const TextStyle(fontWeight: FontWeight.w600),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // Tablet Taken Status
                                Row(
                                  children: [
                                    Icon(
                                      entry['tablet_taken_today'] == true 
                                        ? Icons.check_circle 
                                        : Icons.cancel,
                                      color: entry['tablet_taken_today'] == true 
                                        ? Colors.green 
                                        : Colors.red,
                                      size: 16,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      entry['tablet_taken_today'] == true 
                                        ? 'Tablet Taken' 
                                        : 'Tablet Not Taken',
                                      style: TextStyle(
                                        color: entry['tablet_taken_today'] == true 
                                          ? Colors.green.shade700 
                                          : Colors.red.shade700,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                // Prescription Status
                                Row(
                                  children: [
                                    Icon(
                                      entry['is_prescribed'] == true 
                                        ? Icons.verified 
                                        : Icons.info_outline,
                                      color: entry['is_prescribed'] == true 
                                        ? Colors.blue 
                                        : Colors.orange,
                                      size: 16,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      entry['is_prescribed'] == true 
                                        ? 'Prescribed Medication' 
                                        : 'Over-the-Counter',
                                      style: TextStyle(
                                        color: entry['is_prescribed'] == true 
                                          ? Colors.blue.shade700 
                                          : Colors.orange.shade700,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                // Date and Time
                                Text(
                                  'Date: ${entry['date_taken'] ?? 'N/A'}',
                                  style: TextStyle(
                                    color: Colors.grey.shade600,
                                    fontSize: 12,
                                  ),
                                ),
                                Text(
                                  'Time: ${entry['time_taken'] ?? 'N/A'}',
                                  style: TextStyle(
                                    color: Colors.grey.shade600,
                                    fontSize: 12,
                                  ),
                                ),
                                if (entry['notes']?.isNotEmpty == true) ...[
                                  const SizedBox(height: 4),
                                  Text(
                                    'Notes: ${entry['notes']}',
                                    style: TextStyle(
                                      color: Colors.grey.shade700,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                            trailing: Icon(
                              Icons.check_circle,
                              color: Colors.green.shade600,
                              size: 20,
                            ),
                          ),
                        );
                      },
                    ),
                  
                  const SizedBox(height: 24),
                  
                  // Refresh Button
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: OutlinedButton.icon(
                      onPressed: _loadTabletHistory,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Refresh History'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.primary,
                        side: BorderSide(color: AppColors.primary),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
