class N8NConfig {
  // N8N Webhook Configuration
  // Replace these URLs with your actual N8N webhook endpoints

  // Main prescription processing webhook
  static const String prescriptionWebhookUrl = 'https://n8n.srv795087.hstgr.cloud/webhook/bf25c478-c4a9-44c5-8f43-08c3fcae51f9';

  // Alternative webhook for different processing types
  static const String medicationAnalysisWebhookUrl = 'https://n8n.srv795087.hstgr.cloud/webhook/bf25c478-c4a9-44c5-8f43-08c3fcae51f9';

  // Webhook for prescription validation
  static const String prescriptionValidationWebhookUrl = 'https://n8n.srv795087.hstgr.cloud/webhook/bf25c478-c4a9-44c5-8f43-08c3fcae51f9';

  // Test webhook for development
  static const String testWebhookUrl = 'https://n8n.srv795087.hstgr.cloud/webhook/bf25c478-c4a9-44c5-8f43-08c3fcae51f9';

  // Get the appropriate webhook URL based on processing type
  static String getWebhookUrl(String processingType) {
    switch (processingType.toLowerCase()) {
      case 'prescription':
        return prescriptionWebhookUrl;
      case 'medication_analysis':
        return medicationAnalysisWebhookUrl;
      case 'validation':
        return prescriptionValidationWebhookUrl;
      case 'test':
        return testWebhookUrl;
      default:
        return prescriptionWebhookUrl;
    }
  }

  // Check if webhook URLs are configured
  static bool get isConfigured {
    return prescriptionWebhookUrl != 'https://your-n8n-instance.com/webhook/prescription-processor' &&
           prescriptionWebhookUrl.isNotEmpty;
  }

  // Get webhook configuration status
  static Map<String, dynamic> get configurationStatus {
    return {
      'configured': isConfigured,
      'prescription_webhook': prescriptionWebhookUrl,
      'medication_analysis_webhook': medicationAnalysisWebhookUrl,
      'validation_webhook': prescriptionValidationWebhookUrl,
      'test_webhook': testWebhookUrl,
    };
  }
}
