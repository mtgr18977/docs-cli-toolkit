#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpeza do arquivo qadata.csv
Remove linhas com respostas inválidas especificadas

Autor: Paulo Duarte
Data: 2025-05-30
"""

import pandas as pd
import os
from pathlib import Path

def clean_csv_data(input_file, output_file=None):
    """
    Remove linhas com padrões de respostas inválidas do CSV
    
    Args:
        input_file (str): Caminho para o arquivo CSV de entrada
        output_file (str, optional): Caminho para o arquivo CSV de saída
    
    Returns:
        dict: Estatísticas do processamento
    """
    
    # Definir padrões de respostas inválidas
    invalid_patterns = [
        "Please select from dropdown",
        "1 2 3 4 5 Enter filename Enter filename Enter filename Enter filename Enter filename",
        "Enter filename Enter filename Enter filename Enter filename Enter filename",
        "1 2 3 4 5 6 7 8 9 10",
        "Use + or - signs on the left to Expand or collapse Static Entitlement Assignment Policies Dynamic Entitlement Assignment Policies SOD Policies Enter filename Enter filename Enter filename Enter filename Enter filename"
    ]
    
    try:
        # Ler o arquivo CSV
        print(f"📖 Lendo arquivo: {input_file}")
        df = pd.read_csv(input_file, encoding='utf-8')
        
        print(f"✅ Arquivo carregado com sucesso!")
        print(f"📊 Linhas originais: {len(df)}")
        print(f"📋 Colunas: {list(df.columns)}")
        
        # Criar cópia para trabalhar
        df_clean = df.copy()
        
        # Contador de linhas removidas por padrão
        removal_stats = {}
        total_removed = 0
        
        # Remover linhas que contêm os padrões inválidos
        for pattern in invalid_patterns:
            # Encontrar linhas que contêm o padrão
            mask = df_clean['response'].astype(str).str.contains(pattern, na=False)
            rows_with_pattern = mask.sum()
            
            if rows_with_pattern > 0:
                # Remover as linhas
                df_clean = df_clean[~mask]
                removal_stats[pattern[:50] + "..."] = rows_with_pattern
                total_removed += rows_with_pattern
                print(f"🗑️  Removidas {rows_with_pattern} linhas com padrão: '{pattern[:50]}...'")
        
        # Gerar nome do arquivo de saída se não fornecido
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_clean{input_path.suffix}"
        
        # Salvar arquivo limpo
        df_clean.to_csv(output_file, index=False, encoding='utf-8')
        print(f"💾 Arquivo limpo salvo: {output_file}")
        
        # Preparar estatísticas
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
        for pattern, count in stats['removal_details'].items():
            print(f"   • {count:2d}x: {pattern}")
    
    print("="*60)
    print("✨ Processamento concluído com sucesso!")

def main():
    """
    Função principal do script
    """
    print("🧹 CSV Cleaner - Limpeza de Dados QA")
    print("="*50)
    
    # Configurar arquivos
    input_file = "data.csv"

    # Verificar se o arquivo existe
    if not os.path.exists(input_file):
        print(f"❌ Arquivo '{input_file}' não encontrado no diretório atual!")
        print("💡 Certifique-se de que o arquivo está no mesmo diretório do script.")
        return
    
    # Processar o arquivo
    stats = clean_csv_data(input_file)
    
    # Mostrar resumo
    if stats:
        print_summary(stats)
    else:
        print("❌ Falha no processamento do arquivo!")

def cli_main(): # Nova main para CLI
    import argparse
    import os # Para os.path.exists
    import sys # Para sys.exit
    parser = argparse.ArgumentParser(description="Limpa um arquivo CSV de Q&A removendo padrões inválidos.")
    parser.add_argument("input_file", help="Caminho para o arquivo CSV de entrada.")
    parser.add_argument("output_file", help="Caminho para salvar o arquivo CSV limpo.")
    args = parser.parse_args()

    print("🧹 CSV Cleaner - Limpeza de Dados QA")
    print("="*50)
    if not os.path.exists(args.input_file):
        print(f"❌ Arquivo '{args.input_file}' não encontrado no diretório atual!")
        sys.exit(1)

    stats = clean_csv_data(args.input_file, args.output_file) # Passa ambos os argumentos
    if stats:
        print_summary(stats)
    else:
        print("❌ Falha no processamento do arquivo!")
        sys.exit(1)

if __name__ == "__main__":
    # from pathlib import Path # Mantenha se Path for usado em clean_csv_data
    cli_main()