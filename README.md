# Secure AI Studio

Uma aplicação segura e escalável para geração de vídeo e imagem utilizando IA Generativa via Replicate API, com foco em conformidade e segurança corporativa.

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- Pip (gerenciador de pacotes Python)

### Passos para Instalação

1. Clone o repositório:
```bash
git clone <repositorio>
cd secure-ai-studio
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
   - No Windows:
     ```bash
     venv\Scripts\activate
     ```
   - No Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🔐 Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com base no arquivo `.env.example`:

```env
# Token de API da Replicate
REPLICATE_API_TOKEN=seu_token_aqui

# Chave secreta do Flask
FLASK_SECRET_KEY=chave_secreta_segura_aqui

# Configurações do servidor
PORT=5000
FLASK_ENV=development

# Política de retenção de dados (Recurso de Segurança)
DATA_RETENTION_POLICY=ZERO

# Configuração da AWS para Armazenamento Seguro (Opcional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET_NAME=secure-ai-studio-temp
AWS_REGION=us-east-1
```

> ⚠️ **Importante**: Nunca commite o arquivo `.env` com credenciais reais.

## ▶️ Como Rodar

1. Certifique-se de ter ativado o ambiente virtual e configurado as variáveis de ambiente.

2. Execute a aplicação:
```bash
python app/main.py
```

3. Acesse a aplicação no navegador:
```
http://localhost:5000
```

## 🛡️ Conformidade LGPD e Segurança de Dados

Este sistema implementa um plano de segurança em múltiplos níveis para proteger dados sensíveis, especialmente fotos e vídeos pessoais, conforme detalhado no plano de segurança:

### Nível 1: Escolha Estratégica do Provedor
- Implementa verificação de conformidade do provedor (Replicate com Wan Video, Google Veo)
- Prioriza provedores com políticas de retenção de dados claras (ZDR - Zero Data Retention)
- Fornece informações sobre níveis de risco de diferentes provedores
- Garante que os dados sejam processados via API Replicate (EUA) com consentimento explícito

### Nível 2: Configurações de Conta e Contratuais
- Validação de política de retenção de dados (ZDR - Zero Data Retention)
- Opção de opt-out de treinamento de modelos com dados do usuário
- Verificação de conformidade com termos de serviço
- Sistema de controle de orçamento com limite de $5.00

### Nível 3: Arquitetura de Transferência Segura
- Implementação de "pre-signed URLs" para transferência segura de arquivos
- Validação de tipos de arquivo e tamanho máximo
- Criptografia em trânsito (TLS 1.2+)
- Política de ciclo de vida para exclusão automática de arquivos

### Nível 4: Opções de Infraestrutura
- Modo nuvem para alta qualidade e velocidade
- Modo local (planejado) para privacidade máxima usando modelos open-source

A aplicação implementa as seguintes medidas de segurança:
- Sanitização de prompts para prevenir injeção de prompts
- Limitação de taxa (rate limiting) para prevenir abuso
- Validação de entrada de dados
- Separação de credenciais sensíveis
- Mecanismo de consentimento explícito (LGPD)
- Validação de URLs e formatos de arquivos
- Controle rigoroso de orçamento com alertas e bloqueios automáticos

## 💰 Controle de Orçamento e Seleção de Modelos

O sistema implementa um controle de orçamento rigoroso com:

- **Limite Total:** $5.00 de crédito
- **Limite de Alerta:** 92% do orçamento ($4.60) - aviso quando se aproxima do limite
- **Limite de Bloqueio:** 99% do orçamento ($4.95) - bloqueia novas gerações automaticamente
- **Seleção de Modelos:**
  - **Wan Video (padrão, econômico):** $0.02 por geração
    - `wan-video/wan-2.2-t2v-fast` - texto para vídeo
    - `wan-video/wan-2.2-i2v-fast` - imagem para vídeo
  - **Google Veo (premium):** $0.10 por geração
    - `google/veo-3-fast` - qualidade cinematográfica
  - **Modelos de Imagem:**
    - `stability-ai/sdxl` - $0.01 por geração
    - `playgroundai/playground-v2.5-1024px-aesthetic` - $0.015 por geração

### Endpoints de Orçamento:
- `GET /api/budget-status` - Verifica o status atual do orçamento
- `POST /api/reset-budget` - Reseta o orçamento (somente em modo de teste)

## ▶️ Como Rodar

1. Certifique-se de ter ativado o ambiente virtual e configurado as variáveis de ambiente.

2. Execute a aplicação:
```bash
python app/main.py
```

3. Acesse a aplicação no navegador:
```
http://localhost:5000
```

## 🏗️ Arquitetura

O projeto segue uma arquitetura modular baseada no padrão MVC:

- `app/main.py` - Ponto de entrada da aplicação Flask
- `app/routes.py` - Definição das rotas da API
- `app/services/ai_service.py` - Lógica de negócio para integração com a API da Replicate (Wan Video e Google Veo)
- `app/utils/security.py` - Funções de segurança e sanitização
- `app/utils/secure_storage.py` - Gerenciamento seguro de arquivos com pre-signed URLs
- `app/templates/` - Templates HTML da interface
- `app/static/` - Arquivos estáticos (CSS, JS, imagens)

## 📝 Uso

1. Acesse a interface web no endpoint raiz (`/`)
2. Insira um prompt descritivo do conteúdo que deseja gerar
3. Selecione o tipo de mídia (vídeo ou imagem)
4. Marque a caixa de consentimento para processamento de dados
5. Clique em "Gerar Mídia"
6. Acompanhe o progresso da geração
7. Após a conclusão, visualize e faça o download do conteúdo gerado

## 🛠️ Tecnologias Utilizadas

- Python 3.8+
- Flask (framework web)
- Replicate API Client (geração de vídeo e imagem com Wan Video e Google Veo)
- Flask-Limiter (controle de taxa)
- python-dotenv (gerenciamento de variáveis de ambiente)
- Requests (cliente HTTP)
- Boto3 (integração com AWS S3 para armazenamento seguro)
- HTML/CSS/JavaScript (interface web)

## 🧪 Testes e Qualidade (QA / CI/CD)

O projeto conta com uma arquiterura SDET robusta baseada em testes contínuos automatizados.

### Status de Qualidade (Avaliação SDET Lead)
- **Cobertura de Código (Coverage)**: >85% confirmados.
- **Isolamento de Custos**: Interações com o provedor de IA Replicate são virtualizadas localmente (via `pytest-mock`), evitando custos financeiros desnecessários de $5 na validação de Pull Requests.
- **Automação de CI/CD**: Uma pipeline do GitHub Actions valida automaticamente a funcionalidade de core, persistência de budget e segurança anti-injeção a cada Pull Request.
- **Status do Projeto**: **100% (Fase 3 Finalizada)**, validado para adoção `Production-Ready` ou merge imediato na `main`.

### Executar Testes

Para executar todos os testes automatizados ou checar a saúde geral:
```bash
python run_all_tests.py
# ou alternativamente:
python verify_functionality.py
```

Para executar testes específicos:
```bash
python -m pytest tests/test_ai_service.py -v
python -m pytest tests/test_budget_service.py -v
python -m pytest tests/test_api_endpoints.py -v
```

### Endpoints de Monitoramento

- `GET /api/budget-status` - Status atual do orçamento
- `GET /api/status/{task_id}` - Status de uma tarefa específica
- `GET /` - Interface web principal

### Cenários de Erro Comuns

1. **Erro 402 (Payment Required)** - Orçamento excedido
2. **Erro 400 (Bad Request)** - Dados inváldos ou consentimento faltando
3. **Erro 429 (Too Many Requests)** - Limite de taxa atingido

---

Desenvolvido com foco em segurança, conformidade corporativa e resiliência contínua via CI/CD.