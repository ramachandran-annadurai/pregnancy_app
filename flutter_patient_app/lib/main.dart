import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/role_selection_screen.dart';
import 'screens/login_screen.dart';
import 'screens/signup_screen.dart';
import 'screens/home_screen.dart';
import 'screens/patient_daily_log_screen.dart';
import 'screens/patient_food_tracking_screen.dart';
import 'screens/patient_sleep_log_screen.dart';
import 'screens/patient_profile_screen.dart';
import 'screens/patient_symptoms_tracking_screen.dart';
import 'screens/patient_medication_tracking_screen.dart';
import 'screens/medication_dosage_list_screen.dart';
import 'screens/patient_daily_tracking_details_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/mental_health_screen.dart';

import 'screens/forgot_password_screen.dart';
import 'screens/otp_verification_screen.dart';
import 'screens/reset_password_screen.dart';
import 'screens/profile_completion_screen.dart';
import 'providers/auth_provider.dart';
import 'providers/user_provider.dart';
import 'utils/constants.dart';
import 'screens/patient_kick_counter_screen.dart';

void main() {
  runApp(const PatientAlertApp());
}

class PatientAlertApp extends StatelessWidget {
  const PatientAlertApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => UserProvider()),
      ],
      child: MaterialApp(
        title: 'Patient Alert System',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          primaryColor: AppColors.primary,
          scaffoldBackgroundColor: AppColors.background,
          appBarTheme: const AppBarTheme(
            backgroundColor: AppColors.primary,
            foregroundColor: Colors.white,
            elevation: 0,
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: const BorderSide(color: AppColors.border),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: const BorderSide(color: AppColors.border),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: const BorderSide(color: AppColors.primary, width: 2),
            ),
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          ),
        ),
        initialRoute: '/role-selection',
        routes: {
          '/role-selection': (context) => const RoleSelectionScreen(),
          '/login': (context) {
            final args = ModalRoute.of(context)!.settings.arguments as String?;
            return LoginScreen(role: args ?? 'patient');
          },
          '/signup': (context) {
            final args = ModalRoute.of(context)!.settings.arguments as String?;
            return SignupScreen(role: args ?? 'patient');
          },
          '/home': (context) => const HomeScreen(),
          '/patient-profile': (context) => const PatientProfileScreen(),
          '/patient-daily-log': (context) => const PatientDailyLogScreen(),
          '/patient-food-tracking': (context) {
            final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
            return PatientFoodTrackingScreen(
              date: args['date'],
            );
          },
          '/patient-sleep-log': (context) => PatientSleepLogScreen(
            userId: (ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>)['userId'],
            userRole: (ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>)['userRole'],
            username: (ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>)['username'],
            email: (ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>)['email'],
          ),
          '/patient-kick-counter': (context) => PatientKickCounterScreen(
            userId: (ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>)['userId'],
            userRole: (ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>)['userRole'],
            username: (ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>)['username'],
            email: (ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>)['email'],
          ),
          '/patient-symptoms-tracking': (context) {
            final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>;
            return PatientSymptomsTrackingScreen(
              date: args['date'],
            );
          },
          '/patient-medication-tracking': (context) {
            final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>;
            return PatientMedicationTrackingScreen(
              date: args['date'],
            );
          },
          '/medication-dosage-list': (context) => const MedicationDosageListScreen(),
          '/patient-daily-tracking-details': (context) => const PatientDailyTrackingDetailsScreen(),
          '/mental-health': (context) {
            final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
            return MentalHealthScreen(
              selectedDate: args?['selectedDate'],
            );
          },
          '/profile': (context) => const ProfileScreen(),
          '/forgot-password': (context) => const ForgotPasswordScreen(),
          '/otp-verification': (context) {
            final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
            return OtpVerificationScreen(
              email: args['email'],
              role: args['role'] ?? 'patient',
            );
          },
          '/reset-password': (context) {
            final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
            return ResetPasswordScreen(email: args['email']);
          },
          '/profile-completion': (context) => const ProfileCompletionScreen(),
        },
        debugShowCheckedModeBanner: false,
      ),
    );
  }
} 