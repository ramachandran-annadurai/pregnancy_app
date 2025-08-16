import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../utils/constants.dart';

class DetailedFoodEntryScreen extends StatefulWidget {
  final String userId;
  final String username;
  final String email;
  final int pregnancyWeek;
  final Function(Map<String, dynamic>) onFoodSaved;

  const DetailedFoodEntryScreen({
    Key? key,
    required this.userId,
    required this.username,
    required this.email,
    required this.pregnancyWeek,
    required this.onFoodSaved,
  }) : super(key: key);

  @override
  State<DetailedFoodEntryScreen> createState() => _DetailedFoodEntryScreenState();
}

class _DetailedFoodEntryScreenState extends State<DetailedFoodEntryScreen> {
  final TextEditingController _foodController = TextEditingController();
  final TextEditingController _allergyController = TextEditingController();
  final TextEditingController _medicalConditionController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  
  bool _isLoading = false;
  bool _isSaving = false;
  bool _isLoadingPregnancyInfo = true;
  
  String _selectedMealType = 'breakfast';
  String _dietaryPreference = 'vegetarian';
  int _pregnancyWeek = 1;
  
  List<String> _allergies = [];
  List<String> _medicalConditions = [];
  
  // Dietary preference options
  final List<String> _dietaryOptions = [
    'vegetarian',
    'non-vegetarian',
    'vegan',
    'pescatarian',
    'gluten-free',
    'dairy-free'
  ];

  @override
  void initState() {
    super.initState();
    _pregnancyWeek = widget.pregnancyWeek;
    _fetchPregnancyInfo();
  }

