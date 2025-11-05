# 🤖 Bitcoin News Publisher Bot

Este projeto contém o código-fonte para a automação de posts de notícias sobre Bitcoin no WordPress, com um sistema avançado de curadoria de conteúdo, SEO e imagens.

O script foi desenvolvido para ser o *core* de um **Jornalista IA** que pode ser controlado via Telegram.

## ⚙️ Funcionalidades Principais

*   **Busca de Notícias Reais:** Integração com **SerpApi (Google News)** para obter notícias factuais sobre Bitcoin.
*   **Geração de Conteúdo:** Utiliza o LLM para reescrever as notícias em um post coeso, com formatação de blocos (Gutenberg).
*   **Otimização SEO:** Gera **Título Otimizado** e **Meta Descrição** para cada post.
*   **Tags e Categorias:** Cria e atribui tags relevantes e seleciona a categoria **"Bitcoin"** automaticamente.
*   **Curadoria de Imagens:** Sistema avançado de **Pexels + LLM** para:
    *   Extrair palavras-chave do conteúdo.
    *   Buscar múltiplas imagens no Pexels.
    *   Realizar um "match" de relevância para selecionar a melhor **Imagem de Destaque** e imagens para o **Corpo do Post**.
*   **Publicação Automática:** Publica o post diretamente no WordPress via API REST.

## 🚀 Configuração e Instalação

### 1. Clonar o Repositório

```bash
git clone https://github.com/luizphelipes/bitcoin-news-publisher-bot.git
cd bitcoin-news-publisher-bot
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

**Conteúdo de `requirements.txt`:**
```
requests
openai
Pillow
```

### 3. Configurar Credenciais

O arquivo `wp_config.py` contém todas as credenciais necessárias. **É altamente recomendável** que você substitua este arquivo por um sistema de **Variáveis de Ambiente** (ex: `.env` ou variáveis de ambiente do servidor) para maior segurança.

**Credenciais Necessárias:**

| Variável | Descrição |
| :--- | :--- |
| `WP_URL` | URL base do seu WordPress (ex: `https://meublog.com.br/`) |
| `WP_USER` | Usuário com permissão de Administrador/Editor (para API) |
| `WP_APP_PASSWORD` | **Senha de Aplicação** gerada no WordPress |
| `PEXELS_API_KEY` | Chave de API do Pexels (para imagens) |
| `SERPAPI_API_KEY` | Chave de API da SerpApi (para notícias do Google News) |

### 4. Executar o Script

Para testar a automação, execute o script principal:

```bash
python3 bitcoin_news_publisher.py
```

## 🤖 Integração com Bot de Telegram (Jornalista IA)

Para transformar esta automação em um **Jornalista IA** que responde via Telegram, siga estes passos:

### 1. Criar o Bot

1.  Crie um novo bot no Telegram usando o **BotFather** e obtenha o **Token de API do Bot**.
2.  Instale a biblioteca de Telegram (ex: `pip install python-telegram-bot`).

### 2. Estrutura do Bot (Exemplo Simplificado)

Crie um arquivo `telegram_bot.py` que irá escutar os comandos:

```python
import telegram
from telegram.ext import Updater, CommandHandler
import subprocess
import os

# Substitua pelo seu token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# ID do chat para onde as notificações serão enviadas
ADMIN_CHAT_ID = [SEU_CHAT_ID] 

def start(update, context):
    update.message.reply_text('Olá! Eu sou o Jornalista IA de Bitcoin. Use /publicar para gerar um novo post.')

def publicar(update, context):
    update.message.reply_text('Iniciando a publicação de notícias... Isso pode levar alguns minutos.')
    
    try:
        # Executa o script de automação
        result = subprocess.run(
            ['python3', 'bitcoin_news_publisher.py'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # O script imprime o link final na saída padrão
        link = [line for line in result.stdout.split('\n') if 'Processo concluído com sucesso. O novo post está em:' in line][-1].split(': ')[-1]
        
        update.message.reply_text(f'✅ **Post Publicado!**\n\nConfira a notícia mais quente do dia: {link}', parse_mode=telegram.ParseMode.MARKDOWN)
        
    except subprocess.CalledProcessError as e:
        update.message.reply_text(f'❌ **Erro na Publicação!**\n\nDetalhes: {e.stderr}')
    except Exception as e:
        update.message.reply_text(f'❌ **Erro Inesperado!**\n\nDetalhes: {e}')

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("publicar", publicar))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
```

### 3. Agendamento Diário (Cron Job)

Para a publicação diária automática, configure um **Cron Job** no seu servidor para executar o script no horário desejado (ex: 9h da manhã).

```bash
# Edite o crontab
crontab -e

# Adicione a linha (substitua o caminho)
0 9 * * * /usr/bin/python3 /caminho/completo/para/bitcoin-news-publisher-bot/bitcoin_news_publisher.py
```

**Nota:** Para que o Cron Job notifique o Telegram, você precisará modificar o `bitcoin_news_publisher.py` para enviar uma mensagem via API do Telegram após a publicação bem-sucedida.

---
**Este é o código final e a documentação para o seu projeto. Boa sorte com o seu Jornalista IA!**
