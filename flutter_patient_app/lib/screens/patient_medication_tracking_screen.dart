import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../utils/date_utils.dart';

// Medication dosage model
class MedicationDosage {
  final String dosage;
  final String time;
  final String frequency;
  final bool reminderEnabled;
  final String? nextDoseTime;
  final String? specialInstructions;

  MedicationDosage({
    required this.dosage,
    required this.time,
    required this.frequency,
    this.reminderEnabled = false,
    this.nextDoseTime,
    this.specialInstructions,
  });

  Map<String, dynamic> toJson() {
    return {
      'dosage': dosage,
      'time': time,
      'frequency': frequency,
      'reminder_enabled': reminderEnabled,
      'next_dose_time': nextDoseTime,
      'special_instructions': specialInstructions,
    };
  }
}

class PatientMedicationTrackingScreen extends StatefulWidget {
  final String date;

  const PatientMedicationTrackingScreen({
    super.key,
    required this.date,
  });

  @override
  State<PatientMedicationTrackingScreen> createState() => _PatientMedicationTrackingScreenState();
}

class _PatientMedicationTrackingScreenState extends State<PatientMedicationTrackingScreen> {
  final TextEditingController _medicationNameController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  final TextEditingController _prescribedByController = TextEditingController();
  
  bool _isSaving = false;
  String _successMessage = '';
  String _errorMessage = '';
  int? _currentPregnancyWeek;
  bool _isLoadingPregnancyWeek = true;
  
  String _selectedMedicationType = 'prescription';
  List<String> _sideEffects = [];
  final TextEditingController _sideEffectController = TextEditingController();
  
  // Multiple dosages support
  List<MedicationDosage> _dosages = [];

  @override
  void initState() {
    super.initState();
    _loadPatientPregnancyWeek();
  }

  @override
  void dispose() {
    _medicationNameController.dispose();
    _notesController.dispose();
    _prescribedByController.dispose();
    _sideEffectController.dispose();
    super.dispose();
  }

