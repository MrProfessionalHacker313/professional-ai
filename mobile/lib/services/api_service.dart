import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:hive_flutter/hive_flutter.dart';

class ApiService {
  static final ApiService instance = ApiService._();
  ApiService._();

  static const String _baseUrl = String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000/api');
  final Connectivity _connectivity = Connectivity();
  Box? _offlineBox;

  Future<void> init() async {
    _offlineBox = await Hive.openBox('offline_operations');
  }

  Future<bool> get isOnline async {
    final result = await _connectivity.checkConnectivity();
    return result.any((c) => c != ConnectivityResult.none);
  }

  Future<Map<String, dynamic>> get(String endpoint, {String? token}) async {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (token != null) headers['Authorization'] = 'Bearer $token';

    final response = await http.get(Uri.parse('$_baseUrl$endpoint'), headers: headers);
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> data, [String? token]) async {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (token != null) headers['Authorization'] = 'Bearer $token';

    final online = await isOnline;
    if (!online) {
      await _queueOfflineOperation(endpoint, data, token);
      return {'offline': true, 'message': 'Queued for sync when online'};
    }

    final response = await http.post(
      Uri.parse('$_baseUrl$endpoint'),
      headers: headers,
      body: json.encode(data),
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> chat(String prompt) async {
    return post('/chat', {'prompt': prompt, 'mode': 'chat', 'stream': false});
  }

  Future<Map<String, dynamic>> generateCode(String prompt, String language) async {
    return post('/code', {'prompt': prompt, 'language': language});
  }

  Future<Map<String, dynamic>> generateImage(File image) async {
    final token = await AuthService.instance.getAccessToken();
    final request = http.MultipartRequest('POST', Uri.parse('$_baseUrl/media/generate'))
      ..headers['Authorization'] = 'Bearer $token' ?? ''
      ..files.add(await http.MultipartFile.fromPath('file', image.path));
    
    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);
    return _handleResponse(response);
  }

  Future<List<dynamic>> getVaultItems() async {
    final token = await AuthService.instance.getAccessToken();
    final response = await get('/vault/items', token: token);
    return response['items'] ?? [];
  }

  Future<Map<String, dynamic>> saveVaultItem(String key, String value) async {
    final token = await AuthService.instance.getAccessToken();
    return post('/vault/items', {'key': key, 'value': value}, token);
  }

  Future<Map<String, dynamic>> deleteVaultItem(String key) async {
    final token = await AuthService.instance.getAccessToken();
    final response = await http.delete(
      Uri.parse('$_baseUrl/vault/items/$key'),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
    );
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> getAdminStats() async {
    final token = await AuthService.instance.getAccessToken();
    return get('/admin/stats', token: token);
  }

  Future<Map<String, dynamic>> subscribe(String plan) async {
    final token = await AuthService.instance.getAccessToken();
    return post('/payments/subscribe', {'plan': plan}, token);
  }

  Future<void> _queueOfflineOperation(String endpoint, Map<String, dynamic> data, String? token) async {
    if (_offlineBox == null) return;
    await _offlineBox!.add({
      'endpoint': endpoint,
      'data': data,
      'token': token,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  Map<String, dynamic> _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return json.decode(response.body);
    }
    throw Exception('API Error: ${response.statusCode} - ${response.body}');
  }
}
