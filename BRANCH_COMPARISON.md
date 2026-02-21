# Comparação entre Branches: Master vs Dev

## Visão Geral

Este documento compara as diferenças entre as branches `master` e `dev` do projeto Secure AI Studio, destacando as mudanças realizadas para transformar o projeto de uma aplicação de IA offline para uma plataforma de geração de mídia baseada em APIs de IA com foco em segurança corporativa.

## Estrutura de Arquivos

### Branch Master
- Projeto inicial com foco em geração de IA offline
- Estrutura complexa com múltiplos componentes: API, engine, monitoring, pipeline, security, UI
- Arquitetura voltada para processamento local de IA

### Branch Dev
- Estrutura simplificada e modular
- Componentes principais:
  - `app/main.py` - Ponto de entrada da aplicação Flask
  - `app/routes.py` - Rotas da API
  - `app/services/luma_service.py` - Integração com API da Luma AI
  - `app/utils/security.py` - Funções de segurança
  - `app/utils/secure_storage.py` - Armazenamento seguro de arquivos
  - `app/templates/index.html` - Interface web

## Principais Mudanças

### 1. Arquitetura
- **Master**: Arquitetura monolítica complexa com múltiplos módulos
- **Dev**: Arquitetura modular baseada em serviços com padrão MVC

### 2. Tecnologia de Geração
- **Master**: Foco em IA offline com PyTorch e processamento local
- **Dev**: Integração com APIs de IA (Luma AI) para geração de vídeo e imagem

### 3. Segurança
- **Master**: Segurança baseada em isolamento offline
- **Dev**: Segurança multifacetada com:
  - Sanitização de prompts
  - Limitação de taxa (rate limiting)
  - Validação de consentimento (LGPD)
  - Pre-signed URLs para transferência segura
  - Verificação de conformidade de provedores

### 4. Interface
- **Master**: Interface potencialmente baseada em Tkinter
- **Dev**: Interface web completa com HTML/CSS/JavaScript

### 5. Dependências
- **Master**: PyTorch, OpenCV, MoviePy, etc. (bibliotecas locais)
- **Dev**: Flask, requests, python-dotenv, flask-limiter, boto3

## Recursos Implementados na Branch Dev

### 1. Segurança Corporativa
- Verificação de conformidade de provedores (Google Vertex, Adobe Firefly, Luma, etc.)
- Política de retenção zero de dados (ZDR)
- Mecanismo de consentimento para LGPD
- Sanitização de prompts para prevenir injeção

### 2. Funcionalidades de Geração
- Geração de vídeo via API da Luma AI
- Geração de imagem via API da Luma AI
- Sistema de polling para acompanhamento de tarefas
- Visualização e download de conteúdo gerado

### 3. Infraestrutura Segura
- Pre-signed URLs para upload seguro de arquivos
- Validação de tipos e tamanhos de arquivos
- Criptografia em trânsito
- Políticas de ciclo de vida para exclusão automática

## Considerações Finais

A branch `dev` representa uma transformação completa do projeto, passando de uma solução de IA offline para uma plataforma de geração de mídia baseada em APIs de IA com foco em segurança corporativa e conformidade com regulamentações como a LGPD.

A nova arquitetura é mais adequada para ambientes corporativos que necessitam de geração de conteúdo com garantias de segurança e conformidade regulatória.