#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTE DE GERAÇÃO DE IMAGEM OFFLINE
Script para testar a geração de imagens em modo completamente offline
"""

import sys
import os
from pathlib import Path
import time
import socket

# Adicionar o diretório do engine ao path
engine_path = Path(__file__).parent
sys.path.insert(0, str(engine_path))

try:
    # Tentar importar do diretório atual
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core', 'engine'))
    from secure_ai_engine import SecureAIEngine, GenerationRequest
    print("✅ Engine de IA carregado com sucesso")
except ImportError as e:
    print(f"❌ Falha ao carregar engine: {e}")
    print("Tentando importação alternativa...")
    try:
        # Importação direta do arquivo
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "secure_ai_engine", 
            os.path.join(os.path.dirname(__file__), "..", "core", "engine", "secure_ai_engine.py")
        )
        secure_ai_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(secure_ai_module)
        SecureAIEngine = secure_ai_module.SecureAIEngine
        GenerationRequest = secure_ai_module.GenerationRequest
        print("✅ Engine de IA carregado via importação direta")
    except Exception as e2:
        print(f"❌ Falha na importação alternativa: {e2}")
        sys.exit(1)

def check_offline_mode():
    """Verifica se o sistema está realmente offline"""
    print("📡 Verificando modo offline...")
    
    # Teste de conectividade básica
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("⚠️  Conectividade detectada - modo online")
        return False
    except (socket.gaierror, OSError):
        print("✅ Modo offline confirmado - sem conectividade externa")
        return True

def test_image_generation():
    """Testa a geração de imagem em modo offline"""
    print("\n🎨 INICIANDO TESTE DE GERAÇÃO DE IMAGEM")
    print("=" * 50)
    
    # Verificar modo offline
    if not check_offline_mode():
        print("❌ Teste abortado - sistema não está em modo offline")
        return False
    
    try:
        # Inicializar engine
        print("🔧 Inicializando Secure AI Engine...")
        engine = SecureAIEngine("../config/system.conf")
        print("✅ Engine inicializado")
        
        # Criar requisição de teste
        print("\n📝 Criando requisição de geração...")
        request = GenerationRequest(
            content_type="image",
            prompt="Logo corporativo profissional",
            dimensions=(512, 512),
            format="PNG",
            quality="HIGH",
            batch_size=1
        )
        
        print(f"   Prompt: {request.prompt}")
        print(f"   Dimensões: {request.dimensions}")
        print(f"   Formato: {request.format}")
        print(f"   Qualidade: {request.quality}")
        
        # Gerar imagem
        print("\n⚡ Gerando imagem (modo offline)...")
        start_time = time.time()
        
        result = engine.generate_content(request)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Verificar resultado
        if result.success:
            print("✅ GERAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"   Tempo de processamento: {generation_time:.2f} segundos")
            print(f"   Arquivos gerados: {len(result.output_paths)}")
            
            for i, path in enumerate(result.output_paths):
                print(f"   Output {i+1}: {path}")
                
            print(f"\n🔐 Verificação de segurança:")
            print(f"   - Modo air-gap: {'✅' if engine.config.get('AIR_GAP_MODE', False) else '❌'}")
            print(f"   - Sem conexão externa: ✅")
            print(f"   - Proteção de marca: {'✅' if engine.config.get('WATERMARK_ENABLED', False) else '❌'}")
            
            return True
        else:
            print("❌ FALHA NA GERAÇÃO")
            print(f"   Erro: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def main():
    """Função principal do teste"""
    print("🧪 TESTE DE GERAÇÃO DE IMAGEM OFFLINE")
    print("=====================================")
    
    # Informações do sistema
    print(f"Sistema: Secure AI Studio")
    print(f"Diretório: {os.getcwd()}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Executar teste
    success = test_image_generation()
    
    # Resultado final
    print("\n" + "=" * 50)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Geração de imagem offline funcionando corretamente")
    else:
        print("💥 TESTE FALHOU!")
        print("❌ Problemas detectados na geração offline")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)