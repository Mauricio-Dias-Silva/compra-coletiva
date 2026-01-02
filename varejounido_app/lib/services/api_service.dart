// lib/services/api_service.dart

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Classe de exceção personalizada para erros de API
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  
  ApiException(this.message, {this.statusCode});
  
  @override
  String toString() => 'ApiException: $message (status: $statusCode)';
}

/// Serviço principal para comunicação com a API Django
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();
  
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  String get baseUrl => dotenv.env['API_BASE_URL'] ?? 'http://192.168.0.244:8000/api/v1';
  
  /// Headers padrão para requisições
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  /// Headers com autenticação JWT
  Future<Map<String, String>> _authHeaders() async {
    final token = await _storage.read(key: 'access_token');
    return {
      ..._headers,
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }
  
  /// Salva os tokens JWT
  Future<void> saveTokens({required String access, required String refresh}) async {
    await _storage.write(key: 'access_token', value: access);
    await _storage.write(key: 'refresh_token', value: refresh);
  }
  
  /// Remove os tokens (logout)
  Future<void> clearTokens() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }
  
  /// Verifica se o usuário está autenticado
  Future<bool> isAuthenticated() async {
    final token = await _storage.read(key: 'access_token');
    return token != null;
  }
  
  /// Login - obtém tokens JWT
  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/token/'),
      headers: _headers,
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await saveTokens(
        access: data['access'],
        refresh: data['refresh'],
      );
      return data;
    } else if (response.statusCode == 401) {
      throw ApiException('Credenciais inválidas', statusCode: 401);
    } else {
      throw ApiException('Erro ao fazer login', statusCode: response.statusCode);
    }
  }
  
  /// Refresh do token
  Future<bool> refreshToken() async {
    final refreshToken = await _storage.read(key: 'refresh_token');
    if (refreshToken == null) return false;
    
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/token/refresh/'),
        headers: _headers,
        body: jsonEncode({'refresh': refreshToken}),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await _storage.write(key: 'access_token', value: data['access']);
        if (data['refresh'] != null) {
          await _storage.write(key: 'refresh_token', value: data['refresh']);
        }
        return true;
      }
    } catch (e) {
      // Falha no refresh
    }
    
    await clearTokens();
    return false;
  }
  
  /// GET request autenticado
  Future<dynamic> get(String endpoint) async {
    final response = await http.get(
      Uri.parse('$baseUrl$endpoint'),
      headers: await _authHeaders(),
    );
    
    if (response.statusCode == 401) {
      // Tenta refresh e retry
      if (await refreshToken()) {
        return get(endpoint);
      }
      throw ApiException('Sessão expirada', statusCode: 401);
    }
    
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body);
    }
    
    throw ApiException('Erro na requisição', statusCode: response.statusCode);
  }
  
  /// POST request autenticado
  Future<dynamic> post(String endpoint, Map<String, dynamic> body) async {
    final response = await http.post(
      Uri.parse('$baseUrl$endpoint'),
      headers: await _authHeaders(),
      body: jsonEncode(body),
    );
    
    if (response.statusCode == 401) {
      if (await refreshToken()) {
        return post(endpoint, body);
      }
      throw ApiException('Sessão expirada', statusCode: 401);
    }
    
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body);
    }
    
    throw ApiException('Erro na requisição', statusCode: response.statusCode);
  }
  
  /// Upload de imagem para OCR
  Future<Map<String, dynamic>> uploadImageForOCR(String endpoint, File imageFile) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final request = http.MultipartRequest('POST', uri);
    
    // Adiciona headers de autenticação
    final authHeaders = await _authHeaders();
    request.headers.addAll(authHeaders);
    
    // Adiciona o arquivo
    request.files.add(await http.MultipartFile.fromPath('image', imageFile.path));
    
    try {
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 401) {
        if (await refreshToken()) {
          return uploadImageForOCR(endpoint, imageFile);
        }
        throw ApiException('Sessão expirada', statusCode: 401);
      }
      
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return jsonDecode(response.body);
      }
      
      final errorBody = jsonDecode(response.body);
      throw ApiException(
        errorBody['error'] ?? 'Erro ao processar imagem',
        statusCode: response.statusCode,
      );
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Erro de conexão: $e');
    }
  }
  
  /// Escanear encarte de supermercado
  Future<Map<String, dynamic>> scanFlyer(File imageFile) async {
    return uploadImageForOCR('/ofertas/scan-flyer/', imageFile);
  }
  
  /// Escanear foto de produto
  Future<Map<String, dynamic>> scanProduct(File imageFile) async {
    return uploadImageForOCR('/ofertas/scan-product/', imageFile);
  }
  
  /// Buscar dados do usuário logado
  Future<Map<String, dynamic>> getMe() async {
    return await get('/contas/me/');
  }
  
  /// Listar ofertas
  Future<List<dynamic>> getOfertas() async {
    final data = await get('/ofertas/');
    return data is List ? data : data['results'] ?? [];
  }
  
  /// Listar categorias
  Future<List<dynamic>> getCategorias() async {
    final data = await get('/ofertas/categorias/');
    return data is List ? data : data['results'] ?? [];
  }
}
