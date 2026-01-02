# VarejoUnido - App Flutter

App mobile para a plataforma VarejoUnido de compras coletivas.

## Funcionalidades

- ✅ Autenticação JWT (login/logout)
- ✅ Scanner de Encartes (OCR)
- ✅ Scanner de Produtos (foto)
- 🚧 Lista de Ofertas
- 🚧 Meus Cupons
- 🚧 Criação de Ofertas

## Configuração

### 1. Pré-requisitos

- Flutter SDK 3.0+
- Android Studio / VS Code
- Dispositivo ou emulador Android/iOS

### 2. Instalação

```bash
# Navegue até a pasta do app
cd varejounido_app

# Copie o arquivo de ambiente
cp .env.example .env

# Edite o .env com a URL da sua API
# API_BASE_URL=http://SEU_IP:8000/api/v1

# Instale as dependências
flutter pub get

# Execute o app
flutter run
```

### 3. Configuração da API

Edite o arquivo `.env` com o IP da máquina onde o Django está rodando:

```
API_BASE_URL=http://192.168.1.100:8000/api/v1
```

> **Importante:** Use o IP real da sua rede local, não `localhost` ou `127.0.0.1`.

### 4. Permissões necessárias

#### Android (`android/app/src/main/AndroidManifest.xml`)

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

#### iOS (`ios/Runner/Info.plist`)

```xml
<key>NSCameraUsageDescription</key>
<string>Precisamos da câmera para escanear encartes e produtos</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Precisamos acessar suas fotos para enviar imagens</string>
```

## Estrutura do Projeto

```
lib/
├── main.dart              # Entry point
├── models/                # Modelos de dados
├── providers/             # Gerenciamento de estado
│   └── auth_provider.dart
├── screens/               # Telas
│   ├── home_screen.dart
│   ├── login_screen.dart
│   ├── scanner_screen.dart
│   └── splash_screen.dart
├── services/              # Serviços
│   └── api_service.dart
└── widgets/               # Widgets reutilizáveis
```

## Funcionalidade de OCR

O app utiliza os endpoints de OCR do backend Django:

- `POST /api/v1/ofertas/scan-flyer/` - Escaneia encartes de supermercado
- `POST /api/v1/ofertas/scan-product/` - Escaneia fotos de produtos

### Fluxo de uso:

1. Usuário tira foto ou seleciona da galeria
2. App envia imagem para a API
3. Backend processa com Google Cloud Vision
4. Retorna produtos/preços identificados
5. Usuário pode criar oferta com dados pré-preenchidos

## Build

### Android APK

```bash
flutter build apk --release
```

### iOS (requer Mac com Xcode)

```bash
flutter build ios --release
```
