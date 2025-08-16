import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../utils/constants.dart';
import '../widgets/custom_text_field.dart';
import '../widgets/loading_button.dart';

class DoctorProfileCompletionScreen extends StatefulWidget {
  const DoctorProfileCompletionScreen({super.key});

  @override
  State<DoctorProfileCompletionScreen> createState() => _DoctorProfileCompletionScreenState();
}

class _DoctorProfileCompletionScreenState extends State<DoctorProfileCompletionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _qualificationController = TextEditingController();
  final _specializationController = TextEditingController();
  final _workingHospitalController = TextEditingController();
  final _doctorIdController = TextEditingController();
  final _licenseNumberController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();
  final _cityController = TextEditingController();
  final _stateController = TextEditingController();
  final _zipCodeController = TextEditingController();
  final _experienceYearsController = TextEditingController();

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _qualificationController.dispose();
    _specializationController.dispose();
    _workingHospitalController.dispose();
    _doctorIdController.dispose();
    _licenseNumberController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    _cityController.dispose();
    _stateController.dispose();
    _zipCodeController.dispose();
    _experienceYearsController.dispose();
    super.dispose();
  }

  Future<void> _completeProfile() async {
    if (!_formKey.currentState!.validate()) return;

    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final success = await authProvider.completeDoctorProfile(
      firstName: _firstNameController.text.trim(),
      lastName: _lastNameController.text.trim(),
      qualification: _qualificationController.text.trim(),
      specialization: _specializationController.text.trim(),
      workingHospital: _workingHospitalController.text.trim(),
      doctorId: _doctorIdController.text.trim(),
      licenseNumber: _licenseNumberController.text.trim(),
      phone: _phoneController.text.trim(),
      address: _addressController.text.trim(),
      city: _cityController.text.trim(),
      state: _stateController.text.trim(),
      zipCode: _zipCodeController.text.trim(),
      experienceYears: _experienceYearsController.text.trim(),
    );

    if (success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Profile completed successfully!'),
          backgroundColor: AppColors.success,
        ),
      );
      Navigator.pushReplacementNamed(context, '/doctor-dashboard');
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(authProvider.error ?? 'Profile completion failed'),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Complete Doctor Profile'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        automaticallyImplyLeading: false, // Disable back button
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
                
                // Title
                Text(
                  'Complete Your Doctor Profile',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  'Please provide your professional information to complete your profile',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: AppColors.textSecondary,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),

                // Personal Information
                _buildSectionTitle('Personal Information'),
                const SizedBox(height: 16),
                
                Row(
                  children: [
                    Expanded(
                      child: CustomTextField(
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
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: CustomTextField(
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
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                CustomTextField(
                  controller: _phoneController,
                  labelText: 'Phone Number',
                  hintText: 'Enter your phone number',
                  prefixIcon: Icons.phone,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your phone number';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // Professional Information
                _buildSectionTitle('Professional Information'),
                const SizedBox(height: 16),

                CustomTextField(
                  controller: _qualificationController,
                  labelText: 'Qualification',
                  hintText: 'e.g., MBBS, MD, MS, etc.',
                  prefixIcon: Icons.school,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your qualification';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                CustomTextField(
                  controller: _specializationController,
                  labelText: 'Specialization',
                  hintText: 'e.g., Cardiology, Neurology, etc.',
                  prefixIcon: Icons.medical_services,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your specialization';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                CustomTextField(
                  controller: _workingHospitalController,
                  labelText: 'Working Hospital',
                  hintText: 'Enter your hospital name',
                  prefixIcon: Icons.local_hospital,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your working hospital';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                Row(
                  children: [
                    Expanded(
                      child: CustomTextField(
                        controller: _doctorIdController,
                        labelText: 'Doctor ID',
                        hintText: 'Enter your doctor ID',
                        prefixIcon: Icons.badge,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Please enter your doctor ID';
                          }
                          return null;
                        },
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: CustomTextField(
                        controller: _licenseNumberController,
                        labelText: 'License Number',
                        hintText: 'Enter your license number',
                        prefixIcon: Icons.verified_user,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Please enter your license number';
                          }
                          return null;
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                CustomTextField(
                  controller: _experienceYearsController,
                  labelText: 'Years of Experience',
                  hintText: 'Enter years of experience',
                  prefixIcon: Icons.work,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your years of experience';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // Address Information
                _buildSectionTitle('Address Information'),
                const SizedBox(height: 16),

                CustomTextField(
                  controller: _addressController,
                  labelText: 'Street Address',
                  hintText: 'Enter your street address',
                  prefixIcon: Icons.home,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your address';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                Row(
                  children: [
                    Expanded(
                      child: CustomTextField(
                        controller: _cityController,
                        labelText: 'City',
                        hintText: 'Enter your city',
                        prefixIcon: Icons.location_city,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Please enter your city';
                          }
                          return null;
                        },
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: CustomTextField(
                        controller: _stateController,
                        labelText: 'State',
                        hintText: 'Enter your state',
                        prefixIcon: Icons.location_on,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Please enter your state';
                          }
                          return null;
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                CustomTextField(
                  controller: _zipCodeController,
                  labelText: 'ZIP Code',
                  hintText: 'Enter your ZIP code',
                  prefixIcon: Icons.pin_drop,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your ZIP code';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 32),

                // Complete Profile Button
                Consumer<AuthProvider>(
                  builder: (context, authProvider, child) {
                    return LoadingButton(
                      onPressed: authProvider.isLoading ? null : _completeProfile,
                      isLoading: authProvider.isLoading,
                      text: 'Complete Profile',
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.titleLarge?.copyWith(
        fontWeight: FontWeight.bold,
        color: AppColors.textPrimary,
      ),
    );
  }
} 