  @override
  void dispose() {
    _foodController.dispose();
    _allergyController.dispose();
    _medicalConditionController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _fetchPregnancyInfo() async {
    try {
      setState(() {
        _isLoadingPregnancyInfo = true;
      });

      print('🔍 Fetching current pregnancy week for patient ID: ${widget.userId}');
      
      final response = await http.get(
        Uri.parse('${ApiConfig.nutritionBaseUrl}/get-current-pregnancy-week/${widget.userId}'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('✅ Current pregnancy week response: ${json.encode(data)}');
        
        if (data['success'] == true) {
          final currentWeek = data['current_pregnancy_week'] ?? 1;
          final autoFetched = data['auto_fetched'] ?? false;
          
          setState(() {
            _pregnancyWeek = currentWeek;
            _isLoadingPregnancyInfo = false;
          });
          
          print('✅ Auto-fetched pregnancy week: $_pregnancyWeek (Auto-fetched: $autoFetched)');
          
          // Show success message if auto-fetched
          if (autoFetched) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('✅ Pregnancy Week $_pregnancyWeek automatically fetched from your profile'),
                backgroundColor: Colors.green,
                duration: Duration(seconds: 3),
              ),
            );
          }
        } else {
          setState(() {
            _isLoadingPregnancyInfo = false;
          });
        }
      } else {
        setState(() {
          _isLoadingPregnancyInfo = false;
        });
      }
    } catch (e) {
      print('❌ Error fetching current pregnancy week: $e');
      setState(() {
        _isLoadingPregnancyInfo = false;
      });
    }
  }

  void _addAllergy() {
    final allergy = _allergyController.text.trim();
    if (allergy.isNotEmpty && !_allergies.contains(allergy)) {
      setState(() {
        _allergies.add(allergy);
        _allergyController.clear();
      });
    }
  }

  void _removeAllergy(String allergy) {
    setState(() {
      _allergies.remove(allergy);
    });
  }

  void _addMedicalCondition() {
    final condition = _medicalConditionController.text.trim();
    if (condition.isNotEmpty && !_medicalConditions.contains(condition)) {
      setState(() {
        _medicalConditions.add(condition);
        _medicalConditionController.clear();
      });
    }
  }

  void _removeMedicalCondition(String condition) {
    setState(() {
      _medicalConditions.remove(condition);
    });
  }

  Future<void> _saveDetailedFoodEntry() async {
    try {
      final foodDetails = _foodController.text.trim();
      if (foodDetails.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please enter food details first'),
            backgroundColor: Colors.orange,
          ),
        );
        return;
      }

      setState(() {
        _isSaving = true;
      });

      final foodData = {
        'userId': widget.userId,
        'userRole': 'patient',
        'username': widget.username,
        'email': widget.email,
        'food_details': foodDetails,
        'meal_type': _selectedMealType,
        // pregnancy_week is now auto-fetched by backend
        'dietary_preference': _dietaryPreference,
        'allergies': _allergies,
        'medical_conditions': _medicalConditions,
        'notes': _notesController.text.trim(),
        'timestamp': DateTime.now().toIso8601String(),
      };

      print('📤 Sending detailed food data to backend: $foodData');

      final response = await http.post(
        Uri.parse('${ApiConfig.nutritionBaseUrl}/nutrition/save-detailed-food-entry'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(foodData),
      ).timeout(const Duration(seconds: 60));

      print('📡 Save API Response Status: ${response.statusCode}');
      print('📡 Save API Response Body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ ${data['message'] ?? 'Detailed food entry saved successfully!'}'),
              backgroundColor: Colors.green,
            ),
          );
          
          // Call the callback to notify parent
          widget.onFoodSaved(foodData);
          
          // Navigate back
          Navigator.of(context).pop();
        } else {
          throw Exception(data['error'] ?? 'Unknown error saving detailed food entry');
        }
      } else {
        throw Exception('Save API returned status ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('❌ Error saving detailed food entry: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error saving: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Detailed Food Entry'),
        backgroundColor: AppColors.primary,
        foregroundColor: const Color.fromARGB(255, 251, 241, 241),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Pregnancy Week Display
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      Icon(Icons.pregnant_woman, color: Colors.pink[600], size: 24),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Pregnancy Week',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 8),
                            if (_isLoadingPregnancyInfo)
                              const CircularProgressIndicator(strokeWidth: 2)
                            else
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                decoration: BoxDecoration(
                                  color: Colors.pink[100],
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(color: Colors.pink[300]!),
                                ),
                                child: Text(
                                  'Week $_pregnancyWeek',
                                  style: TextStyle(
                                    color: Colors.pink[800],
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: _fetchPregnancyInfo,
                        icon: Icon(Icons.refresh, color: Colors.blue[600]),
                        tooltip: 'Refresh pregnancy info',
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Food Details
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Food Details',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _foodController,
                        maxLines: 3,
                                               decoration: InputDecoration(
                         hintText: 'Describe what you ate in detail...',
                         border: const OutlineInputBorder(),
                         filled: true,
                         fillColor: Colors.grey[50],
                       ),
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Meal Type and Dietary Preference
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Meal Type & Dietary Preference',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 16),
                      
                      // Meal Type
                      Text(
                        'Meal Type:',
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildSelectionChip('breakfast', 'Breakfast', Icons.wb_sunny),
                          _buildSelectionChip('lunch', 'Lunch', Icons.restaurant),
                          _buildSelectionChip('dinner', 'Dinner', Icons.nights_stay),
                          _buildSelectionChip('snack', 'Snack', Icons.coffee),
                        ],
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // Dietary Preference
                      Text(
                        'Dietary Preference:',
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                        value: _dietaryPreference,
                                                 decoration: InputDecoration(
                           border: const OutlineInputBorder(),
                           filled: true,
                           fillColor: Colors.grey[50],
                         ),
                        items: _dietaryOptions.map((String option) {
                          return DropdownMenuItem<String>(
                            value: option,
                            child: Text(option.replaceAll('-', ' ').toUpperCase()),
                          );
                        }).toList(),
                        onChanged: (String? newValue) {
                          if (newValue != null) {
                            setState(() {
                              _dietaryPreference = newValue;
                            });
                          }
                        },
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Allergies Section
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Allergies',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 16),
                      
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _allergyController,
                                                           decoration: InputDecoration(
                               hintText: 'Add allergy (e.g., nuts, dairy)',
                               border: const OutlineInputBorder(),
                               filled: true,
                               fillColor: Colors.grey[50],
                             ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: _addAllergy,
                            child: const Text('Add'),
                          ),
                        ],
                      ),
                      
                      if (_allergies.isNotEmpty) ...[
                        const SizedBox(height: 16),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: _allergies.map((allergy) => Chip(
                            label: Text(allergy),
                            deleteIcon: const Icon(Icons.close, size: 18),
                            onDeleted: () => _removeAllergy(allergy),
                            backgroundColor: Colors.red[100],
                            deleteIconColor: Colors.red[600],
                          )).toList(),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Medical Conditions Section
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Medical Conditions',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 16),
                      
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _medicalConditionController,
                                                           decoration: InputDecoration(
                               hintText: 'Add medical condition (e.g., diabetes, heart problem)',
                               border: const OutlineInputBorder(),
                               filled: true,
                               fillColor: Colors.grey[50],
                             ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: _addMedicalCondition,
                            child: const Text('Add'),
                          ),
                        ],
                      ),
                      
                      if (_medicalConditions.isNotEmpty) ...[
                        const SizedBox(height: 16),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: _medicalConditions.map((condition) => Chip(
                            label: Text(condition),
                            deleteIcon: const Icon(Icons.close, size: 18),
                            onDeleted: () => _removeMedicalCondition(condition),
                            backgroundColor: Colors.orange[100],
                            deleteIconColor: Colors.orange[600],
                          )).toList(),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Additional Notes
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Additional Notes',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _notesController,
                        maxLines: 3,
                                               decoration: InputDecoration(
                         hintText: 'Any additional information about your meal...',
                         border: const OutlineInputBorder(),
                         filled: true,
                         fillColor: Colors.grey[50],
                       ),
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Save Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isSaving ? null : _saveDetailedFoodEntry,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green[600],
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: _isSaving
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : const Text('Save Detailed Food Entry'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSelectionChip(String value, String label, IconData icon) {
    final isSelected = _selectedMealType == value;
    return FilterChip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: isSelected ? Colors.white : Colors.grey[600]),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: isSelected ? Colors.white : Colors.grey[700])),
        ],
      ),
      selected: isSelected,
      onSelected: (bool selected) {
        setState(() {
          _selectedMealType = value;
        });
      },
      backgroundColor: Colors.grey[200],
      selectedColor: Colors.blue[600],
      checkmarkColor: Colors.white,
    );
  }
}
