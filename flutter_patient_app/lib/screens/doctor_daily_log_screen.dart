import 'package:flutter/material.dart';
import '../utils/constants.dart';

class DoctorDailyLogScreen extends StatefulWidget {
  const DoctorDailyLogScreen({super.key});

  @override
  State<DoctorDailyLogScreen> createState() => _DoctorDailyLogScreenState();
}

class _DoctorDailyLogScreenState extends State<DoctorDailyLogScreen> {
  final TextEditingController _patientIdController = TextEditingController();
  final TextEditingController _dateController = TextEditingController();
  DateTime _selectedDate = DateTime.now();

  @override
  void initState() {
    super.initState();
    _dateController.text = "${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}";
  }

  @override
  void dispose() {
    _patientIdController.dispose();
    _dateController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now(),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
        _dateController.text = "${picked.day}/${picked.month}/${picked.year}";
      });
    }
  }

  void _navigateToCategory(String category, String patientId) {
    if (patientId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter a Patient ID first'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    // Navigate to specific category tracking screen
    switch (category) {
      case 'food':
        Navigator.pushNamed(context, '/doctor-food-tracking', arguments: {
          'patientId': patientId,
          'date': _selectedDate,
        });
        break;
      case 'medication':
        Navigator.pushNamed(context, '/doctor-medication-tracking', arguments: {
          'patientId': patientId,
          'date': _selectedDate,
        });
        break;
      case 'symptoms':
        Navigator.pushNamed(context, '/doctor-symptoms-tracking', arguments: {
          'patientId': patientId,
          'date': _selectedDate,
        });
        break;
      case 'sleep':
        Navigator.pushNamed(context, '/doctor-sleep-tracking', arguments: {
          'patientId': patientId,
          'date': _selectedDate,
        });
        break;
      case 'mental_health':
        Navigator.pushNamed(context, '/doctor-mental-health-tracking', arguments: {
          'patientId': patientId,
          'date': _selectedDate,
        });
        break;
      case 'kick_count':
        Navigator.pushNamed(context, '/doctor-kick-count-tracking', arguments: {
          'patientId': patientId,
          'date': _selectedDate,
        });
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Daily Patient Log'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.arrow_back),
            tooltip: 'Back to Dashboard',
            onPressed: () => Navigator.pushReplacementNamed(context, '/doctor-dashboard'),
          ),
          IconButton(
            icon: const Icon(Icons.person),
            tooltip: 'Profile',
            onPressed: () => Navigator.pushNamed(context, '/doctor-profile'),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () async {
              // Handle logout
              Navigator.pushReplacementNamed(context, '/role-selection');
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSizes.paddingLarge),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Section
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
                              Icons.medical_services,
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
                                  'Patient Daily Log',
                                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Track patient health metrics and daily activities',
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: AppColors.textSecondary,
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

              // Patient ID and Date Selection
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSizes.paddingLarge),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Patient Information',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      // Patient ID Input
                      TextFormField(
                        controller: _patientIdController,
                        decoration: const InputDecoration(
                          labelText: 'Patient ID',
                          hintText: 'Enter Patient ID',
                          prefixIcon: Icon(Icons.person),
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter Patient ID';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      
                      // Date Selection
                      TextFormField(
                        controller: _dateController,
                        readOnly: true,
                        decoration: InputDecoration(
                          labelText: 'Date',
                          hintText: 'Select Date',
                          prefixIcon: const Icon(Icons.calendar_today),
                          border: const OutlineInputBorder(),
                          suffixIcon: IconButton(
                            icon: const Icon(Icons.date_range),
                            onPressed: () => _selectDate(context),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Health Tracking Categories
              Text(
                'Health Tracking Categories',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 16),

              Expanded(
                child: GridView.count(
                  crossAxisCount: 2,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  children: [
                    _buildCategoryCard(
                      context,
                      title: 'Food & Nutrition',
                      subtitle: 'Track meals, calories, and dietary intake',
                      icon: Icons.restaurant,
                      color: Colors.orange,
                      onTap: () => _navigateToCategory('food', _patientIdController.text),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Medication',
                      subtitle: 'Monitor medication adherence and dosage',
                      icon: Icons.medication,
                      color: Colors.red,
                      onTap: () => _navigateToCategory('medication', _patientIdController.text),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Symptoms',
                      subtitle: 'Record symptoms and health concerns',
                      icon: Icons.sick,
                      color: Colors.purple,
                      onTap: () => _navigateToCategory('symptoms', _patientIdController.text),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Sleep',
                      subtitle: 'Monitor sleep patterns and quality',
                      icon: Icons.bedtime,
                      color: Colors.indigo,
                      onTap: () => _navigateToCategory('sleep', _patientIdController.text),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Mental Health',
                      subtitle: 'Track mood, stress, and mental well-being',
                      icon: Icons.psychology,
                      color: Colors.teal,
                      onTap: () => _navigateToCategory('mental_health', _patientIdController.text),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Kick Count',
                      subtitle: 'Monitor fetal movement (pregnancy)',
                      icon: Icons.favorite,
                      color: Colors.pink,
                      onTap: () => _navigateToCategory('kick_count', _patientIdController.text),
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

  Widget _buildCategoryCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 3,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppSizes.radiusMedium),
        child: Padding(
          padding: const EdgeInsets.all(AppSizes.paddingMedium),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  size: 40,
                  color: color,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
} 