  // Load patient's pregnancy week when screen initializes
  Future<void> _loadPatientPregnancyWeek() async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] != null) {
        final apiService = ApiService();
        final profileResponse = await apiService.getProfile(patientId: userInfo['userId']!);
        
        if (profileResponse.containsKey('pregnancy_week') && profileResponse['pregnancy_week'] != null) {
          setState(() {
            _currentPregnancyWeek = int.tryParse(profileResponse['pregnancy_week'].toString());
          });
          print('🔍 Loaded pregnancy week: $_currentPregnancyWeek');
        }
        
      }
    } catch (e) {
      print('⚠️ Could not load pregnancy week: $e');
    } finally {
      setState(() {
        _isLoadingPregnancyWeek = false;
      });
    }
  }

  Future<void> _saveMedicationLog() async {
    if (_medicationNameController.text.trim().isEmpty) {
      setState(() {
        _errorMessage = 'Please enter medication name';
      });
      return;
    }

    // Validate based on mode
    if (_dosages.isEmpty) {
      setState(() {
        _errorMessage = 'Please add at least one dosage';
      });
      return;
    }

    setState(() {
      _isSaving = true;
      _errorMessage = '';
      _successMessage = '';
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      final pregnancyWeek = _currentPregnancyWeek ?? 20;
      
      // Save medication log with dosages using existing API
      final medicationData = {
        'patient_id': userInfo['userId'] ?? 'unknown',
        'medication_name': _medicationNameController.text.trim(),
        'dosages': _dosages.map((d) => d.toJson()).toList(),
        'date_taken': widget.date,
        'notes': _notesController.text.trim(),
        'prescribed_by': _prescribedByController.text.trim(),
        'medication_type': _selectedMedicationType,
        'side_effects': _sideEffects,
        'pregnancy_week': pregnancyWeek,
      };
      
      // Debug logging
      print('🔍 ===== MEDICATION DATA DEBUG =====');
      print('🔍 Medication Name: ${medicationData['medication_name']}');
      print('🔍 Dosages Count: ${(medicationData['dosages'] as List).length}');
      print('🔍 Dosages: ${medicationData['dosages']}');
      print('🔍 ===== END DEBUG =====');

      final apiService = ApiService();
      final saveResult = await apiService.saveMedicationLog(medicationData);
      
      setState(() {
        _isSaving = false;
        if (saveResult.containsKey('success') && saveResult['success'] == true) {
          _successMessage = 'Medication log saved successfully!';
          _clearForm();
        } else {
          _errorMessage = saveResult['message'] ?? 'Failed to save medication log';
        }
      });

      // Show success message
      if (_successMessage.isNotEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_successMessage),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      setState(() {
        _isSaving = false;
        _errorMessage = 'Error saving medication log: $e';
      });
    }
  }

  void _clearForm() {
    _medicationNameController.clear();
    _notesController.clear();
    _prescribedByController.clear();
    _sideEffectController.clear();
    setState(() {
      _selectedMedicationType = 'prescription';
      _dosages.clear();
      _sideEffects.clear();
      _successMessage = '';
      _errorMessage = '';
    });
  }

  void _addSideEffect() {
    if (_sideEffectController.text.trim().isNotEmpty) {
      setState(() {
        _sideEffects.add(_sideEffectController.text.trim());
        _sideEffectController.clear();
      });
    }
  }

  void _removeSideEffect(int index) {
    setState(() {
      _sideEffects.removeAt(index);
    });
  }

  // Add new dosage
  void _addDosage() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        final dosageController = TextEditingController();
        final timeController = TextEditingController();
        final frequencyController = TextEditingController();
        final instructionsController = TextEditingController();
        bool reminderEnabled = false;
        String? nextDoseTime;
        
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: const Text('Add Dosage'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextFormField(
                      controller: dosageController,
                      decoration: const InputDecoration(
                        labelText: 'Dosage *',
                        hintText: 'e.g., 500mg, 1 tablet',
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: timeController,
                            readOnly: true,
                            decoration: const InputDecoration(
                              labelText: 'Time *',
                              hintText: 'Select time',
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: () async {
                            final TimeOfDay? picked = await showTimePicker(
                              context: context,
                              initialTime: TimeOfDay.now(),
                            );
                            if (picked != null) {
                              setState(() {
                                timeController.text = '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
                              });
                            }
                          },
                          child: const Text('Pick Time'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: frequencyController,
                      decoration: const InputDecoration(
                        labelText: 'Frequency *',
                        hintText: 'e.g., Once daily, Twice daily, Every 8 hours',
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: instructionsController,
                      decoration: const InputDecoration(
                        labelText: 'Special Instructions',
                        hintText: 'Take with food, etc.',
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Checkbox(
                          value: reminderEnabled,
                          onChanged: (value) {
                            setState(() {
                              reminderEnabled = value!;
                            });
                          },
                        ),
                        const Text('Enable Reminder'),
                      ],
                    ),
                    if (reminderEnabled) ...[
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              readOnly: true,
                              decoration: const InputDecoration(
                                labelText: 'Next Dose Time',
                                hintText: 'Select reminder time',
                              ),
                              onTap: () async {
                                final TimeOfDay? picked = await showTimePicker(
                                  context: context,
                                  initialTime: TimeOfDay.now(),
                                );
                                if (picked != null) {
                                  setState(() {
                                    nextDoseTime = '${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}';
                                  });
                                }
                              },
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () {
                    if (dosageController.text.trim().isNotEmpty &&
                        timeController.text.trim().isNotEmpty &&
                        frequencyController.text.trim().isNotEmpty) {
                      final dosage = MedicationDosage(
                        dosage: dosageController.text.trim(),
                        time: timeController.text.trim(),
                        frequency: frequencyController.text.trim(),
                        reminderEnabled: reminderEnabled,
                        nextDoseTime: nextDoseTime,
                        specialInstructions: instructionsController.text.trim(),
                      );
                      this.setState(() {
                        _dosages.add(dosage);
                      });
                      Navigator.of(context).pop();
                    }
                  },
                  child: const Text('Add'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  // Remove dosage
  void _removeDosage(int index) {
    setState(() {
      _dosages.removeAt(index);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Medication Tracking'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.schedule),
            tooltip: 'View Dosage Schedule',
            onPressed: () {
              Navigator.pushNamed(context, '/medication-dosage-list');
            },
          ),
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'View Medication History',
            onPressed: () {
              // TODO: Navigate to medication history
            },
          ),
          IconButton(
            icon: const Icon(Icons.clear),
            tooltip: 'Clear Form',
            onPressed: _clearForm,
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSizes.paddingLarge),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSizes.paddingLarge),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 25,
                            backgroundColor: AppColors.primary,
                            child: Icon(
                              Icons.medication,
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
                                  'Daily Medication Log',
                                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Track your medications and dosages',
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              'Date: ${AppDateUtils.formatDate(widget.date)}',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                color: AppColors.primary,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          if (_isLoadingPregnancyWeek)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              child: const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              ),
                            )
                          else if (_currentPregnancyWeek != null)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: AppColors.primary.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: AppColors.primary),
                              ),
                              child: Text(
                                'Week $_currentPregnancyWeek',
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Medication Form
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    children: [
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(AppSizes.paddingLarge),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Medication Details',
                                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 16),
                              
                              // Medication Name
                              TextFormField(
                                controller: _medicationNameController,
                                decoration: const InputDecoration(
                                  labelText: 'Medication Name *',
                                  hintText: 'Enter medication name...',
                                  border: OutlineInputBorder(),
                                  prefixIcon: Icon(Icons.medication),
                                ),
                              ),
                              const SizedBox(height: 16),
                              
                              // Multiple Dosages Section
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      'Dosages',
                                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ),
                                  ElevatedButton.icon(
                                    onPressed: _addDosage,
                                    icon: const Icon(Icons.add),
                                    label: const Text('Add Dosage'),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: AppColors.primary,
                                      foregroundColor: Colors.white,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              
                              if (_dosages.isEmpty)
                                Container(
                                  padding: const EdgeInsets.all(16),
                                  decoration: BoxDecoration(
                                    border: Border.all(color: Colors.grey.shade300),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Center(
                                    child: Text(
                                      'No dosages added yet. Click "Add Dosage" to get started.',
                                      style: TextStyle(color: Colors.grey),
                                    ),
                                  ),
                                )
                              else
                                ListView.builder(
                                  shrinkWrap: true,
                                  physics: const NeverScrollableScrollPhysics(),
                                  itemCount: _dosages.length,
                                  itemBuilder: (context, index) {
                                    final dosage = _dosages[index];
                                    return Card(
                                      margin: const EdgeInsets.only(bottom: 8),
                                      child: ListTile(
                                        title: Text(
                                          '${dosage.dosage} at ${dosage.time}',
                                          style: const TextStyle(fontWeight: FontWeight.bold),
                                        ),
                                        subtitle: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text('Frequency: ${dosage.frequency}'),
                                            if (dosage.specialInstructions?.isNotEmpty == true)
                                              Text('Instructions: ${dosage.specialInstructions}'),
                                            if (dosage.reminderEnabled)
                                              Text('🔔 Reminder enabled for next dose'),
                                          ],
                                        ),
                                        trailing: IconButton(
                                          icon: const Icon(Icons.delete, color: Colors.red),
                                          onPressed: () => _removeDosage(index),
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              const SizedBox(height: 16),
                              
                              // Medication Type
                              DropdownButtonFormField<String>(
                                value: _selectedMedicationType,
                                decoration: const InputDecoration(
                                  labelText: 'Medication Type',
                                  border: OutlineInputBorder(),
                                  prefixIcon: Icon(Icons.category),
                                ),
                                items: const [
                                  DropdownMenuItem(value: 'prescription', child: Text('Prescription')),
                                  DropdownMenuItem(value: 'over_the_counter', child: Text('Over the Counter')),
                                  DropdownMenuItem(value: 'supplement', child: Text('Supplement')),
                                  DropdownMenuItem(value: 'vitamin', child: Text('Vitamin')),
                                ],
                                onChanged: (value) {
                                  setState(() {
                                    _selectedMedicationType = value!;
                                  });
                                },
                              ),
                              const SizedBox(height: 16),
                              
                              // Prescribed By
                              TextFormField(
                                controller: _prescribedByController,
                                decoration: const InputDecoration(
                                  labelText: 'Prescribed By',
                                  hintText: 'Doctor name or clinic',
                                  border: OutlineInputBorder(),
                                  prefixIcon: Icon(Icons.person),
                                ),
                              ),
                              const SizedBox(height: 16),
                              
                              // Notes
                              TextFormField(
                                controller: _notesController,
                                maxLines: 3,
                                decoration: const InputDecoration(
                                  labelText: 'Additional Notes',
                                  hintText: 'Any special instructions or notes...',
                                  border: OutlineInputBorder(),
                                  prefixIcon: Icon(Icons.note),
                                ),
                              ),
                              const SizedBox(height: 16),
                              
                              // Side Effects
                              Text(
                                'Side Effects (if any)',
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Expanded(
                                    child: TextFormField(
                                      controller: _sideEffectController,
                                      decoration: const InputDecoration(
                                        labelText: 'Add Side Effect',
                                        hintText: 'Enter side effect...',
                                        border: OutlineInputBorder(),
                                        prefixIcon: Icon(Icons.warning),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  ElevatedButton(
                                    onPressed: _addSideEffect,
                                    child: const Text('Add'),
                                  ),
                                ],
                              ),
                              if (_sideEffects.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Wrap(
                                  spacing: 8,
                                  children: _sideEffects.asMap().entries.map((entry) {
                                    return Chip(
                                      label: Text(entry.value),
                                      onDeleted: () => _removeSideEffect(entry.key),
                                      deleteIcon: const Icon(Icons.close),
                                    );
                                  }).toList(),
                                ),
                              ],
                              const SizedBox(height: 16),
                              
                              // Reminder Note
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.blue.shade50,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: Colors.blue.shade200),
                                ),
                                child: Row(
                                  children: [
                                    Icon(Icons.info, color: Colors.blue.shade700, size: 20),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        'Reminders are automatically set for each dosage when enabled. Check your dosage list above for reminder status.',
                                        style: TextStyle(
                                          color: Colors.blue.shade700,
                                          fontSize: 12,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 24),
                              
                              // Button Row for Daily Tracking and Medication Dosage Details
                              Row(
                                children: [
                                  // Daily Tracking Button
                                  Expanded(
                                    child: SizedBox(
                                      height: 50,
                                      child: ElevatedButton.icon(
                                        onPressed: () {
                                          // Navigate to daily tracking details screen
                                          Navigator.pushNamed(context, '/patient-daily-tracking-details');
                                        },
                                        icon: const Icon(Icons.track_changes),
                                        label: const Text('Daily Tracking'),
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: Colors.green,
                                          foregroundColor: Colors.white,
                                        ),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 16),
                                  // Medication Dosage Details Button
                                  Expanded(
                                    child: SizedBox(
                                       height: 50,
                                       child: ElevatedButton.icon(
                                         onPressed: () {
                                           // Navigate to medication dosage list screen
                                           Navigator.pushNamed(context, '/medication-dosage-list');
                                         },
                                         icon: const Icon(Icons.medication),
                                         label: const Text('Dosage Details'),
                                         style: ElevatedButton.styleFrom(
                                           backgroundColor: AppColors.primary,
                                           foregroundColor: Colors.white,
                                         ),
                                       ),
                                     ),
                                   ),
                                 ],
                               ),
                              
                              const SizedBox(height: 24),
                                 
                              // Save Button
                              SizedBox(
                                width: double.infinity,
                                height: 50,
                                child: ElevatedButton.icon(
                                  onPressed: _isSaving ? null : _saveMedicationLog,
                                  icon: _isSaving 
                                    ? const SizedBox(
                                        width: 20,
                                        height: 20,
                                        child: CircularProgressIndicator(strokeWidth: 2),
                                      )
                                    : const Icon(Icons.save),
                                  label: Text(_isSaving ? 'Saving...' : 'Save Medication Log'),
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
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
