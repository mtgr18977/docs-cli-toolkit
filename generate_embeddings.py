# generate_embeddings.py (Atualizado para lidar com a estrutura e com Rate Limiting e incluir slug)

import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time
import re

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configuração da API do Google Gemini ---
EMBEDDING_MODEL = "models/embedding-001"

# Limite de caracteres para o embedding, para evitar exceder o limite de tokens da API
EMBEDDING_TEXT_MAX_LENGTH = 1024 

# --- Variáveis para controle de Rate Limiting ---
REQUEST_LIMIT_PER_MINUTE = 150
request_count = 0
last_request_time = time.time() # Inicializa com o tempo atual

def configure_api(api_key=None):
    """
    Configura a API do Google Gemini com a chave fornecida ou da variável de ambiente.
    """
    global GOOGLE_API_KEY
    GOOGLE_API_KEY = api_key or os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("A chave da API do Google Gemini não está configurada. Use --api-key ou configure GOOGLE_API_KEY no arquivo .env")
    genai.configure(api_key=GOOGLE_API_KEY) # type: ignore

def clean_text_for_embedding(text):
    """
    Remove caracteres especiais e formatação markdown para texto que será EMBEDDADO.
    Esta função foi aprimorada para lidar com mais casos de Markdown.
    """
    # Remove links markdown (e.g., [texto](link))
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    # Remove bold/italic (**, __, *, _)
    text = re.sub(r'\*\*|__|\*|_', '', text)
    # Remove cabeçalhos (#, ##, ### etc.)
    text = re.sub(r'#+\s*', '', text)
    # Remove blocos de código (``` ou `)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL) # Para blocos multilinhas
    text = re.sub(r'`[^`]*`', '', text) # Para blocos de uma linha
    # Remove blockquotes (>)
    text = re.sub(r'^\s*>\s*', '', text, flags=re.MULTILINE)
    # Remove linhas de lista (- + *)
    text = re.sub(r'^\s*[-+*]\s*', '', text, flags=re.MULTILINE)
    # Remove linhas horizontais (---, ***, ___)
    text = re.sub(r'^-{3,}|^\*{3,}|^__{3,}', '', text, flags=re.MULTILINE)
    # Remove múltiplos espaços e quebras de linha para um único espaço
    text = re.sub(r'\s+', ' ', text).strip() 
    # Substitui múltiplas quebras de linha por um único espaço (se houver alguma que restou)
    text = re.sub(r'\n+', ' ', text).strip() 
    return text

def split_content_into_semantic_chunks(document_content, doc_title, filepath, doc_slug): # MODIFICADO: adicionado doc_slug
    """
    Divide o conteúdo de um único documento Markdown em chunks baseados em cabeçalhos (H2, H3, etc.).
    Ignora seções de metadados se ainda estiverem presentes.
    Inclui o slug do documento em cada chunk.
    """
    chunks = []
    
    # Remove o bloco de metadados se por acaso ainda estiver aqui
    content_without_metadata = re.sub(r'## Metadata_Start.*?## Metadata_End', '', document_content, flags=re.DOTALL).strip()
    
    # Divide por qualquer cabeçalho de nível 2 ou superior (##, ###, etc.)
    sections = re.split(r'(^##+\s*.*$)', content_without_metadata, flags=re.MULTILINE)

    current_chunk_title = doc_title 
    current_chunk_content_lines = []

    for i, part in enumerate(sections):
        if not part.strip(): 
            continue

        if part.startswith("##"): 
            if current_chunk_content_lines:
                chunks.append({
                    "document_title": doc_title,
                    "document_filepath": filepath,
                    "document_slug": doc_slug, # MODIFICADO: adicionado slug
                    "chunk_title": current_chunk_title.strip(),
                    "chunk_content": "\n".join(current_chunk_content_lines).strip()
                })
                current_chunk_content_lines = [] 
            
            current_chunk_title = part.strip().lstrip('# ').strip() 
        else: 
            current_chunk_content_lines.append(part.strip())

    if current_chunk_content_lines:
        chunks.append({
            "document_title": doc_title,
            "document_filepath": filepath,
            "document_slug": doc_slug, # MODIFICADO: adicionado slug
            "chunk_title": current_chunk_title.strip(),
            "chunk_content": "\n".join(current_chunk_content_lines).strip()
        })
    
    if not chunks and content_without_metadata.strip():
        chunks.append({
            "document_title": doc_title,
            "document_filepath": filepath,
            "document_slug": doc_slug, # MODIFICADO: adicionado slug
            "chunk_title": doc_title, # Usa o título do documento se não houver seções
            "chunk_content": content_without_metadata.strip()
        })
    
    return [chunk for chunk in chunks if chunk['chunk_content'].strip()]


