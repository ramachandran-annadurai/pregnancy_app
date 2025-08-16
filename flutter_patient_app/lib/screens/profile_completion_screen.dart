import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/user_provider.dart';
import '../providers/auth_provider.dart';
import '../utils/constants.dart';
import '../widgets/custom_text_field.dart';
import '../widgets/loading_button.dart';

class ProfileCompletionScreen extends StatefulWidget {
  const ProfileCompletionScreen({super.key});

  @override
  State<ProfileCompletionScreen> createState() => _ProfileCompletionScreenState();
}

class _ProfileCompletionScreenState extends State<ProfileCompletionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _dateOfBirthController = TextEditingController();
  final _emergencyNameController = TextEditingController();
  final _emergencyRelationshipController = TextEditingController();
  final _emergencyPhoneController = TextEditingController();
  final _lastPeriodDateController = TextEditingController();
  final _weightController = TextEditingController();
  final _heightController = TextEditingController();
  
  String _selectedBloodType = 'A+';
  bool _isPregnant = false;
  DateTime? _lastPeriodDate;
  bool _isLoading = false;

  final List<String> _bloodTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _dateOfBirthController.dispose();
    _emergencyNameController.dispose();
    _emergencyRelationshipController.dispose();
    _emergencyPhoneController.dispose();
    _lastPeriodDateController.dispose();
    _weightController.dispose();
    _heightController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(BuildContext context, bool isLastPeriod) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: isLastPeriod ? DateTime.now().subtract(const Duration(days: 90)) : DateTime.now().subtract(const Duration(days: 6570)), // 18 years ago
      firstDate: isLastPeriod ? DateTime.now().subtract(const Duration(days: 365)) : DateTime(1900),
      lastDate: DateTime.now(),
    );
    if (picked != null) {
      setState(() {
        if (isLastPeriod) {
          _lastPeriodDate = picked;
          _lastPeriodDateController.text = "${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}";
        } else {
          _dateOfBirthController.text = "${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}";
        }
      });
    }
  }

  Future<void> _completeProfile() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    final userProvider = Provider.of<UserProvider>(context, listen: false);
    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    final profileData = {
      'patient_id': authProvider.patientId,
      'first_name': _firstNameController.text.trim(),
      'last_name': _lastNameController.text.trim(),
      'date_of_birth': _dateOfBirthController.text.trim(),
      'blood_type': _selectedBloodType,
      'is_pregnant': _isPregnant,
      'last_period_date': _lastPeriodDate != null 
          ? "${_lastPeriodDate!.year}-${_lastPeriodDate!.month.toString().padLeft(2, '0')}-${_lastPeriodDate!.day.toString().padLeft(2, '0')}"
          : '',
      'emergency_name': _emergencyNameController.text.trim(),
      'emergency_relationship': _emergencyRelationshipController.text.trim(),
      'emergency_phone': _emergencyPhoneController.text.trim(),
    };

    final success = await userProvider.completeProfile(
      patientId: authProvider.patientId!,
      firstName: _firstNameController.text.trim(),
      lastName: _lastNameController.text.trim(),
      dateOfBirth: _dateOfBirthController.text.trim(),
      bloodType: _selectedBloodType,
      weight: _weightController.text.trim(),
      height: _heightController.text.trim(),
      isPregnant: _isPregnant,
      lastPeriodDate: _lastPeriodDate != null 
          ? "${_lastPeriodDate!.year}-${_lastPeriodDate!.month.toString().padLeft(2, '0')}-${_lastPeriodDate!.day.toString().padLeft(2, '0')}"
          : null,
      emergencyName: _emergencyNameController.text.trim(),
      emergencyRelationship: _emergencyRelationshipController.text.trim(),
      emergencyPhone: _emergencyPhoneController.text.trim(),
    );

    setState(() {
      _isLoading = false;
    });

    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Profile completed successfully!'),
          backgroundColor: AppColors.success,
        ),
      );
      Navigator.pushReplacementNamed(context, '/home');
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(userProvider.error ?? 'Failed to complete profile'),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Complete Profile'),
        automaticallyImplyLeading: false, // Prevent back navigation
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              // Show logout confirmation dialog
              showDialog(
                context: context,
                builder: (BuildContext context) {
                  return AlertDialog(
                    title: const Text('Logout'),
                    content: const Text('Are you sure you want to logout?'),
                    actions: [
                      TextButton(
                        onPressed: () {
                          Navigator.of(context).pop(); // Close dialog
                        },
                        child: const Text('Cancel'),
                      ),
                      TextButton(
                        onPressed: () {
                          Navigator.of(context).pop(); // Close dialog
                          // Perform logout
                          Provider.of<AuthProvider>(context, listen: false).logout();
                          Navigator.pushReplacementNamed(context, '/login');
                        },
                        child: const Text('Logout'),
                      ),
                    ],
                  );
                },
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSizes.paddingLarge),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 20),
                
                // Icon and Title
                Icon(
                  Icons.person_add,
                  size: 70,
                  color: AppColors.primary,
                ),
                const SizedBox(height: 20),
                Text(
                  'Complete Your Profile',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  'Please provide your basic information to complete your profile',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: AppColors.textSecondary,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),

                // Personal Information Section
                Text(
                  'Personal Information',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),

                // First Name
                CustomTextField(
                  controller: _firstNameController,
                  labelText: 'First Name',
                  hintText: 'Enter your first name',
                  prefixIcon: Icons.person,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your first name';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Last Name
                CustomTextField(
                  controller: _lastNameController,
                  labelText: 'Last Name',
                  hintText: 'Enter your last name',
                  prefixIcon: Icons.person,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your last name';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Date of Birth
                GestureDetector(
                  onTap: () => _selectDate(context, false),
                  child: CustomTextField(
                    controller: _dateOfBirthController,
                    labelText: 'Date of Birth',
                    hintText: 'Select your date of birth',
                    prefixIcon: Icons.calendar_today,
                    enabled: false,
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'Please select your date of birth';
                      }
                      return null;
                    },
                  ),
                ),
                const SizedBox(height: 16),

                // Blood Type
                DropdownButtonFormField<String>(
                  value: _selectedBloodType,
                  decoration: const InputDecoration(
                    labelText: 'Blood Type',
                    prefixIcon: Icon(Icons.bloodtype),
                    border: OutlineInputBorder(),
                  ),
                  items: _bloodTypes.map((String type) {
                    return DropdownMenuItem<String>(
                      value: type,
                      child: Text(type),
                    );
                  }).toList(),
                  onChanged: (String? newValue) {
                    setState(() {
                      _selectedBloodType = newValue!;
                    });
                  },
                ),
                const SizedBox(height: 16),

                // Weight
                CustomTextField(
                  controller: _weightController,
                  labelText: 'Weight (kg)',
                  hintText: 'Enter your weight in kg',
                  prefixIcon: Icons.monitor_weight,
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your weight';
                    }
                    final weight = double.tryParse(value);
                    if (weight == null || weight <= 0 || weight > 500) {
                      return 'Please enter a valid weight (1-500 kg)';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Height
                CustomTextField(
                  controller: _heightController,
                  labelText: 'Height (cm)',
                  hintText: 'Enter your height in cm',
                  prefixIcon: Icons.height,
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your height';
                    }
                    final height = double.tryParse(value);
                    if (height == null || height <= 0 || height > 300) {
                      return 'Please enter a valid height (1-300 cm)';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // Pregnancy Information Section
                Text(
                  'Pregnancy Information',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),

                // Are you pregnant checkbox
                CheckboxListTile(
                  title: const Text('Are you pregnant?'),
                  value: _isPregnant,
                  onChanged: (bool? value) {
                    setState(() {
                      _isPregnant = value ?? false;
                    });
                  },
                  controlAffinity: ListTileControlAffinity.leading,
                ),
                const SizedBox(height: 16),

                // Last Period Date (only if pregnant)
                if (_isPregnant) ...[
                  GestureDetector(
                    onTap: () => _selectDate(context, true),
                    child: CustomTextField(
                      controller: _lastPeriodDateController,
                      labelText: 'Last Period Date',
                      hintText: 'Select your last period date',
                      prefixIcon: Icons.calendar_today,
                      enabled: false,
                      validator: (value) {
                        if (_isPregnant && (value == null || value.trim().isEmpty)) {
                          return 'Please select your last period date';
                        }
                        return null;
                      },
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                // Emergency Contact Section
                Text(
                  'Emergency Contact',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),

                // Emergency Contact Name
                CustomTextField(
                  controller: _emergencyNameController,
                  labelText: 'Emergency Contact Name',
                  hintText: 'Enter emergency contact name',
                  prefixIcon: Icons.emergency,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter emergency contact name';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Emergency Contact Relationship
                CustomTextField(
                  controller: _emergencyRelationshipController,
                  labelText: 'Relationship',
                  hintText: 'e.g., Spouse, Parent, Friend',
                  prefixIcon: Icons.people,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter relationship';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Emergency Contact Phone
                CustomTextField(
                  controller: _emergencyPhoneController,
                  labelText: 'Emergency Contact Phone',
                  hintText: 'Enter emergency contact phone',
                  prefixIcon: Icons.phone,
                  keyboardType: TextInputType.phone,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter emergency contact phone';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 32),

                // Complete Profile Button
                LoadingButton(
                  onPressed: _isLoading ? null : _completeProfile,
                  isLoading: _isLoading,
                  text: 'Complete Profile',
                ),
                
                // Extra space at bottom to prevent overflow
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
} 