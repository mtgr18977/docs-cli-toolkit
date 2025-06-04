import re
import time
import google.generativeai as genai

# Modelo padrão para geração de embeddings com Gemini
GEMINI_EMBEDDING_MODEL = "models/embedding-001"

# --- Variáveis de controle para Rate Limiting (Gemini) ---
REQUEST_LIMIT_PER_MINUTE_GEMINI = 150
_gemini_request_count = 0
_gemini_last_request_time = time.time()


def clean_text_for_embedding(text):
    """Limpa texto removendo elementos de Markdown e espaços extras."""
    if not isinstance(text, str):
        return ""

    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\*\*|__|\*|_", "", text)
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-+*]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^-{3,}|^\*{3,}|^_{3,}", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\n+", " ", text).strip()
    return text


def generate_embedding_with_retry(text_content, api_key, model=GEMINI_EMBEDDING_MODEL):
    """Gera embedding com Gemini, aplicando retry e rate limiting."""
    global _gemini_request_count, _gemini_last_request_time

    genai.configure(api_key=api_key)

    current_time = time.time()
    elapsed_time = current_time - _gemini_last_request_time

    if elapsed_time < 60 and _gemini_request_count >= REQUEST_LIMIT_PER_MINUTE_GEMINI:
        sleep_duration = 60 - elapsed_time
        print(f"  Atingido limite de requisições por minuto. Aguardando {sleep_duration:.2f} segundos...")
        time.sleep(sleep_duration)
        _gemini_request_count = 0
        _gemini_last_request_time = time.time()
    elif elapsed_time >= 60:
        _gemini_request_count = 0
        _gemini_last_request_time = time.time()

    _gemini_request_count += 1

    retries = 3
    for attempt in range(retries):
        try:
            response = genai.embed_content(model=model, content=text_content)  # type: ignore
            return response["embedding"]
        except Exception as e:
            print(f"Erro ao gerar embedding (tentativa {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None
    return None
