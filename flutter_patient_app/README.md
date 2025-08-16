# Patient Alert System - Flutter Mobile App

A beautiful and modern Flutter mobile application for the Patient Alert System, connecting to the Flask backend API.

## 🚀 Features

- **Modern UI/UX**: Beautiful Material Design interface
- **Authentication**: Login, Signup, and OTP verification
- **Profile Management**: Complete profile with pregnancy tracking
- **State Management**: Provider pattern for clean state management
- **API Integration**: Full integration with Flask backend
- **Form Validation**: Comprehensive input validation
- **Loading States**: Smooth loading indicators
- **Error Handling**: User-friendly error messages

## 📱 Screens

- **Login Screen**: Patient ID/Email login with password
- **Signup Screen**: User registration with validation
- **Home Screen**: Dashboard with quick actions
- **Profile Screen**: User profile management (coming soon)
- **Forgot Password**: Password reset functionality (coming soon)

## 🛠️ Setup Instructions

### Prerequisites

1. **Flutter SDK**: Install Flutter (version 3.0.0 or higher)
2. **Android Studio / VS Code**: For development
3. **Flask Backend**: Ensure the Flask API is running on `http://localhost:5000`

### Installation

1. **Navigate to the Flutter app directory**:
   ```bash
   cd flutter_patient_app
   ```

2. **Install dependencies**:
   ```bash
   flutter pub get
   ```

3. **Run the app**:
   ```bash
   flutter run
   ```

### Configuration

The app is configured to connect to the Flask backend at `http://localhost:5000`. If your backend is running on a different URL, update the `ApiConfig.baseUrl` in `lib/utils/constants.dart`.

## 📦 Dependencies

- **http**: For API communication
- **provider**: For state management
- **shared_preferences**: For local storage
- **flutter_secure_storage**: For secure storage
- **intl**: For date formatting
- **flutter_svg**: For SVG support
- **url_launcher**: For external links

## 🏗️ Project Structure

```
lib/
├── main.dart                 # App entry point
├── utils/
│   └── constants.dart        # App constants and colors
├── services/
│   └── api_service.dart      # API communication
├── providers/
│   ├── auth_provider.dart    # Authentication state
│   └── user_provider.dart    # User profile state
├── screens/
│   ├── login_screen.dart     # Login screen
│   ├── signup_screen.dart    # Signup screen
│   ├── home_screen.dart      # Home dashboard
│   ├── profile_screen.dart   # Profile screen
│   └── forgot_password_screen.dart # Password reset
└── widgets/
    ├── custom_text_field.dart # Custom text input
    └── loading_button.dart   # Loading button widget
```

## 🔧 API Integration

The app integrates with the following Flask API endpoints:

- `POST /signup` - User registration
- `POST /verify-otp` - OTP verification
- `POST /login` - User authentication
- `POST /forgot-password` - Password reset request
- `POST /reset-password` - Password reset
- `POST /complete-profile` - Profile completion
- `GET /profile/{patient_id}` - Get user profile

## 🎨 UI/UX Features

- **Consistent Design**: Material Design 3 principles
- **Color Scheme**: Professional medical app colors
- **Responsive Layout**: Works on different screen sizes
- **Loading States**: Smooth loading indicators
- **Error Handling**: User-friendly error messages
- **Form Validation**: Real-time input validation

## 🔐 Security Features

- **Secure Storage**: Sensitive data stored securely
- **Input Validation**: Client-side and server-side validation
- **Error Handling**: Secure error messages
- **Session Management**: Proper login/logout handling

## 🚀 Running the App

1. **Start the Flask backend**:
   ```bash
   python start_system.py
   ```

2. **Start the Flutter app**:
   ```bash
   cd flutter_patient_app
   flutter run
   ```

3. **Test the app**:
   - Create a new account
   - Verify OTP
   - Login with Patient ID or Email
   - Explore the dashboard

## 📱 Testing

### Manual Testing Steps

1. **Signup Flow**:
   - Fill in registration form
   - Verify OTP
   - Complete profile

2. **Login Flow**:
   - Login with Patient ID
   - Login with Email
   - Test forgot password

3. **Profile Management**:
   - View profile information
   - Update profile details
   - Test pregnancy calculations

## 🔧 Development

### Adding New Features

1. **Create new screen** in `lib/screens/`
2. **Add route** in `lib/main.dart`
3. **Update API service** if needed
4. **Add state management** in providers
5. **Test thoroughly**

### Code Style

- Follow Flutter conventions
- Use meaningful variable names
- Add comments for complex logic
- Keep widgets small and focused
- Use constants for repeated values

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Error**:
   - Ensure Flask backend is running
   - Check API URL in constants
   - Verify network connectivity

2. **Build Errors**:
   - Run `flutter clean`
   - Run `flutter pub get`
   - Check Flutter version compatibility

3. **Dependency Issues**:
   - Update dependencies: `flutter pub upgrade`
   - Check pubspec.yaml for conflicts

## 📄 License

This project is part of the Patient Alert System.

## 🤝 Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Test thoroughly before submitting

---

**Note**: This Flutter app is designed to work with the Flask backend API. Ensure the backend is running before testing the mobile app. 