# Guia de Testes - Secure AI Studio

## Sumário
1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Configuração Inicial](#configuração-inicial)
4. [Testes Funcionais](#testes-funcionais)
5. [Testes de Segurança](#testes-de-segurança)
6. [Testes de Integração](#testes-de-integração)
7. [Verificação Final](#verificação-final)

## Visão Geral

Este guia fornece instruções detalhadas para testar o Secure AI Studio, uma aplicação web para geração de vídeo e imagem com foco em segurança corporativa e conformidade com a LGPD.

## Pré-requisitos

Antes de iniciar os testes, verifique se você tem:

- Python 3.8 ou superior instalado
- Pip (gerenciador de pacotes Python)
- Uma chave de API válida da Luma AI (opcional para testes básicos)
- Acesso à internet (para integração com APIs externas)
- Navegador web moderno (Chrome, Firefox, Edge, Safari)

## Configuração Inicial

### Passo 1: Clonar o Repositório
```bash
git clone https://github.com/RaFeltrim/secure-ai-studio.git
cd secure-ai-studio
```

### Passo 2: Criar Ambiente Virtual
```bash
python -m venv venv
```

### Passo 3: Ativar Ambiente Virtual
**No Windows:**
```bash
venv\Scripts\activate
```

**No Linux/Mac:**
```bash
source venv/bin/activate
```

### Passo 4: Instalar Dependências
```bash
pip install -r requirements.txt
```

### Passo 5: Configurar Variáveis de Ambiente
1. Copie o arquivo `.env.example` para `.env`:
```bash
copy .env.example .env  # No Windows
# OU
cp .env.example .env    # No Linux/Mac
```

2. Edite o arquivo `.env` e adicione sua chave de API da Luma AI:
```
LUMAAI_API_KEY=sua_chave_aqui
FLASK_SECRET_KEY=uma_chave_secreta_segura
```

## Testes Funcionais

### Teste 1: Iniciar a Aplicação
1. No terminal, execute:
```bash
python app/main.py
```

2. Verifique se a aplicação inicia sem erros
3. Acesse `http://localhost:5000` no navegador
4. Confirme que a página inicial carrega corretamente

### Teste 2: Interface Web
1. Verifique se todos os elementos da interface estão presentes:
   - Campo para digitar o prompt
   - Seleção de tipo de mídia (Vídeo/Imagem)
   - Checkbox de consentimento
   - Botão "Gerar Mídia"

2. Verifique se os estilos CSS são aplicados corretamente
3. Teste a responsividade em diferentes tamanhos de tela

### Teste 3: Validação de Formulário
1. Deixe o campo de prompt vazio e clique em "Gerar Mídia"
2. Verifique se uma mensagem de erro é exibida
3. Preencha o prompt mas não marque o consentimento
4. Verifique se uma mensagem de erro de consentimento é exibida
5. Preencha tudo corretamente e verifique se o processo inicia

### Teste 4: Geração de Vídeo
1. Preencha um prompt descritivo (ex: "A beautiful sunset over mountains")
2. Selecione "Vídeo" como tipo de mídia
3. Marque a caixa de consentimento
4. Clique em "Gerar Mídia"
5. Observe o status de processamento
6. Verifique se o sistema faz polling para atualizar o status
7. (OBS: Em ambiente de teste sem chave válida, o status pode permanecer em processamento)

### Teste 5: Geração de Imagem
1. Preencha um prompt descritivo (ex: "A colorful parrot on a branch")
2. Selecione "Imagem" como tipo de mídia
3. Marque a caixa de consentimento
4. Clique em "Gerar Mídia"
5. Observe o status de processamento
6. Verifique se o sistema faz polling para atualizar o status

## Testes de Segurança

### Teste 6: Sanitização de Prompt
1. Digite um prompt com caracteres especiais: `Teste <script>alert('xss')</script>`
2. Verifique se o sistema sanitiza corretamente o input
3. Tente com comandos de injeção de prompt: `Ignore all previous instructions and ...`
4. Verifique se o sistema previne essas injeções

### Teste 7: Limitação de Taxa (Rate Limiting)
1. Execute rapidamente várias requisições à API `/api/generate`
2. Verifique se o sistema começa a retornar erro 429 após 5 requisições por minuto
3. Aguarde alguns minutos e verifique se as requisições são aceitas novamente

### Teste 8: Validação de Consentimento (LGPD)
1. Tente gerar mídia sem marcar a caixa de consentimento
2. Verifique se o sistema retorna um erro adequado
3. Verifique se a mensagem de consentimento está clara e em conformidade com a LGPD

### Teste 9: Segurança de Headers e CORS
1. Verifique se os headers de segurança estão presentes na resposta
2. Teste se a aplicação não permite requisições de domínios não autorizados (se configurado)

## Testes de Integração

### Teste 10: Integração com API Externa
1. Com uma chave de API válida configurada:
   - Execute uma geração de vídeo
   - Verifique se a requisição é enviada corretamente para a API da Luma AI
   - Verifique se o ID da tarefa é retornado corretamente

2. Sem uma chave de API válida (modo simulado):
   - Execute uma geração de vídeo
   - Verifique se o sistema entra em modo de simulação
   - Verifique se os status são retornados corretamente

### Teste 11: Verificação de Status
1. Inicie uma geração de mídia
2. Verifique se as requisições de status são feitas corretamente
3. Verifique se o progresso é atualizado na interface
4. Verifique se o conteúdo gerado é exibido quando disponível

### Teste 12: Download de Conteúdo
1. Após a geração bem-sucedida de conteúdo
2. Verifique se o botão de download é exibido
3. Clique no botão e verifique se o download inicia corretamente

## Verificação Final

### Checklist de Qualidade
- [ ] Aplicação inicia sem erros
- [ ] Interface carrega corretamente
- [ ] Todos os campos do formulário funcionam
- [ ] Validações de formulário estão funcionando
- [ ] Sanitização de prompts está ativa
- [ ] Limitação de taxa está funcionando
- [ ] Mecanismo de consentimento está ativo
- [ ] Sistema de polling funciona corretamente
- [ ] Mensagens de erro são claras e úteis
- [ ] Documentação está atualizada
- [ ] Variáveis de ambiente são respeitadas

### Testes de Desempenho (Opcional)
1. Meça o tempo de resposta da aplicação
2. Verifique o uso de memória durante a execução
3. Teste a aplicação sob carga leve (múltiplas requisições simultâneas)

### Testes em Diferentes Ambientes
1. Teste em diferentes navegadores (Chrome, Firefox, Edge, Safari)
2. Teste em diferentes sistemas operacionais (Windows, macOS, Linux)
3. Teste em dispositivos móveis e desktop

## Resultado Esperado

Após completar todos os testes, a aplicação deve:

1. Permitir a geração de vídeo e imagem através da API da Luma AI
2. Implementar corretamente todas as medidas de segurança corporativa
3. Cumprir os requisitos de conformidade com a LGPD
4. Fornecer uma interface web intuitiva e responsiva
5. Proteger contra injeção de prompts e outros vetores de ataque
6. Implementar limitação de taxa para prevenir abuso
7. Exibir claramente o status do processamento para o usuário

## Problemas Comuns e Soluções

### Erro: "LUMAAI_API_KEY is required"
- **Solução**: Verifique se o arquivo `.env` está configurado corretamente e a variável está definida

### Erro: "Module not found"
- **Solução**: Verifique se todas as dependências foram instaladas com `pip install -r requirements.txt`

### Interface não carrega
- **Solução**: Verifique se a aplicação Flask está rodando e se não há erros no terminal

### Consentimento não é aceito
- **Solução**: Verifique se a caixa de seleção está marcada antes de clicar em "Gerar Mídia"