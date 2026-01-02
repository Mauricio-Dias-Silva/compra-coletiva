// lib/screens/scanner_screen.dart

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';

enum ScanMode { flyer, product }

class ScannerScreen extends StatefulWidget {
  final ScanMode initialMode;
  
  const ScannerScreen({
    super.key,
    this.initialMode = ScanMode.flyer,
  });

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final ApiService _api = ApiService();
  final ImagePicker _picker = ImagePicker();
  
  late ScanMode _currentMode;
  File? _selectedImage;
  bool _isProcessing = false;
  Map<String, dynamic>? _scanResult;
  String? _error;

  @override
  void initState() {
    super.initState();
    _currentMode = widget.initialMode;
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 85,
      );
      
      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _scanResult = null;
          _error = null;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Erro ao selecionar imagem: $e';
      });
    }
  }

  Future<void> _processImage() async {
    if (_selectedImage == null) return;
    
    setState(() {
      _isProcessing = true;
      _error = null;
    });
    
    try {
      final result = _currentMode == ScanMode.flyer
          ? await _api.scanFlyer(_selectedImage!)
          : await _api.scanProduct(_selectedImage!);
      
      setState(() {
        _scanResult = result;
        _isProcessing = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = e.message;
        _isProcessing = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Erro ao processar imagem: $e';
        _isProcessing = false;
      });
    }
  }

  void _clearSelection() {
    setState(() {
      _selectedImage = null;
      _scanResult = null;
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_currentMode == ScanMode.flyer 
            ? 'Escanear Encarte' 
            : 'Foto do Produto'),
        actions: [
          if (_selectedImage != null)
            IconButton(
              icon: const Icon(Icons.delete_outline),
              onPressed: _clearSelection,
            ),
        ],
      ),
      body: Column(
        children: [
          // Mode Selector
          Container(
            padding: const EdgeInsets.all(16),
            child: SegmentedButton<ScanMode>(
              selected: {_currentMode},
              onSelectionChanged: (Set<ScanMode> newSelection) {
                setState(() {
                  _currentMode = newSelection.first;
                  _selectedImage = null;
                  _scanResult = null;
                  _error = null;
                });
              },
              segments: const [
                ButtonSegment(
                  value: ScanMode.flyer,
                  icon: Icon(Icons.document_scanner),
                  label: Text('Encarte'),
                ),
                ButtonSegment(
                  value: ScanMode.product,
                  icon: Icon(Icons.camera_alt),
                  label: Text('Produto'),
                ),
              ],
            ),
          ),
          
          // Main Content
          Expanded(
            child: _selectedImage == null
                ? _buildImagePicker()
                : _buildImagePreview(),
          ),
          
          // Results
          if (_scanResult != null) _buildResults(),
          
          // Error
          if (_error != null)
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.red.shade200),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: Colors.red.shade700),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _error!,
                      style: TextStyle(color: Colors.red.shade700),
                    ),
                  ),
                ],
              ),
            ),
          
          // Process Button
          if (_selectedImage != null && _scanResult == null)
            Container(
              padding: const EdgeInsets.all(16),
              child: FilledButton.icon(
                onPressed: _isProcessing ? null : _processImage,
                icon: _isProcessing
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.search),
                label: Text(_isProcessing 
                    ? 'Processando...' 
                    : 'Analisar Imagem'),
                style: FilledButton.styleFrom(
                  minimumSize: const Size(double.infinity, 56),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildImagePicker() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          _currentMode == ScanMode.flyer 
              ? Icons.document_scanner 
              : Icons.camera_alt,
          size: 80,
          color: Colors.grey[400],
        ),
        const SizedBox(height: 24),
        Text(
          _currentMode == ScanMode.flyer
              ? 'Escaneie um encarte de supermercado\npara extrair produtos e preços'
              : 'Tire uma foto do produto\npara preencher automaticamente',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: Colors.grey[600],
            fontSize: 16,
          ),
        ),
        const SizedBox(height: 32),
        
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FilledButton.tonalIcon(
              onPressed: () => _pickImage(ImageSource.camera),
              icon: const Icon(Icons.camera_alt),
              label: const Text('Câmera'),
            ),
            const SizedBox(width: 16),
            FilledButton.tonalIcon(
              onPressed: () => _pickImage(ImageSource.gallery),
              icon: const Icon(Icons.photo_library),
              label: const Text('Galeria'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildImagePreview() {
    return Container(
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Image.file(
          _selectedImage!,
          fit: BoxFit.contain,
        ),
      ),
    );
  }

  Widget _buildResults() {
    final result = _scanResult!;
    final isFlyer = _currentMode == ScanMode.flyer;
    
    return Container(
      constraints: const BoxConstraints(maxHeight: 300),
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.green.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.green.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.shade100,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(15)),
            ),
            child: Row(
              children: [
                Icon(Icons.check_circle, color: Colors.green.shade700),
                const SizedBox(width: 8),
                Text(
                  isFlyer 
                      ? 'Produtos Encontrados: ${result['products_count'] ?? 0}'
                      : 'Informações Extraídas',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.green.shade700,
                  ),
                ),
              ],
            ),
          ),
          
          // Content
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: isFlyer ? _buildFlyerResults(result) : _buildProductResults(result),
            ),
          ),
          
          // Action Buttons
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _clearSelection,
                    child: const Text('Nova Imagem'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: () {
                      // TODO: Navegar para tela de criação de oferta com dados pré-preenchidos
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Funcionalidade de criar oferta em desenvolvimento'),
                        ),
                      );
                    },
                    child: const Text('Criar Oferta'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFlyerResults(Map<String, dynamic> result) {
    final products = result['products'] as List? ?? [];
    final validityDate = result['validity_date'];
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (validityDate != null) ...[
          Row(
            children: [
              const Icon(Icons.event, size: 16, color: Colors.grey),
              const SizedBox(width: 4),
              Text(
                'Válido até: $validityDate',
                style: const TextStyle(color: Colors.grey),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Divider(),
        ],
        
        if (products.isEmpty)
          const Text('Nenhum produto identificado na imagem.')
        else
          ...products.map((p) => ListTile(
            dense: true,
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.local_offer, size: 20),
            title: Text(p['nome'] ?? 'Produto'),
            trailing: Text(
              'R\$ ${(p['preco'] ?? 0).toStringAsFixed(2)}',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.green,
              ),
            ),
          )),
      ],
    );
  }

  Widget _buildProductResults(Map<String, dynamic> result) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (result['suggested_name'] != null) ...[
          const Text(
            'Nome Sugerido:',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          Text(result['suggested_name']),
          const SizedBox(height: 12),
        ],
        
        if (result['store_name'] != null) ...[
          const Text(
            'Loja Identificada:',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          Text(result['store_name']),
          const SizedBox(height: 12),
        ],
        
        if (result['validity_date'] != null) ...[
          const Text(
            'Data de Validade:',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          Text(result['validity_date']),
        ],
        
        if (result['suggested_name'] == null && 
            result['store_name'] == null && 
            result['validity_date'] == null)
          const Text('Não foi possível extrair informações da imagem.'),
      ],
    );
  }
}
