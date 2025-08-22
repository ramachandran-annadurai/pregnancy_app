// Comprehensive date utility functions for handling various date formats
class AppDateUtils {
  /// Safely format a date that could be either a String or DateTime
  /// This prevents the "String is not a subtype of DateTime" error
  static String formatDate(dynamic date) {
    try {
      if (date is DateTime) {
        return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
      } else if (date is String) {
        // Check if it's already in DD/MM/YYYY format
        if (date.contains('/') && date.split('/').length == 3) {
          final parts = date.split('/');
          if (parts.length == 3) {
            final day = int.parse(parts[0]);
            final month = int.parse(parts[1]);
            final year = int.parse(parts[2]);
            return '${day.toString().padLeft(2, '0')}/${month.toString().padLeft(2, '0')}/${year}';
          }
        }
        
        // Try to parse as ISO format
        try {
          final dateTime = DateTime.parse(date);
          return '${dateTime.day.toString().padLeft(2, '0')}/${dateTime.month.toString().padLeft(2, '0')}/${dateTime.year}';
        } catch (e) {
          // If ISO parsing fails, return the original string
          return date;
        }
      }
      return date.toString();
    } catch (e) {
      return date.toString();
    }
  }

  /// Safely format a date time string that could be in various formats
  static String formatDateTime(String dateTimeString) {
    try {
      // Check if it's already in DD/MM/YYYY format
      if (dateTimeString.contains('/') && dateTimeString.split('/').length == 3) {
        // Parse DD/MM/YYYY format
        final parts = dateTimeString.split('/');
        if (parts.length == 3) {
          final day = int.parse(parts[0]);
          final month = int.parse(parts[1]);
          final year = int.parse(parts[2]);
          return '${day.toString().padLeft(2, '0')}/${month.toString().padLeft(2, '0')}/${year}';
        }
      }
      
      // Try to parse as ISO format
      try {
        final dateTime = DateTime.parse(dateTimeString);
        return '${dateTime.day.toString().padLeft(2, '0')}/${dateTime.month.toString().padLeft(2, '0')}/${dateTime.year}';
      } catch (e) {
        // If ISO parsing fails, return the original string
        return dateTimeString;
      }
    } catch (e) {
      // If parsing fails, return the original string
      return dateTimeString;
    }
  }

  /// Convert a date string to DateTime object safely
  static DateTime? parseDate(dynamic date) {
    try {
      if (date is DateTime) {
        return date;
      } else if (date is String) {
        // Check if it's in DD/MM/YYYY format
        if (date.contains('/') && date.split('/').length == 3) {
          final parts = date.split('/');
          if (parts.length == 3) {
            final day = int.parse(parts[0]);
            final month = int.parse(parts[1]);
            final year = int.parse(parts[2]);
            return DateTime(year, month, day);
          }
        }
        
        // Try to parse as ISO format
        return DateTime.parse(date);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Check if a date string is valid
  static bool isValidDate(dynamic date) {
    try {
      if (date is DateTime) {
        return true;
      } else if (date is String) {
        // Check if it's in DD/MM/YYYY format
        if (date.contains('/') && date.split('/').length == 3) {
          final parts = date.split('/');
          if (parts.length == 3) {
            final day = int.parse(parts[0]);
            final month = int.parse(parts[1]);
            final year = int.parse(parts[2]);
            return day >= 1 && day <= 31 && month >= 1 && month <= 12 && year > 1900;
          }
        }
        
        // Try to parse as ISO format
        DateTime.parse(date);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  /// Get current date in DD/MM/YYYY format
  static String getCurrentDate() {
    final now = DateTime.now();
    return '${now.day.toString().padLeft(2, '0')}/${now.month.toString().padLeft(2, '0')}/${now.year}';
  }

  /// Get current date time in ISO format
  static String getCurrentDateTime() {
    return DateTime.now().toIso8601String();
  }
}
