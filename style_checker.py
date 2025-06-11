import json
import os
try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback if dotenv not installed
    def load_dotenv(*_args, **_kwargs):
        return None
import re
import argparse
import sys
from typing import List, Dict, Any

load_dotenv()


from utils import (
    clean_text_for_embedding,
    generate_embedding_with_retry,
    GEMINI_EMBEDDING_MODEL,
)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calcula a similaridade de cosseno entre dois vetores."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def check_style(
    text: str,
    embeddings_path: str = "style_embeddings.json",
    api_key: str | None = None,
    threshold: float = 0.8,
) -> List[Dict[str, Any]]:
    """Analisa o texto e retorna sentenças fora do padrão de estilo."""
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(f"Embeddings file '{embeddings_path}' not found")

    with open(embeddings_path, "r", encoding="utf-8") as f:
        style_data = json.load(f)

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    flagged: List[Dict[str, Any]] = []
    for sentence in sentences:
        clean_sentence = clean_text_for_embedding(sentence)
        embedding = generate_embedding_with_retry(
            clean_sentence, api_key or os.getenv("GOOGLE_API_KEY"), model=GEMINI_EMBEDDING_MODEL
        )
        if embedding is None:
            continue
        best_sim = 0.0
        for item in style_data:
            style_emb = item.get("embedding")
            if style_emb:
                sim = cosine_similarity(embedding, style_emb)
                if sim > best_sim:
                    best_sim = sim
        if best_sim < threshold:
            flagged.append({"sentence": sentence, "similarity": best_sim})
    return flagged


def cli_main() -> None:
    parser = argparse.ArgumentParser(
        description="Verifica conformidade de estilo de um texto usando embeddings."
    )
    parser.add_argument("input_file", help="Arquivo de texto a verificar")
    parser.add_argument(
        "embeddings_file",
        help="Arquivo JSON com embeddings do guia de estilo",
    )
    parser.add_argument(
        "threshold",
        type=float,
        help="Similaridade mínima para considerar frase no padrão",
    )
    parser.add_argument(
        "--api_key",
        help="Chave de API opcional (senão usa GOOGLE_API_KEY do ambiente)",
    )
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        text = f.read()

    issues = check_style(
        text,
        embeddings_path=args.embeddings_file,
        api_key=args.api_key,
        threshold=args.threshold,
    )
    print(json.dumps(issues, ensure_ascii=False, indent=2))
    if issues:
        print("Trechos fora do padrão encontrados.")
    else:
        print("Nenhum problema de estilo encontrado.")


if __name__ == "__main__":
    cli_main()
