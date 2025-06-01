#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path

# Nomes de arquivo padrão intermediários e finais
DEFAULT_CORPUS_CONSOLIDATED = "corpus_consolidated.md"
DEFAULT_RAW_DOCS = "raw_docs.json"
DEFAULT_EMBEDDINGS = "embeddings.json" # Conforme sua solicitação
DEFAULT_EVAL_RESULTS = "evaluation_results.json"
DEFAULT_QA_PROCESSED = "gartner_filtrado_processed.csv" # Saída do limpa_csv e entrada do evaluate
DEFAULT_MD_REPORT = "coverage_report.md"
DEFAULT_HTML_REPORT = "coverage_report.html"

# Configuração da API
CONFIG_DIR = Path.home() / ".docs-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

def ensure_config_dir():
    """Garante que o diretório de configuração existe."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    """Carrega a configuração do arquivo config.json."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_config(config):
    """Salva a configuração no arquivo config.json."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def run_script(command_args):
    """Executa um script (entry point) como um subprocesso."""
    # Espera que command_args[0] seja um executável no PATH (ex: 'docs-tc-extract-data')
    command = command_args
    print(f"🚀 Executando: {' '.join(command)}")
    try:
        process = subprocess.run(command, capture_output=True, text=True, encoding=sys.stdout.encoding or 'latin-1', errors='replace')

        if process.stdout:
            print("Output:\n", process.stdout)
        if process.stderr:
            print("Errors:\n", process.stderr, file=sys.stderr)

        if process.returncode != 0:
            print(f"❌ Erro ao executar {' '.join(command)}. Código de saída: {process.returncode}", file=sys.stderr)
            return None # Indica falha para as funções run_step_or_exit

        print(f"✅ Script {' '.join(command_args)} concluído com sucesso.")
        return process

    except FileNotFoundError:
        print(f"🚨 Erro: Comando '{command[0]}' não encontrado. Verifique se o docs-cli está instalado corretamente e se os scripts dos subcomandos (ex: {command[0]}.exe) foram criados na pasta Scripts do seu ambiente virtual e se o ambiente virtual está ativo.", file=sys.stderr)
        sys.exit(1) # Falha crítica se o comando do script não for encontrado
    except Exception as e:
        print(f"🚨 Exceção ao executar o subprocesso {' '.join(command)}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Docs Toolkit CLI - Orquestrador de scripts de processamento de documentação.")
    
    # Adiciona argumento global para a chave da API
    parser.add_argument("--api", help="Chave da API do Google Gemini (opcional, pode ser fornecida via GOOGLE_API_KEY no .env)")
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis", required=True)

    # --- Subparser para configuração da API ---
    parser_api = subparsers.add_parser("api", help="Configura a chave da API do Google Gemini.")
    parser_api.add_argument("api_key", help="Chave da API do Google Gemini para ser salva globalmente.")
    parser_api.add_argument("--show", action="store_true", help="Mostra a chave da API atual (parcialmente mascarada).")

    # --- Subparser para merge_markdown.py ---
    parser_merge = subparsers.add_parser("merge", help="Consolida arquivos Markdown de um diretório.")
    parser_merge.add_argument("input_dir", help="Diretório de entrada contendo os arquivos .md.")
    parser_merge.add_argument("--output_file", default=DEFAULT_CORPUS_CONSOLIDATED,
                              help=f"Arquivo de saída para o Markdown consolidado (padrão: {DEFAULT_CORPUS_CONSOLIDATED}).")

    # --- Subparser para extract_data_from_markdown.py ---
    parser_extract = subparsers.add_parser("extract", help="Extrai dados estruturados do Markdown consolidado.")
    parser_extract.add_argument("--input_file", default=DEFAULT_CORPUS_CONSOLIDATED,
                                help=f"Arquivo Markdown consolidado de entrada (padrão: {DEFAULT_CORPUS_CONSOLIDATED}).")
    parser_extract.add_argument("--output_file", default=DEFAULT_RAW_DOCS,
                                help=f"Arquivo JSON de saída para os documentos brutos (padrão: {DEFAULT_RAW_DOCS}).")

    # --- Subparser para generate_embedings.py ---
    parser_generate = subparsers.add_parser("generate_embeddings", help="Gera embeddings para os documentos processados.")
    parser_generate.add_argument("--input_file", default=DEFAULT_RAW_DOCS,
                                 help=f"Arquivo JSON de entrada com os documentos brutos (padrão: {DEFAULT_RAW_DOCS}).")
    parser_generate.add_argument("--output_file", default=DEFAULT_EMBEDDINGS,
                                 help=f"Arquivo JSON de saída para os embeddings (padrão: {DEFAULT_EMBEDDINGS}).")

    # --- Subparser para limpa_csv.py ---
    parser_clean_csv = subparsers.add_parser("clean_csv", help="Limpa o arquivo CSV de Perguntas e Respostas.")
    parser_clean_csv.add_argument("input_file", help="Arquivo CSV de entrada a ser limpo (ex: qa-data.csv).")
    parser_clean_csv.add_argument("--output_file", default=DEFAULT_QA_PROCESSED,
                                  help=f"Arquivo CSV de saída limpo (padrão: {DEFAULT_QA_PROCESSED}).")

    # --- Subparser para evaluate_coverage.py ---
    parser_evaluate = subparsers.add_parser("evaluate", help="Avalia a cobertura da documentação.")
    parser_evaluate.add_argument("qa_file",
                                 help="Caminho para o arquivo CSV limpo com perguntas e respostas.")
    parser_evaluate.add_argument("embeddings_file",
                                 help="Caminho para o arquivo JSON com chunks processados e embeddings.")
    parser_evaluate.add_argument("-k", "--top_k", type=int, default=5,
                                 help="Número de chunks mais relevantes a considerar (padrão: 5).")
    parser_evaluate.add_argument("-o", "--output", default=DEFAULT_EVAL_RESULTS,
                                 help=f"Arquivo de saída para os resultados da avaliação (padrão: {DEFAULT_EVAL_RESULTS}).")

    # --- Subparser para generate_report.py (Markdown) ---
    parser_report_md = subparsers.add_parser("report_md", help="Gera o relatório de cobertura em Markdown.")
    parser_report_md.add_argument("--input_file", default=DEFAULT_EVAL_RESULTS,
                                  help=f"Arquivo JSON de entrada com os resultados da avaliação (padrão: {DEFAULT_EVAL_RESULTS}).")
    parser_report_md.add_argument("--output_file", default=DEFAULT_MD_REPORT,
                                  help=f"Arquivo Markdown de saída para o relatório (padrão: {DEFAULT_MD_REPORT}).")
    parser_report_md.add_argument("--top_k_chunks", type=int, default=5,
                                  help="Valor de top_k_chunks usado na avaliação (para consistência do relatório, padrão: 5).")

    # --- Subparser para generate_report_html.py (HTML) ---
    parser_report_html = subparsers.add_parser("report_html", help="Gera o relatório de cobertura em HTML.")
    parser_report_html.add_argument("--input_file", default=DEFAULT_EVAL_RESULTS,
                                    help=f"Arquivo JSON de entrada com os resultados da avaliação (padrão: {DEFAULT_EVAL_RESULTS}).")
    parser_report_html.add_argument("--output_file", default=DEFAULT_HTML_REPORT,
                                    help=f"Arquivo HTML de saída para o relatório (padrão: {DEFAULT_HTML_REPORT}).")
    parser_report_html.add_argument("--top_k_chunks", type=int, default=5,
                                    help="Valor de top_k_chunks usado na avaliação (para consistência do relatório, padrão: 5).")

    # --- Subparser para o fluxo completo ---
    parser_full_flow = subparsers.add_parser("full_flow", help="Executa o fluxo completo de processamento e avaliação.")
    parser_full_flow.add_argument("doc_input_dir", help="Diretório de entrada dos arquivos .md originais.")
    parser_full_flow.add_argument("qa_input_file", help="Arquivo CSV de entrada original com Perguntas e Respostas (ex: qa-data.csv).")
    parser_full_flow.add_argument("--eval_top_k", type=int, default=5, help="Top K para a etapa de avaliação (padrão: 5).")
    parser_full_flow.add_argument("--corpus_file", default=DEFAULT_CORPUS_CONSOLIDATED)
    parser_full_flow.add_argument("--raw_docs_file", default=DEFAULT_RAW_DOCS)
    parser_full_flow.add_argument("--embeddings_file", default=DEFAULT_EMBEDDINGS)
    parser_full_flow.add_argument("--cleaned_qa_file", default=DEFAULT_QA_PROCESSED)
    parser_full_flow.add_argument("--eval_results_file", default=DEFAULT_EVAL_RESULTS)
    parser_full_flow.add_argument("--md_report_file", default=DEFAULT_MD_REPORT)
    parser_full_flow.add_argument("--html_report_file", default=DEFAULT_HTML_REPORT)


    # --- Subparser para fluxo customizado ---
    parser_custom_flow = subparsers.add_parser("custom_flow", help="Executa uma sequência customizada de scripts.")
    parser_custom_flow.add_argument("steps", nargs='+', choices=['merge', 'extract', 'generate_embeddings', 'clean_csv', 'evaluate', 'report_md', 'report_html'],
                                    help="Sequência de etapas a serem executadas (ex: merge extract generate_embeddings).")

    args = parser.parse_args()

    # Carrega a configuração
    config = load_config()

    # Se o comando for 'api', lida com a configuração da API
    if args.command == "api":
        if args.show:
            if "api_key" in config:
                masked_key = config["api_key"][:8] + "..." + config["api_key"][-4:]
                print(f"Chave da API atual: {masked_key}")
            else:
                print("Nenhuma chave da API configurada.")
        else:
            config["api_key"] = args.api_key
            save_config(config)
            print("✅ Chave da API configurada com sucesso!")
        return

    # Usa a chave da API da configuração se não for fornecida via linha de comando
    api_key = args.api or config.get("api_key")

    # Nomes dos entry points (conforme definido em setup.py)
    SCRIPT_MAP = {
        "merge": "docs-tc-merge-markdown",
        "extract": "docs-tc-extract-data",
        "generate_embeddings": "docs-tc-generate-embeddings",
        "clean_csv": "docs-tc-clean-csv",
        "evaluate": "docs-tc-evaluate-coverage",
        "report_md": "docs-tc-generate-report-md",
        "report_html": "docs-tc-generate-report-html"
    }

    if args.command == "merge":
        run_script([SCRIPT_MAP["merge"], args.input_dir, args.output_file])
    elif args.command == "extract":
        run_script([SCRIPT_MAP["extract"], args.input_file, args.output_file])
    elif args.command == "generate_embeddings":
        command_args = [SCRIPT_MAP["generate_embeddings"], args.input_file, args.output_file]
        if api_key:
            command_args.extend(["--api-key", api_key])
        run_script(command_args)
    elif args.command == "clean_csv":
        run_script([SCRIPT_MAP["clean_csv"], args.input_file, args.output_file])
    elif args.command == "evaluate":
        run_script([
            SCRIPT_MAP["evaluate"],
            args.qa_file,
            args.embeddings_file,
            "-k", str(args.top_k),
            "-o", args.output
        ])
    elif args.command == "report_md":
        run_script([
            SCRIPT_MAP["report_md"],
            args.input_file,
            args.output_file,
            str(args.top_k_chunks)
        ])
    elif args.command == "report_html":
        run_script([
            SCRIPT_MAP["report_html"],
            args.input_file,
            args.output_file,
            str(args.top_k_chunks)
        ])
    elif args.command == "full_flow":
        print("🚀 Iniciando fluxo completo...")
        def run_step_or_exit(step_command_args):
            if run_script(step_command_args) is None:
                print(f"❌ Etapa {step_command_args[0]} falhou. Abortando fluxo completo.")
                sys.exit(1)

        run_step_or_exit([SCRIPT_MAP["merge"], args.doc_input_dir, args.corpus_file])
        run_step_or_exit([SCRIPT_MAP["clean_csv"], args.qa_input_file, args.cleaned_qa_file])
        run_step_or_exit([SCRIPT_MAP["extract"], args.corpus_file, args.raw_docs_file])
        
        # Adiciona a chave da API ao comando generate_embeddings se fornecida
        generate_embeddings_args = [SCRIPT_MAP["generate_embeddings"], args.raw_docs_file, args.embeddings_file]
        if api_key:
            generate_embeddings_args.extend(["--api-key", api_key])
        run_step_or_exit(generate_embeddings_args)
        
        run_step_or_exit([
            SCRIPT_MAP["evaluate"],
            args.cleaned_qa_file,
            args.embeddings_file,
            "-k", str(args.eval_top_k),
            "-o", args.eval_results_file
        ])
        run_step_or_exit([
            SCRIPT_MAP["report_md"],
            args.eval_results_file,
            args.md_report_file,
            str(args.eval_top_k)
        ])
        run_step_or_exit([
            SCRIPT_MAP["report_html"],
            args.eval_results_file,
            args.html_report_file,
            str(args.eval_top_k)
        ])
        print("🎉 Fluxo completo concluído!")

    elif args.command == "custom_flow":
        print(f"▶️ Iniciando fluxo customizado: {' -> '.join(args.steps)}")
        current_corpus_file = DEFAULT_CORPUS_CONSOLIDATED
        current_raw_docs_file = DEFAULT_RAW_DOCS
        current_embeddings_file = DEFAULT_EMBEDDINGS
        current_cleaned_qa_file = DEFAULT_QA_PROCESSED
        current_eval_results_file = DEFAULT_EVAL_RESULTS
        default_eval_top_k = 5

        def run_custom_step_or_exit(step_command_args):
            if run_script(step_command_args) is None:
                print(f"❌ Etapa {step_command_args[0]} falhou. Abortando fluxo customizado.")
                sys.exit(1)

        for step in args.steps:
            print(f"\n--- Executando etapa: {step} ---")
            if step == "merge":
                doc_input_dir = input("Por favor, informe o diretório de entrada para 'merge' (pressione Enter para usar 'docs' como padrão): ") or "docs"
                run_custom_step_or_exit([SCRIPT_MAP["merge"], doc_input_dir, current_corpus_file])
            elif step == "extract":
                 if not os.path.exists(current_corpus_file):
                     current_corpus_file = input(f"Arquivo Corpus ({current_corpus_file}) não encontrado. Informe o caminho correto: ")
                 run_custom_step_or_exit([SCRIPT_MAP["extract"], current_corpus_file, current_raw_docs_file])
            elif step == "generate_embeddings":
                if not os.path.exists(current_raw_docs_file):
                     current_raw_docs_file = input(f"Arquivo Raw Docs ({current_raw_docs_file}) não encontrado. Informe o caminho correto: ")
                command_args = [SCRIPT_MAP["generate_embeddings"], current_raw_docs_file, current_embeddings_file]
                if api_key:
                    command_args.extend(["--api-key", api_key])
                run_custom_step_or_exit(command_args)
            elif step == "clean_csv":
                qa_input_file = input("Por favor, informe o arquivo CSV de Q&A original para 'clean_csv' (pressione Enter para usar 'qa-data.csv'): ") or "qa-data.csv"
                run_custom_step_or_exit([SCRIPT_MAP["clean_csv"], qa_input_file, current_cleaned_qa_file])
            elif step == "evaluate":
                if not os.path.exists(current_cleaned_qa_file):
                     current_cleaned_qa_file = input(f"Arquivo QA limpo ({current_cleaned_qa_file}) não encontrado. Informe o caminho correto: ")
                if not os.path.exists(current_embeddings_file):
                     current_embeddings_file = input(f"Arquivo de Embeddings ({current_embeddings_file}) não encontrado. Informe o caminho correto: ")
                eval_k_str = input(f"Informe o top_k para evaluate (pressione Enter para usar {default_eval_top_k}): ") or str(default_eval_top_k)
                run_custom_step_or_exit([
                    SCRIPT_MAP["evaluate"],
                    current_cleaned_qa_file, current_embeddings_file,
                    "-k", eval_k_str,
                    "-o", current_eval_results_file
                ])
            elif step == "report_md":
                 if not os.path.exists(current_eval_results_file):
                     current_eval_results_file = input(f"Arquivo de Resultados da Avaliação ({current_eval_results_file}) não encontrado. Informe o caminho correto: ")
                 report_k_str = input(f"Informe o top_k_chunks para report_md (pressione Enter para usar {default_eval_top_k}, deve coincidir com o usado na avaliação): ") or str(default_eval_top_k)
                 run_custom_step_or_exit([
                    SCRIPT_MAP["report_md"], current_eval_results_file, DEFAULT_MD_REPORT, report_k_str
                ])
            elif step == "report_html":
                if not os.path.exists(current_eval_results_file):
                     current_eval_results_file = input(f"Arquivo de Resultados da Avaliação ({current_eval_results_file}) não encontrado. Informe o caminho correto: ")
                report_k_str = input(f"Informe o top_k_chunks para report_html (pressione Enter para usar {default_eval_top_k}, deve coincidir com o usado na avaliação): ") or str(default_eval_top_k)
                run_custom_step_or_exit([
                    SCRIPT_MAP["report_html"], current_eval_results_file, DEFAULT_HTML_REPORT, report_k_str
                ])
        print("⏹️ Fluxo customizado concluído.")

if __name__ == "__main__":
    main()