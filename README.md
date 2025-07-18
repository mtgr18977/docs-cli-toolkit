# Docs CLI Toolkit

Uma ferramenta de linha de comando para processamento e análise de documentação, com suporte a geração de embeddings usando as APIs do Google Gemini, OpenAI ou DeepInfra.

## Instalação

```bash
pip install docs-cli-toolkit
```

## Configuração das APIs (Gemini, DeepInfra/Maritaca ou OpenAI)

A ferramenta oferece três maneiras de configurar as chaves das APIs do Google Gemini, DeepInfra/Maritaca ou OpenAI:

1. **Configuração Global (Recomendada para Gemini):**
   ```bash
   docs-cli api "sua-chave-api"
   ```
   Para verificar a chave configurada (parcialmente mascarada) sem fornecer uma nova chave:
   ```bash
   docs-cli api --show
   ```

2. **Via Linha de Comando:**
   - Para Gemini:
     ```bash
     docs-cli --api "sua-chave-gemini" generate_embeddings input.json output.json
     ```
   - Para DeepInfra/Maritaca:
     ```bash
     docs-cli generate_embeddings --provider deepinfra --deepinfra-api-key "sua-chave-deepinfra" input.json output.json
     ```
   - Para OpenAI:
     ```bash
     docs-cli generate_embeddings --provider openai --openai-api-key "sua-chave-openai" input.json output.json
     ```

3. **Via Variável de Ambiente:**
   Crie um arquivo `.env` no diretório do projeto:
 ```
  GOOGLE_API_KEY=sua-chave-gemini
  DEEPINFRA_API_KEY=sua-chave-deepinfra
  OPENAI_API_KEY=sua-chave-openai
  ```
  Um arquivo `/.env.example` está disponível com esse formato.
  Se você não especificar `--provider`, o comando escolhe automaticamente `openai` quando `OPENAI_API_KEY` estiver definido; caso contrário usa o Gemini.

## Comandos Disponíveis

### 1. Merge de Documentos
Consolida múltiplos arquivos Markdown em um único arquivo:
```bash
docs-cli merge <diretório_entrada> [arquivo_saída.md]
```

### 2. Extração de Dados
Extrai dados estruturados do Markdown consolidado:
```bash
docs-cli extract [arquivo_entrada.md] [arquivo_saída.json]
```

### 3. Geração de Embeddings
Gera embeddings para os documentos processados:
```bash
# Usando Gemini (padrão)
docs-cli generate_embeddings [arquivo_entrada.json] [arquivo_saída.json]

# Usando DeepInfra/Maritaca
docs-cli generate_embeddings --provider deepinfra --deepinfra-api-key "sua-chave" [arquivo_entrada.json] [arquivo_saída.json]
# Usando OpenAI
docs-cli generate_embeddings --provider openai --openai-api-key "sua-chave" [arquivo_entrada.json] [arquivo_saída.json]
```

### 4. Limpeza de CSV
Limpa e processa arquivos CSV de perguntas e respostas:
```bash
docs-cli clean_csv <arquivo_entrada.csv> [--output_file arquivo_saída.csv] [--question_col coluna_perguntas] [--response_col coluna_respostas] [--encoding utf-8] [--min_length 10] [--no_clean_text] [--invalid_patterns padrão1 padrão2 ...]
```

Opções disponíveis:
- `--output_file`: Arquivo CSV de saída limpo (padrão: qa_data_clean.csv)
- `--question_col`: Nome da coluna de perguntas (padrão: question)
- `--response_col`: Nome da coluna de respostas (padrão: response)
- `--encoding`: Encoding do arquivo CSV (padrão: utf-8)
- `--min_length`: Tamanho mínimo para respostas válidas (padrão: 10)
- `--no_clean_text`: Não limpar o texto das respostas
- `--invalid_patterns`: Lista de frases ou expressões a remover. Se não informado,
  são usados padrões comuns como `"Please select from dropdown"`, `"Click here"`
  e variações similares.

Exemplos:
```bash
# Limpeza básica
docs-cli clean_csv qa-data.csv

# Especificando colunas diferentes
docs-cli clean_csv qa-data.csv --question_col "pergunta" --response_col "resposta"

# Configurando encoding e tamanho mínimo
docs-cli clean_csv qa-data.csv --encoding "latin1" --min_length 20

# Adicionando padrões inválidos personalizados
docs-cli clean_csv qa-data.csv --invalid_patterns "Selecione uma opção" "Clique aqui" "Escolha um item"
```

### 5. Avaliação de Cobertura
Avalia a cobertura da documentação:
```bash
docs-cli evaluate <arquivo_qa.csv> <arquivo_embeddings.json> [-k N] [-o arquivo_saída.json]
```

### 6. Geração de Relatórios
Gera relatórios em Markdown e HTML:
```bash
# Relatório em Markdown
docs-cli report_md [arquivo_entrada.json] [relatório.md] [top_k_chunks]

# Relatório em HTML
docs-cli report_html [arquivo_entrada.json] [relatório.html] [top_k_chunks]
```

### 7. Fluxo Completo
Executa todo o pipeline de processamento:
```bash
docs-cli full_flow <diretório_docs> <arquivo_qa.csv> [--eval_top_k N]
```

### 8. Fluxo Customizado
Executa uma sequência personalizada de etapas:
```bash
docs-cli custom_flow [opções] <etapas...>
```
Etapas disponíveis: `merge`, `extract`, `generate_embeddings`, `clean_csv`, `evaluate`, `report_md`, `report_html`.
Principais opções:
`--doc_input_dir`, `--qa_input_file`, `--corpus_file`, `--raw_docs_file`,
`--embeddings_file`, `--cleaned_qa_file`, `--eval_results_file`,
`--md_report_file`, `--html_report_file` e `--eval_top_k`.
Use-as para definir caminhos ou parâmetros específicos durante o fluxo.

## Exemplos de Uso

### Processamento Básico
```bash
# Configurar a API (uma única vez)
docs-cli api "sua-chave-api"

# Processar documentação
docs-cli full_flow docs/ qa-data.csv
```

### Fluxo Customizado
```bash
# Executar apenas merge e extração
docs-cli custom_flow --doc_input_dir docs --corpus_file corpus.md merge extract

# Executar geração de embeddings com chave API temporária
docs-cli --api "chave-temporária" custom_flow generate_embeddings
```

### Geração de Relatórios
```bash
# Gerar relatório em Markdown
docs-cli report_md evaluation_results.json coverage.md

# Gerar relatório em HTML
docs-cli report_html evaluation_results.json coverage.html
```

## Arquivos Intermediários

A ferramenta utiliza os seguintes arquivos intermediários por padrão:
- `corpus_consolidated.md`: Documentos Markdown consolidados
- `raw_docs.json`: Dados estruturados extraídos
- `embeddings.json`: Embeddings gerados
- `qa_data_clean.csv`: CSV processado
- `evaluation_results.json`: Resultados da avaliação
- `coverage_report.md`: Relatório em Markdown
- `coverage_report.html`: Relatório em HTML

## Requisitos

- Python 3.8+
- Google Gemini API Key
- (Opcional) OpenAI API Key
- (Opcional) DeepInfra API Key
- Dependências listadas em `pyproject.toml`

## Contribuindo

Contribuições são bem-vindas! Por favor, sinta-se à vontade para enviar um Pull Request.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