def generate_embedding_with_retry(text_content):
    """
    Gera um embedding para o conteúdo de texto, com mecanismo de retry e rate limiting.
    """
    global request_count, last_request_time

    current_time = time.time()
    elapsed_time = current_time - last_request_time

    if elapsed_time < 60 and request_count >= REQUEST_LIMIT_PER_MINUTE:
        sleep_duration = 60 - elapsed_time
        print(f"  Atingido limite de requisições por minuto. Aguardando {sleep_duration:.2f} segundos...")
        time.sleep(sleep_duration)
        request_count = 0
        last_request_time = time.time()
    elif elapsed_time >= 60: 
        request_count = 0
        last_request_time = time.time()
    
    request_count += 1
    
    retries = 3
    for attempt in range(retries):
        try:
            response = genai.embed_content(model=EMBEDDING_MODEL, content=[text_content]) # type: ignore
            return response['embedding'][0] 
        except Exception as e:
            print(f"Erro ao gerar embedding (tentativa {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt) 
            else:
                return None 
    return None

def generate_embeddings_for_docs(input_json_path="raw_docs.json", output_json_path="embeddings.json", api_key=None):
    """
    Lê o JSON com dados de documentos (já separados), divide cada um em chunks,
    gera embeddings para cada chunk, e salva o resultado final em um novo JSON.
    """
    # Configura a API com a chave fornecida
    configure_api(api_key)

    if not os.path.exists(input_json_path):
        print(f"Erro: O arquivo '{input_json_path}' não foi encontrado. Por favor, execute o script de extração (ex: 'extract_consolidated_md_to_raw_json.py') primeiro.")
        return False

    print(f"Gerando embeddings para documentos de '{input_json_path}'...")

    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            raw_docs = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON de '{input_json_path}': {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao carregar '{input_json_path}': {e}")
        return False

    all_processed_chunks = [] 
    total_raw_docs = len(raw_docs)
    
    for i, doc_data in enumerate(raw_docs):
        doc_title = doc_data.get("title", "Título Desconhecido")
        doc_content_full = doc_data.get("content", "") 
        file_path_relative = doc_data.get("filepath", "N/A")
        doc_slug = doc_data.get("slug", "") # MODIFICADO: Obtém o slug

        print(f"\n--- Processando documento {i + 1}/{total_raw_docs}: '{doc_title}' ({file_path_relative}) ---")
        
        # MODIFICADO: Passa o doc_slug para a função de chunking
        chunks_for_doc = split_content_into_semantic_chunks(doc_content_full, doc_title, file_path_relative, doc_slug) 
        
        if not chunks_for_doc:
            print(f"Atenção: Nenhum chunk válido gerado para o documento '{doc_title}'. Pulando.")
            continue 

        for chunk_idx, chunk in enumerate(chunks_for_doc):
            embedding_text_raw = f"Documento: {chunk['document_title']}. Seção: {chunk['chunk_title']}. Conteúdo: {chunk['chunk_content']}"
            embedding_text = clean_text_for_embedding(embedding_text_raw)
            
            if len(embedding_text) > EMBEDDING_TEXT_MAX_LENGTH:
                embedding_text = embedding_text[:EMBEDDING_TEXT_MAX_LENGTH]
                print(f"  Truncando chunk {chunk_idx+1} de '{chunk['chunk_title']}' para {EMBEDDING_TEXT_MAX_LENGTH} caracteres para embedding.")
            
            if not embedding_text.strip():
                print(f"  Atenção: Texto limpo para embedding vazio para chunk '{chunk['chunk_title']}' do documento '{doc_title}'. Pulando embedding.")
                chunk["embedding"] = None
                all_processed_chunks.append(chunk)
                continue

            print(f"  Gerando embedding para chunk {chunk_idx+1} de '{chunk['chunk_title']}'...")
            chunk_embedding = generate_embedding_with_retry(embedding_text)

            if chunk_embedding is not None:
                chunk["embedding"] = chunk_embedding
                all_processed_chunks.append(chunk)
            else:
                print(f"  Atenção: Falha ao gerar embedding para chunk '{chunk['chunk_title']}' do documento '{doc_title}'. Chunk será incluído sem embedding.")
                chunk["embedding"] = None
                all_processed_chunks.append(chunk)

    if not all_processed_chunks:
        print("Nenhum chunk processado com sucesso (sem embeddings ou dados de entrada).")
        return False

    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_processed_chunks, f, ensure_ascii=False, indent=4)
        print(f"\nGeração de embeddings concluída. Salvou {len(all_processed_chunks)} chunks com embeddings em '{output_json_path}'.")
        return True
    except Exception as e:
        print(f"Erro ao salvar o arquivo JSON: {e}")
        return False

def cli_main():
    import argparse
    parser = argparse.ArgumentParser(description="Gera embeddings para documentos a partir de um JSON.")
    parser.add_argument("input_json_path", help="Caminho para o arquivo JSON de entrada (ex: raw_docs.json).")
    parser.add_argument("output_json_path", help="Caminho para o arquivo JSON de saída dos embeddings (ex: embeddings.json).")
    parser.add_argument("--api-key", help="Chave da API do Google Gemini (opcional, pode ser fornecida via GOOGLE_API_KEY no .env)")
    args = parser.parse_args()
    success = generate_embeddings_for_docs(args.input_json_path, args.output_json_path, args.api_key)
    if not success:
        print("A geração de embeddings falhou.")
        sys.exit(1) # Garante que sys está importado se for usar aqui
    else:
        print("Geração de embeddings concluída com sucesso.")

if __name__ == "__main__":
    import sys # Adicionado aqui para garantir que está disponível para cli_main
    cli_main()