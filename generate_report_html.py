# generate_report_html.py

import json
import os
from datetime import datetime
import argparse # Make sure argparse is imported
import sys      # Make sure sys is imported

# ... (keep your generate_html_report function as is) ...
def generate_html_report(evaluation_json_path="evaluation_results.json", output_html_path="coverage_report.html", top_k_chunks=5):
    # ... (your existing code for this function)
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

    html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Cobertura da Documentação - {report_date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 1200px; margin: 20px auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #0056b3; }}
        h1 {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ background-color: #e9f5ff; border-left: 5px solid #0056b3; padding: 15px; margin-bottom: 30px; border-radius: 5px; }}
        .summary p {{ margin: 5px 0; font-size: 1.1em; }}
        .question-item {{ background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; padding: 15px; }}
        .question-item.found {{ border-left: 5px solid #28a745; }}
        .question-item.not-found {{ border-left: 5px solid #dc3545; }}
        .question-item.partial-found {{ border-left: 5px solid #ffc107; }} /* Orange for partial/other */
        .question-item h3 {{ margin-top: 0; color: #0056b3; }}
        .question-item p {{ margin-bottom: 8px; }}
        .question-item strong {{ color: #555; }}
        .details ul {{ list-style-type: none; padding: 0; }}
        .details li {{ margin-bottom: 5px; background-color: #eee; padding: 8px; border-radius: 3px; }}
        .details li.covered {{ background-color: #d4edda; color: #155724; }}
        .details li.not-covered {{ background-color: #f8d7da; color: #721c24; }}
        .chunk-list {{ margin-top: 10px; border-top: 1px dashed #ccc; padding-top: 10px; }}
        .chunk-list h4 {{ margin-bottom: 5px; color: #0056b3; }}
        .chunk-item {{ background-color: #e2f0f7; border: 1px solid #cce5ff; padding: 10px; margin-bottom: 5px; border-radius: 3px; font-size: 0.9em; }}
        .chunk-item strong {{ color: #333; }}
        .collapsible {{ cursor: pointer; padding: 10px; margin-top: 10px; background-color: #007bff; color: white; border: none; text-align: left; border-radius: 4px; width: 100%; font-size: 1em; }}
        .collapsible:hover {{ background-color: #0056b3; }}
        .collapsible.active:after {{ content: "\\2212"; float: right; }} /* Minus sign */
        .collapsible:not(.active):after {{ content: "\\002B"; float: right; }} /* Plus sign */
        .content {{ padding: 0 18px; max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; background-color: #f9f9f9; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Relatório de Cobertura da Documentação</h1>
        <p style="text-align: center; font-size: 0.9em; color: #666;">Gerado em: {report_date}</p>

        <div class="summary">
            <h2>Resumo Geral</h2>
            <p><strong>Total de Perguntas Avaliadas:</strong> {total_questions}</p>
            <p><strong>Perguntas com Cobertura Suficiente:</strong> {found_count}</p>
            <p><strong>Porcentagem de Cobertura Geral:</strong> {coverage_percentage:.2f}%</p>
        </div>

        <h2>Resultados Detalhados por Pergunta</h2>
    """

    for i, item in enumerate(evaluation_results): # Iterate with index for unique IDs
        question_class = ""
        if "Encontrada" in item['status']:
            question_class = "found"
        elif "Não Encontrada" in item['status']:
            question_class = "not-found"
        else:
            question_class = "partial-found"

        html_content += f"""
        <div class="question-item {question_class}">
            <h3>{i+1}. Pergunta: {item['pergunta']}</h3>
            <p><strong>Status:</strong> {item['status']}</p>
            <p><strong>Resposta Ideal:</strong> {item['resposta_ideal']}</p>
            
            <button type="button" class="collapsible">Detalhes da Cobertura e Chunks Relevantes</button>
            <div class="content">
                <div class="details">
                    <h4>Cobertura por Frase da Resposta Ideal:</h4>
                    <ul>
        """
        if item.get('cobertura_detalhes'):
            for detail in item['cobertura_detalhes']:
                detail_class = "covered" if "Coberta" in detail['status'] else "not-covered"
                html_content += f"""
                        <li class="{detail_class}">
                            <strong>Frase:</strong> {detail['frase_ideal']}<br>
                            <strong>Status da Frase:</strong> {detail['status']}<br>
                            <strong>Similaridade Máx. para Frase:</strong> {detail['similaridade_max']}<br>
                            <strong>Chunk Correspondente:</strong> {detail['chunk_correspondente']}
                        </li>
                """
        else:
            html_content += "<li>Nenhum detalhe de cobertura de frase disponível.</li>"

        html_content += f"""
                    </ul>
                </div>
                <div class="chunk-list">
                    <h4>Top {top_k_chunks} Chunks Relevantes para a Pergunta:</h4>
        """ # Removed <ul> here as chunk-item can be a direct child
        if item.get('top_k_chunks_relevantes'):
            for chunk in item['top_k_chunks_relevantes']:
                html_content += f"""
                        <div class="chunk-item">
                            <p><strong>Documento:</strong> {chunk['document_title']}</p>
                            <p><strong>Seção:</strong> {chunk['chunk_title']}</p>
                            <p><strong>Caminho do Arquivo:</strong> <code>{chunk['filepath']}</code></p>
                            <p><strong>Similaridade com a Pergunta:</strong> {chunk['similarity_to_query']}</p>
                            <p><strong>Conteúdo (preview):</strong> <pre><code>{chunk['content_preview']}</code></pre></p>
                        </div>
                """
        else:
            html_content += "<p>Nenhum chunk relevante encontrado.</p>" # Use <p> for consistency

        html_content += f"""
                </div>
            </div>
        </div>
        """

    html_content += """
    </div>
    <script>
        var coll = document.getElementsByClassName("collapsible");
        var i;

        for (i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.maxHeight){
                    content.style.maxHeight = null;
                } else {
                    content.style.maxHeight = content.scrollHeight + "px";
                } 
            });
        }
    </script>
</body>
</html>
    """

    try:
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Relatório HTML gerado com sucesso em '{output_html_path}'.")
        return True
    except Exception as e:
        print(f"Erro ao salvar o relatório HTML: {e}")
        return False

# NEW cli_main function
def cli_main():
    parser = argparse.ArgumentParser(description="Gera relatório HTML da avaliação de cobertura.")
    parser.add_argument("input_file", # Changed from evaluation_json_path to match docs_tc.py call
                        help="Arquivo JSON de entrada com os resultados da avaliação (padrão: evaluation_results.json).")
    parser.add_argument("output_file", # Changed from output_html_path to match docs_tc.py call
                        help="Arquivo HTML de saída para o relatório (padrão: coverage_report.html).")
    parser.add_argument("top_k_chunks", type=int, # Changed from --top_k_chunks for positional
                        help="Valor de top_k_chunks usado na avaliação (para consistência do relatório).")
    args = parser.parse_args()

    success = generate_html_report(
        evaluation_json_path=args.input_file, # Use new arg name
        output_html_path=args.output_file,    # Use new arg name
        top_k_chunks=args.top_k_chunks
    )
    if not success:
        print("A geração do relatório HTML falhou.")
        sys.exit(1)
    else:
        print("Geração do relatório HTML concluída com sucesso.")

if __name__ == "__main__":
    cli_main() # Call the new cli_main