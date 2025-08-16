import 'package:flutter/material.dart';
import '../utils/constants.dart';

class DoctorFoodTrackingScreen extends StatefulWidget {
  final String patientId;
  final DateTime date;
  
  const DoctorFoodTrackingScreen({
    super.key,
    required this.patientId,
    required this.date,
  });

  @override
  State<DoctorFoodTrackingScreen> createState() => _DoctorFoodTrackingScreenState();
}

class _DoctorFoodTrackingScreenState extends State<DoctorFoodTrackingScreen> {
  final List<Map<String, dynamic>> _foodEntries = [];
  final TextEditingController _foodNameController = TextEditingController();
  final TextEditingController _caloriesController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  String _selectedMealType = 'Breakfast';
  final List<String> _mealTypes = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];

  @override
  void initState() {
    super.initState();
    _loadSampleData(); // Load sample data for demonstration
  }

  @override
  void dispose() {
    _foodNameController.dispose();
    _caloriesController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  void _loadSampleData() {
    // Sample food entries for demonstration
    _foodEntries.addAll([
      {
        'mealType': 'Breakfast',
        'foodName': 'Oatmeal with berries',
        'calories': 250,
        'notes': 'Good fiber content',
        'time': '08:00 AM',
      },
      {
        'mealType': 'Lunch',
        'foodName': 'Grilled chicken salad',
        'calories': 350,
        'notes': 'High protein, low carb',
        'time': '12:30 PM',
      },
      {
        'mealType': 'Snack',
        'foodName': 'Apple with peanut butter',
        'calories': 180,
        'notes': 'Healthy snack option',
        'time': '03:00 PM',
      },
    ]);
  }

  void _addFoodEntry() {
    if (_foodNameController.text.isEmpty || _caloriesController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please fill in all required fields'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    setState(() {
      _foodEntries.add({
        'mealType': _selectedMealType,
        'foodName': _foodNameController.text,
        'calories': int.tryParse(_caloriesController.text) ?? 0,
        'notes': _notesController.text,
        'time': '${DateTime.now().hour.toString().padLeft(2, '0')}:${DateTime.now().minute.toString().padLeft(2, '0')}',
      });
    });

    // Clear form
    _foodNameController.clear();
    _caloriesController.clear();
    _notesController.clear();
    _selectedMealType = 'Breakfast';

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Food entry added successfully'),
        backgroundColor: AppColors.success,
      ),
    );
  }

  void _removeFoodEntry(int index) {
    setState(() {
      _foodEntries.removeAt(index);
    });
  }

  int get _totalCalories {
    return _foodEntries.fold(0, (sum, entry) => sum + (entry['calories'] as int));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Food Tracking - ${widget.patientId}'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.arrow_back),
            tooltip: 'Back to Daily Log',
            onPressed: () => Navigator.pop(context),
          ),
          IconButton(
            icon: const Icon(Icons.person),
            tooltip: 'Profile',
            onPressed: () => Navigator.pushNamed(context, '/doctor-profile'),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () => Navigator.pushReplacementNamed(context, '/role-selection'),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSizes.paddingLarge),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header with Patient Info and Date
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSizes.paddingLarge),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 25,
                        backgroundColor: Colors.orange,
                        child: Icon(
                          Icons.restaurant,
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
                              'Food & Nutrition Tracking',
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Patient: ${widget.patientId} | Date: ${widget.date.day}/${widget.date.month}/${widget.date.year}',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Add Food Entry Form
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSizes.paddingLarge),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Add Food Entry',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              value: _selectedMealType,
                              decoration: const InputDecoration(
                                labelText: 'Meal Type',
                                border: OutlineInputBorder(),
                              ),
                              items: _mealTypes.map((String type) {
                                return DropdownMenuItem<String>(
                                  value: type,
                                  child: Text(type),
                                );
                              }).toList(),
                              onChanged: (String? newValue) {
                                setState(() {
                                  _selectedMealType = newValue!;
                                });
                              },
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: TextFormField(
                              controller: _caloriesController,
                              decoration: const InputDecoration(
                                labelText: 'Calories',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.local_fire_department),
                              ),
                              keyboardType: TextInputType.number,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      
                      TextFormField(
                        controller: _foodNameController,
                        decoration: const InputDecoration(
                          labelText: 'Food Name',
                          hintText: 'e.g., Grilled chicken salad',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.fastfood),
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      TextFormField(
                        controller: _notesController,
                        decoration: const InputDecoration(
                          labelText: 'Notes (Optional)',
                          hintText: 'e.g., High protein, low carb',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.note),
                        ),
                        maxLines: 2,
                      ),
                      const SizedBox(height: 16),
                      
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _addFoodEntry,
                          icon: const Icon(Icons.add),
                          label: const Text('Add Food Entry'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.orange,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Summary Card
              Card(
                color: Colors.orange.withOpacity(0.1),
                child: Padding(
                  padding: const EdgeInsets.all(AppSizes.paddingLarge),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Total Calories Today',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: Colors.orange.shade800,
                            ),
                          ),
                          Text(
                            '$_totalCalories kcal',
                            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: Colors.orange.shade800,
                            ),
                          ),
                        ],
                      ),
                      Icon(
                        Icons.local_fire_department,
                        size: 50,
                        color: Colors.orange.shade800,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Food Entries List
              Text(
                'Food Entries (${_foodEntries.length})',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 16),

              Expanded(
                child: _foodEntries.isEmpty
                    ? const Center(
                        child: Text(
                          'No food entries yet. Add some food items above.',
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.grey,
                          ),
                        ),
                      )
                    : ListView.builder(
                        itemCount: _foodEntries.length,
                        itemBuilder: (context, index) {
                          final entry = _foodEntries[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: Colors.orange.withOpacity(0.2),
                                child: Icon(
                                  Icons.restaurant,
                                  color: Colors.orange.shade800,
                                ),
                              ),
                              title: Text(
                                entry['foodName'],
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${entry['mealType']} • ${entry['time']}'),
                                  if (entry['notes'].isNotEmpty)
                                    Text(
                                      entry['notes'],
                                      style: TextStyle(
                                        color: Colors.grey.shade600,
                                        fontStyle: FontStyle.italic,
                                      ),
                                    ),
                                ],
                              ),
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color: Colors.orange.withOpacity(0.2),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Text(
                                      '${entry['calories']} kcal',
                                      style: TextStyle(
                                        color: Colors.orange.shade800,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  IconButton(
                                    icon: const Icon(Icons.delete, color: Colors.red),
                                    onPressed: () => _removeFoodEntry(index),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
} 