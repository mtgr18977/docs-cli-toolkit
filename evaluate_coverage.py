"""Avalia a cobertura da documentação usando embeddings e fornece interface CLI."""

import json
import csv
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time
from typing import Callable

try:
    import openai  # type: ignore
except Exception:  # pragma: no cover
    openai = None  # type: ignore
import numpy as np  # Para cálculo de similaridade de cosseno
import re  # Para manipulação de texto e divisão de frases
import argparse  # Adicionado para parsing de argumentos CLI
import sys  # Adicionado para sys.exit

from utils import (
    clean_text_for_embedding,
    generate_embedding_with_retry,
    generate_openai_embedding,
    GEMINI_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Limite de caracteres para o embedding, para evitar exceder o limite de tokens da API
EMBEDDING_TEXT_MAX_LENGTH = 1024

# Funções auxiliares



def cosine_similarity(vecA, vecB):
    """
    Calcula a similaridade de cosseno entre dois vetores.
    """
    # Certifica-se de que os vetores são arrays numpy
    vecA = np.array(vecA)
    vecB = np.array(vecB)

    # Verifica se os vetores não estão vazios
    if vecA.size == 0 or vecB.size == 0:
        return 0.0

    dot_product = np.dot(vecA, vecB)
    norm_A = np.linalg.norm(vecA)
    norm_B = np.linalg.norm(vecB)

    if norm_A == 0 or norm_B == 0:
        return 0.0
    return dot_product / (norm_A * norm_B)

def get_relevant_chunks(query_embedding, processed_chunks, top_k=5):
    """
    Encontra os chunks mais relevantes com base na similaridade de cosseno.
    """
    similarities = []
    for chunk_info in processed_chunks:
        chunk_embedding = chunk_info.get('embedding')
        if chunk_embedding and len(chunk_embedding) > 0 and len(query_embedding) == len(chunk_embedding):
            try:
                similarity = cosine_similarity(query_embedding, chunk_embedding)
                similarities.append({'similarity': similarity, 'chunk': chunk_info})
            except Exception as e:
                print(f"Aviso: Erro ao calcular similaridade para chunk '{chunk_info.get('chunk_title', 'N/A')}' do documento '{chunk_info.get('document_title', 'N/A')}': {e}")
        else:
            pass # Silenciar avisos excessivos para embeddings inválidos/incompatíveis

    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities[:top_k]

# MODIFICADO: Adicionado output_json_path como parâmetro
def evaluate_coverage(
    qa_filepath: str = "qa_data_clean.csv",
    chunks_filepath: str = "processed_chunks_with_embeddings.json",
    top_k_chunks: int = 5,
    output_json_path: str = "evaluation_results.json",
    provider: str | None = None,
    gemini_api_key: str | None = None,
    openai_api_key: str | None = None,
) -> bool:
    """
    Avalia a cobertura da documentação usando um arquivo CSV de perguntas e respostas ideais.
    A avaliação considera a similaridade de frases da resposta ideal com os chunks relevantes.
    Salva os resultados no caminho especificado por output_json_path.
    """
    if not os.path.exists(qa_filepath):
        print(f"Erro: O arquivo de perguntas e respostas '{qa_filepath}' não foi encontrado.")
        return False
    if not os.path.exists(chunks_filepath):
        print(f"Erro: O arquivo de chunks processados '{chunks_filepath}' não foi encontrado. Execute 'generate_embeddings.py' primeiro.")
        return False

    print(f"Carregando chunks de '{chunks_filepath}'...")
    try:
        with open(chunks_filepath, 'r', encoding='utf-8') as f:
            processed_chunks = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON de '{chunks_filepath}': {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao carregar '{chunks_filepath}': {e}")
        return False

    # Filtrar chunks que não têm embedding válido (se houver algum)
    processed_chunks = [c for c in processed_chunks if c.get('embedding') is not None]
    if not processed_chunks:
        print(
            "Erro: Nenhum chunk com embedding válido encontrado após o carregamento. Verifique o arquivo de chunks com embeddings."
        )
        return False

    # Determina o provedor a ser usado
    chosen_provider = (
        provider or ("openai" if (openai_api_key or OPENAI_API_KEY) else "gemini")
    ).lower()
    actual_gemini_key = gemini_api_key or GOOGLE_API_KEY
    actual_openai_key = openai_api_key or OPENAI_API_KEY

    if chosen_provider == "openai":
        if not actual_openai_key:
            raise ValueError("OPENAI_API_KEY nao configurada")
        embed_func: Callable[[str], list | None] = lambda txt: generate_openai_embedding(txt, actual_openai_key)
    else:
        if not actual_gemini_key:
            raise ValueError("GOOGLE_API_KEY nao configurada")
        embed_func = lambda txt: generate_embedding_with_retry(txt, actual_gemini_key, model=GEMINI_EMBEDDING_MODEL)


    print(f"Carregando perguntas e respostas de '{qa_filepath}'...")
    qa_pairs = []
    try:
        with open(qa_filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Adaptação para as colunas do seu CSV: 'question' e 'response'
                if 'question' in row and 'response' in row:
                    qa_pairs.append({'pergunta': row['question'], 'resposta_ideal': row['response']})
                else:
                    print(f"Aviso: Linha ignorada no CSV. Esperava 'question' e 'response': {row}")
    except Exception as e:
        print(f"Erro ao carregar ou ler o arquivo CSV '{qa_filepath}': {e}")
        return False

    if not qa_pairs:
        print("Atenção: Nenhum par de pergunta-resposta válido encontrado no CSV.")
        return False

    evaluation_results = []
    total_questions = len(qa_pairs)
    found_in_top_k_count = 0

    # Limiares para a avaliação de frases
    MIN_SENTENCE_SIMILARITY_THRESHOLD = 0.65  # Similaridade mínima para uma frase ser considerada "coberta"
    MIN_PHRASES_COVERED_PERCENTAGE = 0.70  # % mínima de frases da resposta ideal que devem ser cobertas

    print(f"\nIniciando avaliação de cobertura para {total_questions} perguntas...")
    print(f"Configuração de avaliação: Considerar 'Encontrada' se {MIN_PHRASES_COVERED_PERCENTAGE*100:.0f}% das frases da resposta ideal tiverem similaridade >= {MIN_SENTENCE_SIMILARITY_THRESHOLD:.2f} com os top {top_k_chunks} chunks.")


    for i, qa in enumerate(qa_pairs):
        question = qa['pergunta']
        ideal_answer = qa['resposta_ideal']

        print(f"\n--- Avaliando Pergunta {i + 1}/{total_questions}: '{question[:100]}...' ---") # Mostra o começo da pergunta

        # 1. Gerar embedding da pergunta
        question_clean = clean_text_for_embedding(question)
        if len(question_clean) > EMBEDDING_TEXT_MAX_LENGTH:
            question_clean = question_clean[:EMBEDDING_TEXT_MAX_LENGTH]
        query_embedding = embed_func(question_clean)
        if query_embedding is None:
            print(f"  Falha ao gerar embedding para a pergunta. Pulando.")
            evaluation_results.append({
                "pergunta": question,
                "resposta_ideal": ideal_answer,
                "status": "Falha no Embedding da Pergunta",
                "cobertura_detalhes": [],
                "top_k_chunks_relevantes": []
            })
            continue

        # 2. Encontrar chunks relevantes
        relevant_chunks_with_similarity = get_relevant_chunks(query_embedding, processed_chunks, top_k=top_k_chunks)

        # Preparar detalhes dos chunks relevantes para o relatório
        top_chunks_report = []
        for item in relevant_chunks_with_similarity:
            chunk = item['chunk']
            top_chunks_report.append({
                "document_title": chunk.get('document_title', 'N/A'),
                "chunk_title": chunk.get('chunk_title', 'N/A'),
                "filepath": chunk.get('document_filepath', 'N/A'),
                "similarity_to_query": f"{item['similarity']:.4f}",
                "content_preview": chunk.get('chunk_content', '')[:200] + "..." if len(chunk.get('chunk_content', '')) > 200 else chunk.get('chunk_content', '')
            })

        # 3. Avaliar cobertura da resposta ideal pelas frases
        answer_covered = False
        covered_sentences_count = 0
        coverage_details = []
        coverage_percentage = 0.0 # Inicializa coverage_percentage

        # Divide a resposta ideal em frases e as limpa
        # Usa um regex mais robusto para split de frases, considerando múltiplos delimitadores
        ideal_answer_sentences_raw = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', ideal_answer)
        ideal_answer_sentences = [clean_text_for_embedding(s).strip() for s in ideal_answer_sentences_raw if clean_text_for_embedding(s).strip()]

        if not ideal_answer_sentences:
            print(f"  Aviso: Resposta ideal vazia ou não divisível em frases após limpeza para '{question}'.")
            status = "Resposta Ideal Vazia/Inválida"
        else:
            for ideal_sentence in ideal_answer_sentences:
                sentence_clean = clean_text_for_embedding(ideal_sentence)
                if len(sentence_clean) > EMBEDDING_TEXT_MAX_LENGTH:
                    sentence_clean = sentence_clean[:EMBEDDING_TEXT_MAX_LENGTH]
                sentence_embedding = embed_func(sentence_clean)

                sentence_covered_by_chunk = False
                best_similarity_for_sentence = 0.0
                covered_by_chunk_info = "N/A"

                if sentence_embedding is None:
                    coverage_details.append({
                        "frase_ideal": ideal_sentence,
                        "status": "Falha no Embedding da Frase",
                        "similaridade_max": 0.0,
                        "chunk_correspondente": "N/A"
                    })
                    continue

                for item in relevant_chunks_with_similarity:
                    chunk_content_for_embedding = item['chunk'].get('embedding') # Usa o embedding do chunk diretamente
                    if chunk_content_for_embedding: # Verifica se o embedding do chunk é válido
                        current_similarity = cosine_similarity(sentence_embedding, chunk_content_for_embedding)
                        if current_similarity > best_similarity_for_sentence:
                            best_similarity_for_sentence = current_similarity
                            covered_by_chunk_info = f"Doc: {item['chunk'].get('document_title', 'N/A')} | Sec: {item['chunk'].get('chunk_title', 'N/A')}"

                        if current_similarity >= MIN_SENTENCE_SIMILARITY_THRESHOLD:
                            sentence_covered_by_chunk = True
                            break # Já encontrou um chunk relevante para esta frase

                if sentence_covered_by_chunk:
                    covered_sentences_count += 1

                coverage_details.append({
                    "frase_ideal": ideal_sentence,
                    "status": "Coberta" if sentence_covered_by_chunk else "Não Coberta",
                    "similaridade_max": f"{best_similarity_for_sentence:.4f}",
                    "chunk_correspondente": covered_by_chunk_info
                })

            # Determinar o status geral da cobertura
            total_sentences = len(ideal_answer_sentences)
            if total_sentences > 0:
                coverage_percentage = covered_sentences_count / total_sentences
                if coverage_percentage >= MIN_PHRASES_COVERED_PERCENTAGE:
                    answer_covered = True

            status = "Encontrada (Cobertura Suficiente)" if answer_covered else "Não Encontrada (Cobertura Insuficiente)"
            print(f"  Status: {status}. Frases cobertas: {covered_sentences_count}/{total_sentences} ({coverage_percentage*100:.2f}%)")

        if answer_covered:
            found_in_top_k_count += 1

        evaluation_results.append({
            "pergunta": question,
            "resposta_ideal": ideal_answer,
            "status": status,
            "cobertura_detalhes": coverage_details,
            "top_k_chunks_relevantes": top_chunks_report # Adiciona os chunks mais relevantes para a pergunta
        })

    # Salvar resultados da avaliação
    # MODIFICADO: usa output_json_path
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_results, f, ensure_ascii=False, indent=4)
        print(f"\nResultados da avaliação salvos em '{output_json_path}'.")
    except Exception as e:
        print(f"Erro ao salvar os resultados da avaliação: {e}")
        return False

    print(f"\n--- Resumo da Avaliação ---")
    print(f"Total de perguntas avaliadas: {total_questions}")
    if total_questions > 0:
        print(f"Perguntas consideradas 'Encontradas (Cobertura Suficiente)': {found_in_top_k_count}")
        print(f"Porcentagem de cobertura geral: {(found_in_top_k_count / total_questions * 100):.2f}%")
    else:
        print("Nenhuma pergunta foi avaliada.")


    return True

def cli_main():
    """Ponto de entrada de linha de comando para avaliação de cobertura."""
    parser = argparse.ArgumentParser(description="Avalia a cobertura da documentação usando embeddings.")
    parser.add_argument("qa_filepath", help="Caminho para o arquivo CSV de perguntas e respostas ideais.")
    parser.add_argument("embeddings_filepath", help="Caminho para o arquivo JSON de chunks processados com embeddings.")
    parser.add_argument("-k", "--top_k_chunks", type=int, default=5, help="Número de chunks mais relevantes a considerar (padrão: 5).")
    parser.add_argument("-o", "--output", default="evaluation_results.json", help="Arquivo de saída para os resultados da avaliação (padrão: evaluation_results.json).")
    parser.add_argument(
        "--provider",
        choices=["gemini", "openai"],
        help="Provedor usado para gerar embeddings das perguntas (detectado automaticamente).",
    )
    parser.add_argument("--gemini-api-key", help="Chave da API do Google Gemini (opcional)")
    parser.add_argument("--openai-api-key", help="Chave da API OpenAI (opcional)")
    args = parser.parse_args()

    success = evaluate_coverage(
        qa_filepath=args.qa_filepath,
        chunks_filepath=args.embeddings_filepath,
        top_k_chunks=args.top_k_chunks,
        output_json_path=args.output,
        provider=args.provider,
        gemini_api_key=args.gemini_api_key,
        openai_api_key=args.openai_api_key,
    )
    if not success:
        print("\nA avaliação de cobertura da documentação falhou.")
        sys.exit(1)
    else:
        print("\nA avaliação de cobertura da documentação foi concluída com sucesso.")

if __name__ == "__main__":
    cli_main() # Now it calls the cli_main function