import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../utils/date_utils.dart';

class PatientSymptomsTrackingScreen extends StatefulWidget {
  final String date;

  const PatientSymptomsTrackingScreen({
    super.key,
    required this.date,
  });

  @override
  State<PatientSymptomsTrackingScreen> createState() => _PatientSymptomsTrackingScreenState();
}

class _PatientSymptomsTrackingScreenState extends State<PatientSymptomsTrackingScreen> {
  final TextEditingController _symptomController = TextEditingController();
  final TextEditingController _severityController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  
  bool _isAnalyzing = false;
  String _analysisResult = '';
  String _errorMessage = '';
  int? _currentPregnancyWeek;
  bool _isLoadingPregnancyWeek = true;

  @override
  void initState() {
    super.initState();
    _loadPatientPregnancyWeek();
  }

  @override
  void dispose() {
    _symptomController.dispose();
    _severityController.dispose();
    _notesController.dispose();
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

  Future<void> _analyzeSymptoms() async {
    if (_symptomController.text.trim().isEmpty) {
      setState(() {
        _errorMessage = 'Please enter your symptoms';
      });
      return;
    }

    setState(() {
      _isAnalyzing = true;
      _errorMessage = '';
      _analysisResult = '';
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      // Use the pregnancy week loaded from profile or default to 20
      final pregnancyWeek = _currentPregnancyWeek ?? 20;
      print('🔍 Using pregnancy week: $pregnancyWeek');
      
      // Prepare symptom data for analysis with enhanced context
      final symptomData = {
        'text': _symptomController.text.trim(),  // Backend expects 'text' field
        'patient_id': userInfo['userId'] ?? 'unknown',
        'weeks_pregnant': pregnancyWeek,  // Dynamic pregnancy week from profile
        'severity': _severityController.text.trim(),
        'notes': _notesController.text.trim(),
        'date': widget.date,
        'userRole': userInfo['userRole'] ?? 'patient',
        'patient_context': {
          'pregnancy_week': pregnancyWeek,
          'trimester': _getTrimester(pregnancyWeek),
          'symptom_date': widget.date,
          'severity_level': _severityController.text.trim(),
          'additional_notes': _notesController.text.trim(),
        }
      };

      // Call the quantum+LLM analysis endpoint
      final response = await _callSymptomAnalysisAPI(symptomData);
      
      setState(() {
        _isAnalyzing = false;
        if (response.containsKey('error')) {
          _errorMessage = response['error'];
        } else {
          // Build comprehensive analysis result from quantum+LLM response
          final primaryRec = response['primary_recommendation'] ?? '';
          final additionalRecs = response['additional_recommendations'] ?? [];
          final redFlags = response['red_flags_detected'] ?? [];
          final trimester = response['trimester'] ?? '';
          final pregnancyWeek = response['pregnancy_week'] ?? '';
          final analysisMethod = response['analysis_method'] ?? '';
          final disclaimer = response['disclaimer'] ?? '';
          
          String result = '🤖 **AI Quantum Analysis**\n\n';
          
          if (trimester.isNotEmpty && pregnancyWeek.toString().isNotEmpty) {
            result += '🤱 **Pregnancy Stage:** Week $pregnancyWeek ($trimester)\n\n';
          }
          
          if (analysisMethod.isNotEmpty) {
            String methodDisplay = analysisMethod.contains('quantum') ? 'Quantum Vector Search + LLM' : 'LLM Analysis';
            result += '🔬 **Analysis Method:** $methodDisplay\n\n';
          }
          
          if (redFlags.isNotEmpty) {
            result += '🚨 **URGENT - Red Flags Detected:**\n';
            for (var flag in redFlags) {
              result += '• $flag\n';
            }
            result += '\n⚠️ **Please seek immediate medical attention!**\n\n';
          }
          
          if (primaryRec.isNotEmpty) {
            result += '💡 **Primary Recommendation:**\n$primaryRec\n\n';
          }
          
          if (additionalRecs.isNotEmpty) {
            result += '📝 **Additional Recommendations:**\n';
            for (var rec in additionalRecs) {
              result += '• $rec\n';
            }
            result += '\n';
          }
          
          if (disclaimer.isNotEmpty) {
            result += '⚕️ **Medical Disclaimer:**\n$disclaimer';
          }
          
          _analysisResult = result;
          
          // Save the analysis report to backend
          _saveAnalysisReport(response, symptomData);
        }
      });
    } catch (e) {
      setState(() {
        _isAnalyzing = false;
        _errorMessage = 'Error analyzing symptoms: $e';
      });
    }
  }

  Future<Map<String, dynamic>> _callSymptomAnalysisAPI(Map<String, dynamic> symptomData) async {
    // Call the actual Flask backend with quantum+LLM integration
    final apiService = ApiService();
    return await apiService.analyzeSymptoms(symptomData);
  }

  void _clearForm() {
    _symptomController.clear();
    _severityController.clear();
    _notesController.clear();
    setState(() {
      _analysisResult = '';
      _errorMessage = '';
    });
  }

  // Helper method to determine trimester based on pregnancy week
  String _getTrimester(int weeksPregnant) {
    if (weeksPregnant <= 12) {
      return 'First Trimester';
    } else if (weeksPregnant <= 26) {
      return 'Second Trimester';
    } else {
      return 'Third Trimester';
    }
  }

  // Save analysis report to backend
  Future<void> _saveAnalysisReport(Map<String, dynamic> analysisResponse, Map<String, dynamic> originalSymptomData) async {
    try {
      print('🔍 Saving analysis report to backend...');
      
      // Prepare report data for saving
      final reportData = {
        'patient_id': originalSymptomData['patient_id'],
        'symptom_text': originalSymptomData['text'],
        'weeks_pregnant': originalSymptomData['weeks_pregnant'],
        'severity': originalSymptomData['severity'],
        'notes': originalSymptomData['notes'],
        'date': originalSymptomData['date'],
        
        // AI Analysis Results
        'analysis_method': analysisResponse['analysis_method'] ?? 'quantum_llm',
        'primary_recommendation': analysisResponse['primary_recommendation'] ?? '',
        'additional_recommendations': analysisResponse['additional_recommendations'] ?? [],
        'red_flags_detected': analysisResponse['red_flags_detected'] ?? [],
        'disclaimer': analysisResponse['disclaimer'] ?? '',
        'urgency_level': 'moderate', // Default, can be enhanced later
        'knowledge_base_suggestions_count': analysisResponse['knowledge_base_suggestions_count'] ?? 0,
        
        // Patient Context
        'patient_context': originalSymptomData['patient_context'],
      };
      
      final apiService = ApiService();
      final saveResult = await apiService.saveSymptomAnalysisReport(reportData);
      
      if (saveResult.containsKey('success') && saveResult['success'] == true) {
        print('✅ Analysis report saved successfully!');
        print('🔍 Report ID: ${saveResult['report_id']}');
        print('🔍 Total reports: ${saveResult['analysisReportsCount']}');
        
        // Show success message to user
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✅ Analysis report saved to your medical history'),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 3),
          ),
        );
      } else {
        print('⚠️ Failed to save analysis report: ${saveResult['message']}');
        
        // Show warning message to user
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('⚠️ Analysis completed but could not save to history'),
            backgroundColor: Colors.orange,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      print('❌ Error saving analysis report: $e');
      
      // Show error message to user
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Error saving analysis report'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
          }
    }

  // View analysis history
  Future<void> _viewAnalysisHistory() async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userInfo = await authProvider.getCurrentUserInfo();
      
      if (userInfo['userId'] == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('❌ User ID not found'),
            backgroundColor: Colors.red,
          ),
        );
        return;
      }
      
      // Show loading dialog
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (BuildContext context) {
          return const AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 20),
                Text('Loading analysis history...'),
              ],
            ),
          );
        },
      );
      
      // Fetch analysis reports
      final apiService = ApiService();
      final reportsResult = await apiService.getSymptomAnalysisReports(userInfo['userId']!);
      
      // Close loading dialog
      Navigator.of(context).pop();
      
      if (reportsResult.containsKey('success') && reportsResult['success'] == true) {
        final reports = reportsResult['analysisReports'] ?? [];
        
        if (reports.isEmpty) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('📝 No analysis reports found yet'),
              backgroundColor: Colors.blue,
            ),
          );
        } else {
          // Navigate to history screen or show dialog
          _showAnalysisHistoryDialog(reports);
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Error loading history: ${reportsResult['message']}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      // Close loading dialog if still open
      if (Navigator.of(context).canPop()) {
        Navigator.of(context).pop();
      }
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Error: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // Show analysis history in a dialog
  void _showAnalysisHistoryDialog(List<dynamic> reports) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Symptom Analysis History'),
          content: SizedBox(
            width: double.maxFinite,
            height: 400,
            child: ListView.builder(
              itemCount: reports.length,
              itemBuilder: (context, index) {
                final report = reports[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text(
                      report['symptom_text'] ?? 'No symptoms',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Week ${report['weeks_pregnant']} (${report['trimester']})'),
                        Text('Date: ${report['analysis_date']}'),
                        if (report['ai_analysis']?['red_flags_detected']?.isNotEmpty == true)
                          Text(
                            '🚨 Red Flags Detected',
                            style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                          ),
                      ],
                    ),
                    trailing: Icon(
                      Icons.psychology,
                      color: report['ai_analysis']?['red_flags_detected']?.isNotEmpty == true 
                        ? Colors.red 
                        : Colors.green,
                    ),
                    onTap: () => _showReportDetails(report),
                  ),
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }

  // Show detailed report information
  void _showReportDetails(Map<String, dynamic> report) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Analysis Report - ${report['analysis_date']}'),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('**Symptoms:** ${report['symptom_text']}'),
                const SizedBox(height: 8),
                Text('**Pregnancy Week:** ${report['weeks_pregnant']} (${report['trimester']})'),
                const SizedBox(height: 8),
                Text('**Severity:** ${report['severity']}'),
                const SizedBox(height: 8),
                if (report['notes']?.isNotEmpty == true) ...[
                  Text('**Notes:** ${report['notes']}'),
                  const SizedBox(height: 8),
                ],
                const Divider(),
                const Text('**AI Analysis Results:**', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                if (report['ai_analysis']?['primary_recommendation']?.isNotEmpty == true) ...[
                  Text('**Primary Recommendation:**\n${report['ai_analysis']['primary_recommendation']}'),
                  const SizedBox(height: 8),
                ],
                if (report['ai_analysis']?['red_flags_detected']?.isNotEmpty == true) ...[
                  Text('**Red Flags:**', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                  ...report['ai_analysis']['red_flags_detected'].map<Widget>((flag) => 
                    Text('• $flag', style: TextStyle(color: Colors.red))
                  ),
                  const SizedBox(height: 8),
                ],
                Text('**Analysis Method:** ${report['ai_analysis']?['analysis_method'] ?? 'Unknown'}'),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Symptom Analysis'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'View Analysis History',
            onPressed: _viewAnalysisHistory,
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
                              Icons.sick,
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
                                  'AI Symptom Analysis',
                                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Get intelligent analysis using Quantum AI',
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

              // Symptom Input Form
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSizes.paddingLarge),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              'Describe Your Symptoms',
                              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ),
                          if (_currentPregnancyWeek != null)
                            Text(
                              'Personalized for Week $_currentPregnancyWeek',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppColors.primary,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      
                      TextFormField(
                        controller: _symptomController,
                        maxLines: 3,
                        decoration: const InputDecoration(
                          labelText: 'Symptoms *',
                          hintText: 'Describe your symptoms in detail...',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.sick),
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      TextFormField(
                        controller: _severityController,
                        decoration: const InputDecoration(
                          labelText: 'Severity Level',
                          hintText: 'Mild, Moderate, Severe',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.trending_up),
                        ),
                      ),
                      const SizedBox(height: 16),
                      
                      TextFormField(
                        controller: _notesController,
                        maxLines: 2,
                        decoration: const InputDecoration(
                          labelText: 'Additional Notes',
                          hintText: 'Any other relevant information...',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.note),
                        ),
                      ),
                      const SizedBox(height: 24),
                      
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton.icon(
                          onPressed: _isAnalyzing ? null : _analyzeSymptoms,
                          icon: _isAnalyzing 
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.psychology),
                          label: Text(_isAnalyzing ? 'Analyzing...' : 'Analyze with AI'),
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

              // Error Message
              if (_errorMessage.isNotEmpty)
                Card(
                  color: Colors.red.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(AppSizes.paddingMedium),
                    child: Row(
                      children: [
                        Icon(Icons.error, color: Colors.red.shade700),
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
                ),

              // Analysis Results
              if (_analysisResult.isNotEmpty)
                Expanded(
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(AppSizes.paddingLarge),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.psychology, color: AppColors.primary),
                              const SizedBox(width: 8),
                              Text(
                                'AI Analysis Results',
                                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.primary,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          Expanded(
                            child: SingleChildScrollView(
                              child: Text(
                                _analysisResult,
                                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                  color: AppColors.textPrimary,
                                  height: 1.5,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
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
