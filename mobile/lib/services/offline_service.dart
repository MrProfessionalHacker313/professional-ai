import 'package:flutter/foundation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

class OfflineService extends ChangeNotifier {
  static final OfflineService instance = OfflineService._();
  OfflineService._();

  final Connectivity _connectivity = Connectivity();
  bool _isOnline = true;
  final List<Map<String, dynamic>> _offlineQueue = [];

  bool get isOnline => _isOnline;

  Future<void> init() async {
    _connectivity.onConnectivityChanged.listen((results) {
      final wasOffline = !_isOnline;
      _isOnline = results.any((r) => r != ConnectivityResult.none);
      notifyListeners();

      if (wasOffline && _isOnline) {
        _syncOfflineQueue();
      }
    });

    final result = await _connectivity.checkConnectivity();
    _isOnline = result.any((r) => r != ConnectivityResult.none);
  }

  Future<void> _syncOfflineQueue() async {
    if (_offlineQueue.isEmpty) return;
    debugPrint('Syncing ${_offlineQueue.length} offline operations');
    _offlineQueue.clear();
    notifyListeners();
  }

  void addToQueue(Map<String, dynamic> operation) {
    _offlineQueue.add(operation);
    notifyListeners();
  }
}
