import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../screens/patient_kick_counter_screen.dart';
import '../screens/patient_sleep_log_screen.dart';
import '../utils/constants.dart';

class PatientDailyLogScreen extends StatefulWidget {
  const PatientDailyLogScreen({super.key});

  @override
  State<PatientDailyLogScreen> createState() => _PatientDailyLogScreenState();
}

class _PatientDailyLogScreenState extends State<PatientDailyLogScreen> {
  final TextEditingController _dateController = TextEditingController();
  DateTime _selectedDate = DateTime.now();

  @override
  void initState() {
    super.initState();
    _dateController.text = "${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}";
    
    // Ensure user data is loaded when the screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      authProvider.checkLoginStatus();
    });
  }

  @override
  void dispose() {
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

  void _navigateToCategory(String category) {
    // Navigate to specific category tracking screen
    switch (category) {
      case 'food':
        Navigator.pushNamed(context, '/patient-food-tracking', arguments: {
          'date': "${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}",
        });
        break;
      case 'medication':
        Navigator.pushNamed(context, '/patient-medication-tracking', arguments: {
          'date': "${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}",
        });
        break;
      case 'symptoms':
        Navigator.pushNamed(context, '/patient-symptoms-tracking', arguments: {
          'date': "${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}",
        });
        break;
      case 'sleep':
        final authProvider = Provider.of<AuthProvider>(context, listen: false);
        // Use the async method to get user info
        authProvider.getCurrentUserInfo().then((userInfo) {
          print('🔍 Daily Log Debug - User Info:');
          print('  Email: ${userInfo['email']}');
          print('  Username: ${userInfo['username']}');
          print('  UserId: ${userInfo['userId']}');
          print('  UserRole: ${userInfo['userRole']}');
          
          Navigator.pushNamed(context, '/patient-sleep-log', arguments: {
            'userId': userInfo['userId'] ?? 'unknown',
            'userRole': userInfo['userRole'] ?? 'patient',
            'username': userInfo['username'] ?? 'unknown',
            'email': userInfo['email'] ?? 'unknown',
          });
        });
        break;
      case 'mental_health':
        Navigator.pushNamed(context, '/mental-health', arguments: {
          'selectedDate': "${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}",
        });
        break;
      case 'kick_count':
        print('🔍 Kick Count button clicked!');
        final authProvider = Provider.of<AuthProvider>(context, listen: false);
        // Use the async method to get user info
        authProvider.getCurrentUserInfo().then((userInfo) {
          print('🔍 Daily Log Debug - User Info:');
          print('  Email: ${userInfo['email']}');
          print('  Username: ${userInfo['username']}');
          print('  UserId: ${userInfo['userId']}');
          print('  UserRole: ${userInfo['userRole']}');

          print('🔍 Navigating to Kick Counter...');
          Navigator.pushNamed(context, '/patient-kick-counter', arguments: {
            'userId': userInfo['userId'] ?? 'unknown',
            'userRole': userInfo['userRole'] ?? 'patient',
            'username': userInfo['username'] ?? 'unknown',
            'email': userInfo['email'] ?? 'unknown',
          }).then((result) {
            print('🔍 Navigation result: $result');
          }).catchError((error) {
            print('❌ Navigation error: $error');
          });
        }).catchError((error) {
          print('❌ Error getting user info: $error');
        });
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Daily Health Log'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.arrow_back),
            tooltip: 'Back to Home',
            onPressed: () => Navigator.pushReplacementNamed(context, '/home'),
          ),
          IconButton(
            icon: const Icon(Icons.person),
            tooltip: 'Profile',
            onPressed: () => Navigator.pushNamed(context, '/profile'),
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
                              Icons.health_and_safety,
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
                                  'Daily Health Log',
                                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Track your daily health metrics and activities',
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

              // Date Selection
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSizes.paddingLarge),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Select Date',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 16),
                      
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
                'Track Your Health Today',
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
                      subtitle: 'Log your meals, calories, and dietary intake',
                      icon: Icons.restaurant,
                      color: Colors.orange,
                      onTap: () => _navigateToCategory('food'),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Medication',
                      subtitle: 'Record medication taken and dosages',
                      icon: Icons.medication,
                      color: Colors.red,
                      onTap: () => _navigateToCategory('medication'),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Symptoms',
                      subtitle: 'Track any symptoms or health concerns',
                      icon: Icons.sick,
                      color: Colors.purple,
                      onTap: () => _navigateToCategory('symptoms'),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Sleep',
                      subtitle: 'Monitor your sleep patterns and quality',
                      icon: Icons.bedtime,
                      color: Colors.indigo,
                      onTap: () => _navigateToCategory('sleep'),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Mental Health',
                      subtitle: 'Track your mood, stress and mental wellbeing',
                      icon: Icons.psychology,
                      color: Colors.teal,
                      onTap: () => _navigateToCategory('mental_health'),
                    ),
                    _buildCategoryCard(
                      context,
                      title: 'Kick Count',
                      subtitle: 'Monitor fetal movement and count kicks',
                      icon: Icons.favorite,
                      color: Colors.pink,
                      onTap: () => _navigateToCategory('kick_count'),
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
        child: Container(
          height: 160, // Fixed height to prevent overflow
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
                  size: 32, // Slightly smaller icon
                  color: color,
                ),
              ),
              const SizedBox(height: 12), // Reduced spacing
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
                maxLines: 1, // Single line for title
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 6), // Reduced spacing
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                  fontSize: 11, // Smaller font size
                ),
                textAlign: TextAlign.center,
                maxLines: 2, // Reduced to 2 lines
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
} 