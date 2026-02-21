# Secure AI Studio

Uma aplicação segura e escalável para geração de vídeo e imagem utilizando IA Generativa, com foco em conformidade e segurança corporativa.

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
# Chave de API da Luma AI
LUMAAI_API_KEY=sua_chave_aqui

# Chave secreta do Flask
FLASK_SECRET_KEY=chave_secreta_segura_aqui

# Configurações do servidor
PORT=5000
FLASK_ENV=development
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

## 🛡️ Conformidade LGPD

Este sistema processa dados em servidores da Luma AI localizados fora do Brasil. Embora a Luma AI não tenha servidores específicos no Brasil, a plataforma segue diretrizes de proteção de dados e permite o processamento de dados pessoais com base em consentimento e execução de contrato, conforme artigo 7º da LGPD.

A aplicação implementa as seguintes medidas de segurança:
- Sanitização de prompts para prevenir injeção de prompts
- Limitação de taxa (rate limiting) para prevenir abuso
- Validação de entrada de dados
- Separação de credenciais sensíveis

## 🏗️ Arquitetura

O projeto segue uma arquitetura modular baseada no padrão MVC:

- `app/main.py` - Ponto de entrada da aplicação Flask
- `app/routes.py` - Definição das rotas da API
- `app/services/luma_service.py` - Lógica de negócio para integração com a API da Luma AI
- `app/utils/security.py` - Funções de segurança e sanitização
- `app/templates/` - Templates HTML da interface
- `app/static/` - Arquivos estáticos (CSS, JS, imagens)

## 📝 Uso

1. Acesse a interface web no endpoint raiz (`/`)
2. Insira um prompt descritivo do conteúdo que deseja gerar
3. Selecione o tipo de mídia (vídeo ou imagem)
4. Clique em "Gerar Mídia"
5. Acompanhe o progresso da geração
6. Após a conclusão, visualize e faça o download do conteúdo gerado

## 🛠️ Tecnologias Utilizadas

- Python 3.8+
- Flask (framework web)
- Luma AI API (geração de vídeo e imagem)
- Flask-Limiter (controle de taxa)
- python-dotenv (gerenciamento de variáveis de ambiente)
- Requests (cliente HTTP)

---

Desenvolvido com foco em segurança, conformidade e usabilidade corporativa.