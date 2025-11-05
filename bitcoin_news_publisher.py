# -*- coding: utf-8 -*-
import requests
import json
import os
from openai import OpenAI
from io import BytesIO

# Carregar configurações do WordPress
try:
    from wp_config import WP_URL, WP_USER, WP_APP_PASSWORD, PEXELS_API_KEY, COINGECKO_API_KEY, COINMARKETCAP_API_KEY, SERPAPI_API_KEY
except ImportError:
    print("Erro: Arquivo wp_config.py não encontrado. Execute o teste de conexão primeiro.")
    exit(1)

# Configuração da API OpenAI (a chave é carregada automaticamente do ambiente)
client = OpenAI()

def search_bitcoin_news():
    """
    Busca notícias reais sobre Bitcoin usando a SerpApi (Google News).
    """
    print("-> Buscando notícias reais sobre Bitcoin na SerpApi (Google News)...")
    
    SERPAPI_URL = "https://serpapi.com/search"
    
    params = {
        "engine": "google_news",
        "q": "Bitcoin",
        "api_key": SERPAPI_API_KEY,
        "hl": "pt", # Idioma
        "gl": "br", # País
        "num": 5 # Número de resultados
    }
    
    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        articles = data.get('news_results', [])
        
        if not articles:
            print("-> Nenhuma notícia encontrada na SerpApi.")
            return None
            
        # Seleciona as 3 notícias mais relevantes
        top_articles = articles[:3]
        
        news_summary = "Notícias Fatuais do Google News (via SerpApi):\n\n"
        
        for article in top_articles:
            title = article.get('title', 'Sem Título')
            source = article.get('source', {}).get('name', 'Google News')
            summary = article.get('snippet', 'Sem resumo disponível.')
            link = article.get('link', '#')
            
            news_summary += f"**{title}** ({source})\n"
            news_summary += f"Resumo: {summary}\n"
            news_summary += f"Link: {link}\n\n"
            
        print("-> Notícias reais coletadas com sucesso.")
        return news_summary
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar notícias na SerpApi: {e}")
        # Fallback para a simulação do LLM se a API falhar
        print("-> Falha na API. Recorrendo à simulação do LLM...")
        return search_bitcoin_news_llm_fallback()

