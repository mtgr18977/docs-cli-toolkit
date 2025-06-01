#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpeza de arquivos CSV de perguntas e respostas
Remove linhas com respostas inválidas e realiza outras operações de limpeza

Autor: Paulo Duarte
Data: 2024-03-19
"""

import pandas as pd
import os
from pathlib import Path
import argparse
import sys
import re

def clean_text(text):
    """
    Realiza limpeza básica do texto
    
    Args:
        text (str): Texto a ser limpo
    
    Returns:
        str: Texto limpo
    """
    if not isinstance(text, str):
        return ""
    
    # Remove espaços extras
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove caracteres especiais comuns
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text

def clean_csv_data(input_file, output_file=None, question_col='question', 
                  response_col='response', encoding='utf-8', min_length=10,
                  invalid_patterns=None, clean_text_flag=True):
    """
    Remove linhas com padrões de respostas inválidas do CSV e realiza outras operações de limpeza
    
    Args:
        input_file (str): Caminho para o arquivo CSV de entrada
        output_file (str, optional): Caminho para o arquivo CSV de saída
        question_col (str): Nome da coluna de perguntas
        response_col (str): Nome da coluna de respostas
        encoding (str): Encoding do arquivo CSV
        min_length (int): Tamanho mínimo para considerar uma resposta válida
        invalid_patterns (list): Lista de padrões inválidos para remover
        clean_text_flag (bool): Se deve limpar o texto das respostas
    
    Returns:
        dict: Estatísticas do processamento
    """
    
    # Padrões padrão de respostas inválidas se nenhum for fornecido
    if invalid_patterns is None:
        invalid_patterns = [
            "Please select from dropdown",
            "Enter filename",
            "1 2 3 4 5",
            "Use + or - signs",
            "Select an option",
            "Click here",
            "Choose from",
            "Please choose",
            "Select from",
            "Choose one",
            "Select one"
        ]
    
    try:
        # Ler o arquivo CSV
        print(f"📖 Lendo arquivo: {input_file}")
        df = pd.read_csv(input_file, encoding=encoding)
        
        # Verificar se as colunas existem
        required_cols = [question_col, response_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Colunas não encontradas no CSV: {', '.join(missing_cols)}")
        
        print(f"✅ Arquivo carregado com sucesso!")
        print(f"📊 Linhas originais: {len(df)}")
        print(f"📋 Colunas: {list(df.columns)}")
        
        # Criar cópia para trabalhar
        df_clean = df.copy()
        
        # Contador de linhas removidas por motivo
        removal_stats = {
            'invalid_patterns': 0,
            'short_responses': 0,
            'empty_responses': 0,
            'duplicates': 0
        }
        
        # Remover linhas com respostas vazias
        empty_mask = df_clean[response_col].isna() | (df_clean[response_col].astype(str).str.strip() == '')
        removal_stats['empty_responses'] = empty_mask.sum()
        df_clean = df_clean[~empty_mask]
        
        # Remover linhas com respostas muito curtas
        short_mask = df_clean[response_col].astype(str).str.len() < min_length
        removal_stats['short_responses'] = short_mask.sum()
        df_clean = df_clean[~short_mask]
        
        # Remover linhas que contêm os padrões inválidos
        for pattern in invalid_patterns:
            mask = df_clean[response_col].astype(str).str.contains(pattern, case=False, na=False)
            if mask.any():
                df_clean = df_clean[~mask]
                removal_stats['invalid_patterns'] += mask.sum()
                print(f"🗑️  Removidas {mask.sum()} linhas com padrão: '{pattern}'")
        
        # Remover duplicatas
        original_len = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=[question_col, response_col])
        removal_stats['duplicates'] = original_len - len(df_clean)
        
        # Limpar o texto das respostas se solicitado
        if clean_text_flag:
            df_clean[response_col] = df_clean[response_col].apply(clean_text)
        
        # Gerar nome do arquivo de saída se não fornecido
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_clean{input_path.suffix}"
        
        # Salvar arquivo limpo
        df_clean.to_csv(output_file, index=False, encoding=encoding)
        print(f"💾 Arquivo limpo salvo: {output_file}")
        
        # Preparar estatísticas
        total_removed = sum(removal_stats.values())
        stats = {
            'original_rows': len(df),
            'removed_rows': total_removed,
            'final_rows': len(df_clean),
            'removal_rate': (total_removed / len(df)) * 100,
            'removal_details': removal_stats,
            'output_file': str(output_file)
        }
        
        return stats
        
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{input_file}' não encontrado!")
        return None
    except Exception as e:
        print(f"❌ Erro durante o processamento: {str(e)}")
        return None

def print_summary(stats):
    """
    Imprime um resumo formatado das estatísticas
    
    Args:
        stats (dict): Estatísticas do processamento
    """
    if not stats:
        return
    
    print("\n" + "="*60)
    print("📊 RESUMO DO PROCESSAMENTO")
    print("="*60)
    print(f"📈 Total de linhas originais:  {stats['original_rows']:,}")
    print(f"🗑️  Linhas removidas:          {stats['removed_rows']:,}")
    print(f"✅ Linhas no arquivo limpo:   {stats['final_rows']:,}")
    print(f"📉 Taxa de remoção:           {stats['removal_rate']:.1f}%")
    print(f"💾 Arquivo de saída:          {stats['output_file']}")
    
    if stats['removal_details']:
        print("\n📋 DETALHES DAS REMOÇÕES:")
        print("-" * 50)
        for reason, count in stats['removal_details'].items():
            if count > 0:
                print(f"   • {count:2d}x: {reason}")
    
    print("="*60)
    print("✨ Processamento concluído com sucesso!")

def cli_main():
    """Função principal para interface de linha de comando"""
    parser = argparse.ArgumentParser(description="Limpa um arquivo CSV de perguntas e respostas.")
    
    # Argumentos obrigatórios
    parser.add_argument("input_file", help="Caminho para o arquivo CSV de entrada.")
    
    # Argumentos opcionais
    parser.add_argument("--output_file", help="Caminho para salvar o arquivo CSV limpo.")
    parser.add_argument("--question_col", default="question", help="Nome da coluna de perguntas (padrão: question)")
    parser.add_argument("--response_col", default="response", help="Nome da coluna de respostas (padrão: response)")
    parser.add_argument("--encoding", default="utf-8", help="Encoding do arquivo CSV (padrão: utf-8)")
    parser.add_argument("--min_length", type=int, default=10, help="Tamanho mínimo para respostas válidas (padrão: 10)")
    parser.add_argument("--no_clean_text", action="store_true", help="Não limpar o texto das respostas")
    parser.add_argument("--invalid_patterns", nargs="+", help="Lista de padrões inválidos para remover")
    
    args = parser.parse_args()
    
    print("🧹 CSV Cleaner - Limpeza de Dados QA")
    print("="*50)
    
    if not os.path.exists(args.input_file):
        print(f"❌ Arquivo '{args.input_file}' não encontrado!")
        sys.exit(1)
    
    stats = clean_csv_data(
        input_file=args.input_file,
        output_file=args.output_file,
        question_col=args.question_col,
        response_col=args.response_col,
        encoding=args.encoding,
        min_length=args.min_length,
        invalid_patterns=args.invalid_patterns,
        clean_text_flag=not args.no_clean_text
    )
    
    if stats:
        print_summary(stats)
    else:
        print("❌ Falha no processamento do arquivo!")
        sys.exit(1)

if __name__ == "__main__":
    cli_main()