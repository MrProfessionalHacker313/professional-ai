import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService extends ChangeNotifier {
  static final AuthService instance = AuthService._();
  AuthService._();

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  Map<String, dynamic>? _currentUser;
  bool _isOnline = true;

  Map<String, dynamic>? get currentUser => _currentUser;
  bool get isOnline => _isOnline;
  bool get isAuthenticated => _currentUser != null;

  Future<void> init() async {
    await _loadUser();
  }

  Future<void> _loadUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString('current_user');
    if (userJson != null) {
      _currentUser = json.decode(userJson);
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>> signInWithProvider(String provider, Map<String, dynamic> userData) async {
    final response = await _post('/api/auth/social', {
      'provider': provider,
      ...userData,
    });

    _currentUser = Map<String, dynamic>.from(response['user'] ?? {});
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('current_user', json.encode(_currentUser));
    await _secureStorage.write(key: 'access_token', value: response['access_token']);
    notifyListeners();

    return Map<String, dynamic>.from(response);
  }

  Future<Map<String, dynamic>> signInWithPhone(String phoneNumber) async {
    final response = await _post('/api/auth/phone/send-otp', {
      'phone': phoneNumber,
      'mode': 'dev',
    });

    final otpController = TextEditingController();
    final confirmed = await _showOtpDialog(otpController);
    if (confirmed != true) {
      throw Exception('OTP cancelled');
    }

    final verifyResponse = await _post('/api/auth/phone/verify-otp', {
      'phone': phoneNumber,
      'otp': otpController.text,
    });

    _currentUser = Map<String, dynamic>.from(verifyResponse['user'] ?? {});
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('current_user', json.encode(_currentUser));
    await _secureStorage.write(key: 'access_token', value: verifyResponse['access_token']);
    notifyListeners();

    return Map<String, dynamic>.from(verifyResponse);
  }

  Future<Map<String, dynamic>> verify2FA(String code) async {
    final response = await _post('/api/auth/2fa/verify', {'code': code});
    return Map<String, dynamic>.from(response);
  }

  Future<Map<String, dynamic>> setupPasskey() async {
    final response = await _post('/api/auth/passkey/setup', {});
    return Map<String, dynamic>.from(response);
  }

  Future<Map<String, dynamic>> skipPasskey() async {
    final response = await _post('/api/auth/passkey/skip', {});
    return Map<String, dynamic>.from(response);
  }

  Future<void> signOut() async {
    _currentUser = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('current_user');
    await _secureStorage.delete(key: 'access_token');
    notifyListeners();
  }

  Future<String?> getAccessToken() async {
    return await _secureStorage.read(key: 'access_token');
  }

  Future<Map<String, dynamic>> _post(String endpoint, Map<String, dynamic> data) async {
    final token = await getAccessToken();
    final response = await ApiService.instance.post(endpoint, data, token);
    return Map<String, dynamic>.from(response);
  }

  Future<bool?> _showOtpDialog(TextEditingController controller) async {
    bool? result;
    await showDialog(
      context: navigatorKey.currentContext!,
      builder: (context) => AlertDialog(
        title: const Text('Enter OTP'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: '123456'),
          keyboardType: TextInputType.number,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Verify')),
        ],
      ),
    );
    return result;
  }
}

final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();