def search_bitcoin_news_llm_fallback():
    """
    Simula a pesquisa de notícias sobre Bitcoin (Fallback).
    """
    prompt = (
        "Pesquise as 3 notícias mais importantes e recentes sobre Bitcoin. "
        "Para cada notícia, forneça o título, uma fonte (site) e um resumo de 2-3 frases. "
        "Formate a saída como uma lista numerada simples, com o título em negrito e a fonte entre parênteses."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente de pesquisa de notícias financeiras."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        news_summary = response.choices[0].message.content
        print("-> Notícias coletadas com sucesso (simulação).")
        return news_summary
    except Exception as e:
        print(f"Erro ao simular a pesquisa de notícias: {e}")
        return None

def generate_blog_post(news_summary):
    """
    Gera o conteúdo completo do post do blog a partir do resumo das notícias.
    """
    print("-> Gerando conteúdo do post do blog...")
    
    prompt = (
        f"Com base nas seguintes notícias sobre Bitcoin, escreva um post de blog otimizado para SEO em Português. "
        f"O post deve ter um título atraente, uma introdução, uma seção para cada notícia (desenvolvendo o resumo) e uma conclusão com uma chamada para ação (ex: 'Compartilhe sua opinião nos comentários'). "
        f"O post deve ser formatado usando blocos do WordPress (Gutenberg), incluindo os comentários <!-- wp:block -->. Use parágrafos simples para o corpo do texto e parágrafos com 'fontSize':'large' e negrito para os subtítulos, conforme o exemplo fornecido pelo usuário. O tom deve ser informativo e profissional. "
        f"Notícias: \n\n{news_summary}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um redator de conteúdo de blog profissional e especialista em SEO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content
        
        lines = content.split('\n')
        title = ""
        body_lines = []
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith('<!--'):
                title = stripped_line
                body_lines = lines[i+1:]
                break
            elif stripped_line.startswith('<!--'):
                title = "Notícias de Bitcoin do Dia"
                body_lines = lines
                break
        
        body = '\n'.join(body_lines).strip()
        
        if len(title) < 10 or title.startswith('<'):
            title = "Notícias de Bitcoin do Dia"
            body = content.strip()
            
        import re
        title = re.sub(r'<[^>]+>', '', title)
        title = re.sub(r'<!--.*?-->', '', title)
        title = title.strip()
        
        if not title:
            title = "Notícias de Bitcoin do Dia"
            body = content.strip()
            
        print("-> Conteúdo do post gerado com sucesso.")
        return title, body
    except Exception as e:
        print(f"Erro ao gerar o post: {e}")
        return None, None

def generate_seo_elements(title, content):
    """
    Gera Meta Descrição e Título Otimizado usando o LLM.
    """
    print("-> Gerando elementos de SEO...")
    
    prompt = (
        "Com base no título e conteúdo do post, gere uma Meta Descrição de até 160 caracteres e um Título Otimizado para SEO (se o título original puder ser melhorado). "
        "Responda APENAS com um objeto JSON no seguinte formato: "
        "{\"meta_description\": \"[Meta Descrição]\", \"seo_title\": \"[Título Otimizado]\"}"
        f"\n\nTítulo Original: {title}"
        f"\n\nConteúdo (Primeiras 2000 palavras):\n{content[:2000]}..."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um especialista em SEO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        seo_elements = json.loads(response.choices[0].message.content)
        meta_description = seo_elements.get("meta_description", "")
        seo_title = seo_elements.get("seo_title", title)
        
        print(f"   Meta Descrição: {meta_description}")
        print(f"   Título Otimizado: {seo_title}")
        
        return meta_description, seo_title
        
    except Exception as e:
        print(f"Erro ao gerar elementos de SEO: {e}")
        return "", title # Fallback

def extract_keywords(content):
    """
    Extrai as palavras-chave mais relevantes do conteúdo do post usando o LLM.
    """
    print("-> Extraindo palavras-chave para busca de imagens...")
    
    prompt = (
        "Analise o seguinte conteúdo de post de blog sobre Bitcoin. "
        "Identifique as 3 a 5 palavras-chave mais relevantes e específicas para buscar imagens de banco de dados. "
        "Responda APENAS com as palavras-chave separadas por vírgula, sem frases introdutórias ou explicações. "
        "Exemplo: 'Bitcoin, Criptomoeda, Blockchain, Investimento'"
        f"Conteúdo: \n\n{content[:2000]}..." # Limita o conteúdo para o prompt
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um analista de conteúdo e extrator de palavras-chave."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        keywords_string = response.choices[0].message.content.strip()
        keywords = [k.strip() for k in keywords_string.split(',') if k.strip()]
        print(f"-> Palavras-chave extraídas: {keywords}")
        return keywords
    except Exception as e:
        print(f"Erro ao extrair palavras-chave: {e}")
        return ["Bitcoin", "Criptomoeda"] # Fallback

def search_pexels_images(keywords):
    """
    Busca 4 imagens para cada palavra-chave no Pexels e retorna uma lista de URLs.
    """
    print("-> Buscando imagens no Pexels para as palavras-chave...")
    
    PEXELS_URL = "https://api.pexels.com/v1/search"
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    all_image_data = []
    
    for keyword in keywords:
        params = {
            "query": keyword,
            "orientation": "landscape",
            "size": "medium",
            "per_page": 4 # Busca 4 imagens por palavra-chave
        }
        
        try:
            response = requests.get(PEXELS_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for photo in data.get('photos', []):
                all_image_data.append({
                    "keyword": keyword,
                    "url": photo['src']['medium'],
                    "photographer": photo['photographer'],
                    "alt": f"{keyword} - {photo['photographer']}",
                    "id": photo['id']
                })
                
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar imagens para '{keyword}' no Pexels: {e}")
            
    print(f"-> Total de {len(all_image_data)} imagens encontradas.")
    return all_image_data

def download_image(image_data):
    """
    Baixa uma imagem do Pexels e retorna o caminho local.
    """
    print(f"-> Baixando imagem ID {image_data['id']}...")
    
    photo_url = image_data['url']
    photo_name = f"pexels_{image_data['id']}.jpeg"
    file_path = f"/home/ubuntu/{photo_name}"
    
    try:
        image_response = requests.get(photo_url, timeout=10)
        image_response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(image_response.content)
            
        print(f"-> Imagem baixada com sucesso: {file_path}")
        return file_path
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar imagem ID {image_data['id']}: {e}")
        return None

def match_and_select_images(content, image_data):
    """
    Usa o LLM para selecionar a imagem de destaque e as imagens para o corpo do post.
    """
    print("-> Realizando 'match' de relevância das imagens...")
    
    if not image_data:
        return None, []
        
    image_list_for_prompt = "\n".join([
        f"ID: {img['id']}, Palavra-chave: {img['keyword']}, URL: {img['url']}"
        for img in image_data
    ])
    
    prompt = (
        "Você é um curador de conteúdo. Analise o conteúdo do post e a lista de imagens disponíveis. "
        "Seu objetivo é selecionar a melhor imagem para ser a 'Imagem de Destaque' e até 3 imagens adicionais para serem inseridas no 'Corpo do Post'. "
        "A seleção deve ser baseada na relevância visual e temática com o conteúdo. "
        "Responda APENAS com um objeto JSON no seguinte formato: "
        "{\"featured_image_id\": [ID da imagem de destaque], \"body_image_ids\": [lista de IDs das imagens para o corpo do post]} "
        "Se não houver imagem relevante, use 0 para o ID de destaque e uma lista vazia para o corpo."
        f"\n\nConteúdo do Post (Primeiras 2000 palavras):\n{content[:2000]}..."
        f"\n\nImagens Disponíveis:\n{image_list_for_prompt}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um especialista em curadoria de imagens para blogs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        selection = json.loads(response.choices[0].message.content)
        featured_id = selection.get("featured_image_id", 0)
        body_ids = selection.get("body_image_ids", [])
        
        print(f"-> Seleção do LLM: Destaque ID {featured_id}, Corpo IDs {body_ids}")
        
        # Mapeia os IDs selecionados de volta para os dados completos da imagem
        featured_image = next((img for img in image_data if img['id'] == featured_id), None)
        body_images = [img for img in image_data if img['id'] in body_ids]
        
        return featured_image, body_images
        
    except Exception as e:
        print(f"Erro no processo de 'match' de imagens: {e}")
        return None, []

def download_image(image_data):
    """
    Retorna o caminho local da imagem gerada.
    """
    # No novo fluxo, a imagem já foi baixada durante a geração.
    return image_data.get('file_path')

def upload_media(file_path, title):
    """
    Faz o upload da imagem para a biblioteca de mídia do WordPress.
    """
    print("-> Fazendo upload da mídia para o WordPress...")
    
    API_URL = f"{WP_URL}wp-json/wp/v2/media"
    auth = (WP_USER, WP_APP_PASSWORD)
    
    headers = {
        "Content-Disposition": f"attachment; filename={os.path.basename(file_path)}",
        "Content-Type": "image/png"
    }
    
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(API_URL, auth=auth, headers=headers, data=f, timeout=30)
            
        if response.status_code == 201:
            media_info = response.json()
            print(f"-> Upload de mídia bem-sucedido. ID: {media_info.get('id')}")
            return media_info.get('id')
        else:
            print(f"-> Erro ao fazer upload da mídia. Status Code: {response.status_code}")
            try:
                error_details = response.json()
                print(f"Detalhes do Erro: {error_details.get('message', 'N/A')}")
            except json.JSONDecodeError:
                print(f"Resposta de erro: {response.text[:200]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"-> Erro de requisição ao fazer upload da mídia: {e}")
        return None

def insert_body_images(content, body_images, body_media_ids):
    """
    Usa o LLM para inserir as imagens no corpo do post, mantendo a formatação de blocos.
    """
    print("-> Inserindo imagens no corpo do post...")
    
    if not body_images or not body_media_ids:
        print("-> Nenhuma imagem para inserir no corpo do post.")
        return content
        
    # Cria a lista de imagens disponíveis para o LLM
    image_list_for_prompt = "\n".join([
        f"ID da Mídia: {media_id}, Palavra-chave: {img['keyword']}, Alt: {img['alt']}"
        for img, media_id in zip(body_images, body_media_ids)
    ])
    
    prompt = (
        "Você é um editor de conteúdo. Analise o conteúdo do post (que está em blocos do Gutenberg) e as imagens disponíveis. "
        "Insira os blocos de imagem (`<!-- wp:image -->`) no corpo do post nos locais mais relevantes, preferencialmente próximos ao parágrafo que contém a palavra-chave relacionada. "
        "Mantenha a formatação de blocos do Gutenberg existente. "
        "Para cada imagem, use o seguinte formato de bloco de imagem, substituindo o ID e o Alt Text: "
        "<!-- wp:image {\"id\":[ID da Mídia],\"align\":\"center\"} -->\n"
        "<figure class=\"wp-block-image aligncenter\"><img src=\"[URL da Imagem]\" alt=\"[Alt Text]\" class=\"wp-image-[ID da Mídia]\"/></figure>\n"
        "<!-- /wp:image -->\n"
        "Você DEVE retornar o conteúdo COMPLETO do post com os blocos de imagem inseridos."
        f"\n\nImagens Disponíveis:\n{image_list_for_prompt}"
        f"\n\nConteúdo do Post:\n{content}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um editor de blocos do Gutenberg."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        new_content = response.choices[0].message.content.strip()
        print("-> Imagens inseridas no corpo do post.")
        return new_content
        
    except Exception as e:
        print(f"Erro ao inserir imagens no corpo do post: {e}")
        return content

def get_or_create_tag_ids(keywords):
    """
    Verifica se as tags existem e as cria se necessário, retornando uma lista de IDs.
    """
    print("-> Gerenciando Tags...")
    tag_ids = []
    
    for keyword in keywords:
        # 1. Tenta buscar a tag
        TAGS_URL = f"{WP_URL}wp-json/wp/v2/tags?search={keyword}"
        auth = (WP_USER, WP_APP_PASSWORD)
        
        try:
            response = requests.get(TAGS_URL, auth=auth, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data and data[0]['name'].lower() == keyword.lower():
                tag_ids.append(data[0]['id'])
                print(f"   Tag '{keyword}' encontrada (ID: {data[0]['id']}).")
                continue
            
            # 2. Se não existir, cria a tag
            CREATE_TAG_URL = f"{WP_URL}wp-json/wp/v2/tags"
            tag_data = {
                "name": keyword
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(CREATE_TAG_URL, auth=auth, headers=headers, data=json.dumps(tag_data), timeout=5)
            response.raise_for_status()
            new_tag = response.json()
            tag_ids.append(new_tag['id'])
            print(f"   Tag '{keyword}' criada (ID: {new_tag['id']}).")
            
        except requests.exceptions.RequestException as e:
            print(f"   Erro ao gerenciar tag '{keyword}': {e}")
            
    return tag_ids

def get_all_categories():
    """
    Busca todas as categorias existentes no WordPress e retorna um dicionário {nome: id}.
    """
    print("-> Buscando categorias existentes no WordPress...")
    
    CATEGORIES_URL = f"{WP_URL}wp-json/wp/v2/categories"
    
    try:
        response = requests.get(CATEGORIES_URL, timeout=10)
        response.raise_for_status()
        categories_data = response.json()
        
        categories_map = {cat['name']: cat['id'] for cat in categories_data}
        
        print(f"   Categorias encontradas: {list(categories_map.keys())}")
        return categories_map
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar categorias: {e}")
        return {}

def get_category_id(content):
    """
    Força a seleção da categoria 'Bitcoin' para posts de notícias gerais, garantindo a precisão.
    """
    print("-> Selecionando Categoria (Forçada para 'Bitcoin')...")
    
    categories_map = get_all_categories()
    
    # Tenta encontrar o ID da categoria 'Bitcoin'
    bitcoin_id = categories_map.get('Bitcoin')
    
    if bitcoin_id:
        print(f"   Categoria selecionada: Bitcoin (ID: {bitcoin_id})")
        return [bitcoin_id]
    else:
        # Fallback para a categoria 'Sem Categoria' se 'Bitcoin' não existir
        fallback_id = categories_map.get('Sem Categoria', 1)
        print(f"   Categoria 'Bitcoin' não encontrada. Usando fallback: Sem Categoria (ID: {fallback_id})")
        return [fallback_id]

def publish_to_wordpress(title, content, media_id, tag_ids, category_ids):
    """
    Publica o post no WordPress usando a API REST, incluindo o ID da mídia de destaque, Tags e Categorias.
    """
    print("-> Tentando publicar no WordPress com Imagem, Tags e Categoria...")
    
    API_URL = f"{WP_URL}wp-json/wp/v2/posts"
    auth = (WP_USER, WP_APP_PASSWORD)
    
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": category_ids,
        "tags": tag_ids
    }
    
    if media_id > 0:
        post_data["featured_media"] = media_id
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, auth=auth, headers=headers, data=json.dumps(post_data), timeout=15)
        
        if response.status_code == 201:
            print("-> Publicação bem-sucedida!")
            post_info = response.json()
            print(f"Post ID: {post_info.get('id')}")
            print(f"Link: {post_info.get('link')}")
            return post_info.get('link')
        else:
            print(f"-> Erro ao publicar. Status Code: {response.status_code}")
            try:
                error_details = response.json()
                print(f"Detalhes do Erro: {error_details.get('message', 'N/A')}")
            except json.JSONDecodeError:
                print(f"Resposta de erro: {response.text[:200]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"-> Erro de requisição ao publicar: {e}")
        return None

def main():
    # 1. Pesquisar notícias
    news_summary = search_bitcoin_news()
    if not news_summary:
        print("Falha na coleta de notícias. Abortando.")
        return

    # 2. Gerar post
    title, content = generate_blog_post(news_summary)
    if not title or not content:
        print("Falha na geração do conteúdo. Abortando.")
        return

    # 3. Gerar Elementos de SEO
    meta_description, seo_title = generate_seo_elements(title, content)
    
    # 4. Extrair Palavras-chave
    keywords = extract_keywords(content)
    
    # 5. Buscar e Selecionar Imagens
    all_image_data = search_pexels_images(keywords)
    featured_image, body_images = match_and_select_images(content, all_image_data)
    
    # 6. Upload da Imagem de Destaque
    featured_media_id = 0
    if featured_image:
        image_path = download_image(featured_image)
        if image_path:
            featured_media_id = upload_media(image_path, featured_image['alt'])
            if not featured_media_id:
                print("Falha no upload da Imagem de Destaque. Publicando sem imagem.")
    
    # 7. Upload das Imagens do Corpo do Post
    body_media_ids = []
    media_id = 0 # Inicializa media_id para evitar UnboundLocalError
    for img in body_images:
        image_path = download_image(img)
        if image_path:
            media_id = upload_media(image_path, img['alt'])
            if media_id:
                body_media_ids.append(media_id)
                
    # 8. Inserir Meta Descrição no Conteúdo (como bloco de comentário)
    meta_block = f"<!-- wp:html -->\n<!-- SEO Meta Description: {meta_description} -->\n<!-- /wp:html -->\n"
    content = meta_block + content
    
    # 9. Inserir Imagens no Corpo do Post
    content = insert_body_images(content, body_images, body_media_ids)
    
     # 10. Gerenciar Tags e Categorias
    tag_ids = get_or_create_tag_ids(keywords)
    category_ids = get_category_id(content)
    
    # 11. Publicar no WordPress
    # Usa o título otimizado para SEO, se for diferente
    final_title = seo_title if seo_title else title
    post_link = publish_to_wordpress(final_title, content, featured_media_id, tag_ids, category_ids)
    
    if post_link:
        print(f"\nProcesso concluído com sucesso. O novo post está em: {post_link}")
    else:
        print("\nProcesso concluído com falha na publicação.")
    """
    Publica o post no WordPress usando a API REST, incluindo o ID da mídia de destaque.
    """
    print("-> Tentando publicar no WordPress com Imagem de Destaque...")
    
    API_URL = f"{WP_URL}wp-json/wp/v2/posts"
    auth = (WP_USER, WP_APP_PASSWORD)
    
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [1],
    }
    
    if media_id > 0:
        post_data["featured_media"] = media_id
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, auth=auth, headers=headers, data=json.dumps(post_data), timeout=15)
        
        if response.status_code == 201:
            print("-> Publicação bem-sucedida!")
            post_info = response.json()
            print(f"Post ID: {post_info.get('id')}")
            print(f"Link: {post_info.get('link')}")
            return post_info.get('link')
        else:
            print(f"-> Erro ao publicar. Status Code: {response.status_code}")
            try:
                error_details = response.json()
                print(f"Detalhes do Erro: {error_details.get('message', 'N/A')}")
            except json.JSONDecodeError:
                print(f"Resposta de erro: {response.text[:200]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"-> Erro de requisição ao publicar: {e}")
        return None


if __name__ == "__main__":
    main()
