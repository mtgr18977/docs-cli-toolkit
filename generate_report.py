# generate_md_report.py

import json
import os
from datetime import datetime

def generate_md_report(evaluation_json_path="evaluation_results.json", output_md_path="coverage_report.md", top_k_chunks=5):
    """
    Gera um relatório Markdown a partir do JSON de avaliação.
    """
    if not os.path.exists(evaluation_json_path):
        print(f"Erro: O arquivo JSON de avaliação '{evaluation_json_path}' não foi encontrado. Execute 'evaluate_coverage.py' primeiro.")
        return False

    print(f"Lendo dados de avaliação de '{evaluation_json_path}'...")
    try:
        with open(evaluation_json_path, 'r', encoding='utf-8') as f:
            evaluation_results = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON de '{evaluation_json_path}': {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao carregar '{evaluation_json_path}': {e}")
        return False

    if not evaluation_results:
        print("Atenção: Nenhum resultado de avaliação válido encontrado no JSON.")
        return False

    # Calcular resumo
    total_questions = len(evaluation_results)
    found_count = sum(1 for item in evaluation_results if "Encontrada" in item['status'])
    coverage_percentage = (found_count / total_questions * 100) if total_questions > 0 else 0

    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md_content = f"""# Relatório de Cobertura da Documentação

**Gerado em:** {report_date}

---

## Resumo Geral

* **Total de Perguntas Avaliadas:** {total_questions}
* **Perguntas com Cobertura Suficiente:** {found_count}
* **Porcentagem de Cobertura Geral:** {coverage_percentage:.2f}%

---

## Resultados Detalhados por Pergunta

"""

    for i, item in enumerate(evaluation_results):
        md_content += f"""
### {i + 1}. Pergunta: {item['pergunta']}

* **Status:** {item['status']}
* **Resposta Ideal:** {item['resposta_ideal']}

"""
        # Detalhes da Cobertura por Frase
        if item.get('cobertura_detalhes'):
            md_content += f"#### Cobertura por Frase da Resposta Ideal:\n\n"
            for detail in item['cobertura_detalhes']:
                status_icon = "✅" if "Coberta" in detail['status'] else "❌"
                md_content += f"""* **{status_icon} Frase:** {detail['frase_ideal']}
    * **Status da Frase:** {detail['status']}
    * **Similaridade Máx. para Frase:** {detail['similaridade_max']}
    * **Chunk Correspondente:** {detail['chunk_correspondente']}
"""
            md_content += "\n" # Adiciona uma linha em branco para espaçamento

        # Top K Chunks Relevantes
        md_content += f"#### Top {top_k_chunks} Chunks Relevantes para a Pergunta:\n\n"
        if item.get('top_k_chunks_relevantes'):
            for chunk in item['top_k_chunks_relevantes']:
                md_content += f"""* **Documento:** {chunk['document_title']}
    * **Seção:** {chunk['chunk_title']}
    * **Caminho do Arquivo:** `{chunk['filepath']}`
    * **Similaridade com a Pergunta:** {chunk['similarity_to_query']}
    * **Conteúdo (preview):** `{chunk['content_preview'].replace('`', '\\`')}`
"""
            md_content += "\n" # Adiciona uma linha em branco para espaçamento
        else:
            md_content += "* Nenhum chunk relevante encontrado.\n\n"
    
    try:
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"Relatório Markdown gerado com sucesso em '{output_md_path}'.")
        return True
    except Exception as e:
        print(f"Erro ao salvar o relatório Markdown: {e}")
        return False

if __name__ == "__main__":
    import argparse # Adicione
    import sys      # Adicione

    parser = argparse.ArgumentParser(description="Gera relatório Markdown da avaliação de cobertura.")
    # Tornando-os posicionais para simplificar a chamada via subprocesso
    parser.add_argument("evaluation_json_path", help="Caminho para o arquivo JSON de resultados da avaliação.")
    parser.add_argument("output_md_path", help="Caminho para salvar o relatório Markdown.")
    parser.add_argument("top_k_chunks", type=int, help="Valor de top_k_chunks usado na avaliação.")
    args = parser.parse_args()

    success = generate_md_report(
        evaluation_json_path=args.evaluation_json_path,
        output_md_path=args.output_md_path,
        top_k_chunks=args.top_k_chunks
    )
    if not success:
        print("A geração do relatório Markdown falhou.")
        sys.exit(1)
    else:
        print("Geração do relatório Markdown concluída com sucesso.")