// lib/providers/auth_provider.dart

import 'package:flutter/foundation.dart';
import 'package:jwt_decoder/jwt_decoder.dart';
import '../services/api_service.dart';

enum AuthStatus {
  unknown,
  authenticated,
  unauthenticated,
}

class AuthProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  
  AuthStatus _status = AuthStatus.unknown;
  Map<String, dynamic>? _user;
  String? _error;
  bool _loading = false;
  
  AuthStatus get status => _status;
  Map<String, dynamic>? get user => _user;
  String? get error => _error;
  bool get loading => _loading;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  
  String get userName => _user?['first_name'] ?? _user?['username'] ?? 'Usuário';
  String get userEmail => _user?['email'] ?? '';
  bool get isVendedor => _user?['vendedor'] != null;
  
  /// Verifica se há uma sessão válida
  Future<void> checkAuthStatus() async {
    _loading = true;
    notifyListeners();
    
    try {
      final isAuth = await _api.isAuthenticated();
      
      if (isAuth) {
        // Tenta buscar dados do usuário
        _user = await _api.getMe();
        _status = AuthStatus.authenticated;
      } else {
        _status = AuthStatus.unauthenticated;
      }
    } catch (e) {
      _status = AuthStatus.unauthenticated;
    }
    
    _loading = false;
    notifyListeners();
  }
  
  /// Realiza login
  Future<bool> login(String username, String password) async {
    _loading = true;
    _error = null;
    notifyListeners();
    
    try {
      await _api.login(username, password);
      _user = await _api.getMe();
      _status = AuthStatus.authenticated;
      _loading = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _error = e.message;
      _status = AuthStatus.unauthenticated;
      _loading = false;
      notifyListeners();
      return false;
    } catch (e) {
      _error = 'Erro de conexão. Verifique sua internet.';
      _status = AuthStatus.unauthenticated;
      _loading = false;
      notifyListeners();
      return false;
    }
  }
  
  /// Realiza logout
  Future<void> logout() async {
    await _api.clearTokens();
    _user = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }
  
  /// Limpa mensagem de erro
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
