# Novo ou modificado: extract_consolidated_md_to_raw_json.py
import re
import json
import os

def extract_docs_from_consolidated_md(input_md_path="corpus_consolidated.md", output_json_path="raw_docs.json"):
    """
    Lê o arquivo MD consolidado, divide-o em documentos individuais
    e extrai seu conteúdo e metadados para raw_docs.json.
    """
    if not os.path.exists(input_md_path):
        print(f"Erro: O arquivo consolidado '{input_md_path}' não foi encontrado.")
        return False

    print(f"Extraindo documentos de '{input_md_path}'...")
    
    with open(input_md_path, 'r', encoding='utf-8') as f:
        full_content = f.read()

    # Padrão para identificar o início de um novo documento e capturar o caminho do arquivo
    # E também o conteúdo de metadados
    doc_sections = re.split(r'(^## Arquivo: (.*?)\.md$)', full_content, flags=re.MULTILINE)

    extracted_docs = []
    current_doc_filepath = None
    current_doc_content = []
    
    # Ignora o primeiro elemento de doc_sections se estiver vazio (antes do primeiro cabeçalho)
    # ou se for a primeira quebra
    for i, section_part in enumerate(doc_sections):
        if i == 0:
            continue # Ignora o que vem antes do primeiro "## Arquivo:"

        if section_part.startswith("## Arquivo:"): # É o cabeçalho de um novo documento
            # Se já temos conteúdo do documento anterior, salve-o
            if current_doc_filepath and current_doc_content:
                # Extrair metadados e conteúdo
                full_doc_content_str = "\n".join(current_doc_content).strip()
                title, slug, content_for_doc = extract_metadata_and_content(full_doc_content_str, current_doc_filepath)
                extracted_docs.append({
                    "title": title,
                    "slug": slug,
                    "content": content_for_doc,
                    "filepath": current_doc_filepath
                })
            
            # Iniciar um novo documento
            match = re.match(r'^## Arquivo: (.*?)\.md$', section_part.strip())
            if match:
                current_doc_filepath = match.group(1) + ".md" # Recompõe o filepath
            current_doc_content = [] # Reseta o conteúdo
        elif i % 2 != 0: # Isso pega o conteúdo que segue o cabeçalho '## Arquivo:'
            # Este é o conteúdo completo do documento, incluindo o Metadata_Start/End
            current_doc_content.append(section_part.strip())
        # else: este é o grupo de captura do regex, ignoramos aqui

    # Salva o último documento após o loop
    if current_doc_filepath and current_doc_content:
        full_doc_content_str = "\n".join(current_doc_content).strip()
        title, slug, content_for_doc = extract_metadata_and_content(full_doc_content_str, current_doc_filepath)
        extracted_docs.append({
            "title": title,
            "slug": slug,
            "content": content_for_doc,
            "filepath": current_doc_filepath
        })

    # Verifica se algum documento foi realmente extraído
    if not extracted_docs:
        print("Atenção: Nenhum documento válido foi extraído do arquivo consolidado.")
        return False

    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_docs, f, ensure_ascii=False, indent=4)
        print(f"Extração concluída. Salvou {len(extracted_docs)} documentos em '{output_json_path}'.")
        return True
    except Exception as e:
        print(f"Erro ao salvar o arquivo JSON de documentos brutos: {e}")
        return False

def extract_metadata_and_content(doc_full_text, default_filepath):
    """
    Extrai metadados (title, slug) e o conteúdo principal de um bloco de documento,
    ignorando as seções Metadata_Start/End.
    """
    title = "Título Desconhecido"
    slug = ""
    content = doc_full_text

    # Expressão regular para encontrar o bloco Metadata_Start/End
    metadata_match = re.search(r'## Metadata_Start(.*?)## Metadata_End', doc_full_text, re.DOTALL)
    
    if metadata_match:
        metadata_block = metadata_match.group(1)
        # Extrai title e slug do bloco de metadados
        title_match = re.search(r'## title: (.*)', metadata_block)
        if title_match:
            title = title_match.group(1).strip()
        
        slug_match = re.search(r'## slug: (.*)', metadata_block)
        if slug_match:
            slug = slug_match.group(1).strip()

        # Remove o bloco de metadados do conteúdo principal
        content = re.sub(r'## Metadata_Start.*?## Metadata_End', '', doc_full_text, flags=re.DOTALL).strip()
    
    # Remove o cabeçalho "## Arquivo: ..." que foi usado para dividir
    content = re.sub(r'^## Arquivo: .*$', '', content, flags=re.MULTILINE).strip()

    return title, slug, content

def cli_main():
    import argparse
    parser = argparse.ArgumentParser(description="Extrai dados do arquivo MD consolidado para JSON.")
    parser.add_argument("input_md_path", help="Caminho para o arquivo MD consolidado de entrada.")
    parser.add_argument("output_json_path", help="Caminho para o arquivo JSON de saída (ex: raw_docs.json).")
    args = parser.parse_args()
    success = extract_docs_from_consolidated_md(args.input_md_path, args.output_json_path)
    if not success:
        print("A extração de documentos do MD consolidado falhou.")
        sys.exit(1)
    else:
        print("Extração de documentos do MD consolidado concluída com sucesso.")

if __name__ == "__main__":
    import sys # Adicione se não estiver importado
    cli_main()