import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'package:twitter_login/twitter_login.dart';
import '../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _isLoading = false;

  Future<void> _signInWithGoogle() async {
    setState(() => _isLoading = true);
    try {
      final googleUser = await GoogleSignIn().signIn();
      if (googleUser != null && mounted) {
        final result = await AuthService.instance.signInWithProvider(
          'google',
          {
            'email': googleUser.email,
            'name': googleUser.displayName ?? '',
            'photo': googleUser.photoUrl ?? '',
            'id': googleUser.id,
          },
        );
        _handleAuthResult(result);
      }
    } catch (e) {
      _showError('Google sign-in failed: ${e.toString()}');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _signInWithApple() async {
    setState(() => _isLoading = true);
    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [AppleIDAuthorizationScopes.email, AppleIDAuthorizationScopes.fullName],
      );
      if (mounted) {
        final result = await AuthService.instance.signInWithProvider(
          'apple',
          {
            'email': credential.email ?? '',
            'name': '${credential.givenName ?? ''} ${credential.familyName ?? ''}'.trim(),
            'id': credential.userIdentifier ?? '',
          },
        );
        _handleAuthResult(result);
      }
    } catch (e) {
      _showError('Apple sign-in failed: ${e.toString()}');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _signInWithTwitter() async {
    setState(() => _isLoading = true);
    try {
      final twitterLogin = TwitterLogin(
        apiKey: 'YOUR_TWITTER_API_KEY',
        apiSecretKey: 'YOUR_TWITTER_API_SECRET',
        redirectURI: 'professionalai://twitter-callback',
      );
      final result = await twitterLogin.login();
      if (result.authToken != null && mounted) {
        final authResult = await AuthService.instance.signInWithProvider(
          'twitter',
          {
            'email': result.user?.screenName ?? '',
            'name': result.user?.name ?? '',
            'photo': result.user?.profileImageUrl ?? '',
            'id': result.user?.id.toString() ?? '',
          },
        );
        _handleAuthResult(authResult);
      }
    } catch (e) {
      _showError('Twitter sign-in failed: ${e.toString()}');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _signInWithPhone() async {
    setState(() => _isLoading = true);
    try {
      final phoneController = TextEditingController();
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Phone Sign In'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Enter your phone number with country code'),
              const SizedBox(height: 16),
              TextField(
                controller: phoneController,
                decoration: const InputDecoration(
                  hintText: '+1234567890',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.phone,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Send OTP'),
            ),
          ],
        ),
      );

      if (confirmed == true && phoneController.text.isNotEmpty) {
        final result = await AuthService.instance.signInWithPhone(phoneController.text);
        _handleAuthResult(result);
      }
    } catch (e) {
      _showError('Phone sign-in failed: ${e.toString()}');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _handleAuthResult(Map<String, dynamic> result) {
    if (result['needs2FA'] == true) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const TwoFactorScreen()),
      );
    } else if (result['needsPasskey'] == true) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const PasskeyScreen()),
      );
    } else {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
      );
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF0B1220), Color(0xFF1E3A5F)],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                const Spacer(),
                Image.asset(
                  'assets/images/eagle_logo.png',
                  width: 100,
                  height: 100,
                  errorBuilder: (_, __, ___) => const Icon(
                    Icons.bolt,
                    size: 64,
                    color: Color(0xFF06B6D4),
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Professional AI',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  "World's Most Powerful AI Assistant",
                  style: TextStyle(
                    fontSize: 16,
                    color: Color(0xFF94A3B8),
                  ),
                ),
                const Spacer(),
                if (_isLoading)
                  const Padding(
                    padding: EdgeInsets.all(16.0),
                    child: CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF06B6D4)),
                    ),
                  ),
                const SizedBox(height: 24),
                _buildSignInButton(
                  icon: Icons.g_mobiledata,
                  label: 'Continue with Google',
                  onTap: _signInWithGoogle,
                ),
                const SizedBox(height: 12),
                _buildSignInButton(
                  icon: Icons.apple,
                  label: 'Continue with Apple',
                  onTap: _signInWithApple,
                ),
                const SizedBox(height: 12),
                _buildSignInButton(
                  icon: Icons.code,
                  label: 'Continue with GitHub',
                  onTap: _signInWithPhone,
                ),
                const SizedBox(height: 12),
                _buildSignInButton(
                  icon: Icons.phone_android,
                  label: 'Continue with Phone',
                  onTap: _signInWithPhone,
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSignInButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        onPressed: _isLoading ? null : onTap,
        icon: Icon(icon, size: 24),
        label: Text(
          label,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF1E293B),
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFF334155)),
          ),
        ),
      ),
    );
  }
}
