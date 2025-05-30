# Toolkit de Análise e Cobertura de Documentação Técnica (`docs-cli`)

Este toolkit fornece um conjunto de scripts Python para processar documentação técnica em formato Markdown, gerar embeddings semânticos, avaliar a cobertura da documentação em relação a um conjunto de perguntas e respostas, e gerar relatórios detalhados. O script principal `docs_tc.py` orquestra a execução dos scripts individuais.

## Pré-requisitos

1.  **Python 3.7+**: certifique-se de que o Python está instalado e configurado no seu PATH.
2.  **Dependências Python**: instale as bibliotecas necessárias. É recomendado criar um ambiente virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows
    pip install google-generativeai python-dotenv numpy pandas
    ```
    Você também pode criar um arquivo `requirements.txt` com o conteúdo acima e rodar `pip install -r requirements.txt`.
3.  **Chave da API Google Gemini**:
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Dentro do `.env`, adicione sua chave da API:
        ```
        GOOGLE_API_KEY="SUA_CHAVE_API_AQUI"
        ```
    * **IMPORTANTE**: o arquivo `.env` contém informações sensíveis e **não deve ser versionado** no Git. Adicione `.env` ao seu arquivo `.gitignore`.

## Estrutura de Arquivos Esperada (Antes da Execução)  

```txt
/seu-projeto-raiz/
|-- docs_tc.py                   # Script orquestrador principal
|-- merge_markdown.py            # Script para consolidar .md
|-- extract_data_from_markdown.py  # Script para extrair dados do .md consolidado
|-- generate_embeddings.py        # Script para gerar embeddings
|-- limpa_csv.py                 # Script para limpar o CSV de Q&A
|-- evaluate_coverage.py         # Script para avaliar a cobertura
|-- generate_report.py           # Script para gerar relatório .md
|-- generate_report_html.py      # Script para gerar relatório .html
```
## Arquivos Gerados (e não versionados por padrão):

Os seguintes arquivos são gerados durante a execução dos scripts. É recomendado adicioná-los ao seu `.gitignore` se você não pretende versioná-los:

- `corpus_consolidated.md`
- `raw_docs.json`
- `embedings.json` (ou o nome que você usar para o arquivo de embeddings)
- `gartner_filtrado_processed.csv` (ou o nome do seu CSV de Q&A limpo)
- `evaluation_results.json`
- `coverage_report.md`
- `coverage_report.html`

### Configuração do `.gitignore`:

#### Arquivos de Ambiente
```gitignore	
.env
chaves/.env
```
#### Arquivos de Dados Gerados
```gitignore
# Ignorar arquivos gerados automaticamente 
*.json
*.csv
*.md
*.html
```

#### Exceto os arquivos que SÃO parte do toolkit/interface

```bash
# Mantenha estes arquivos versionados (exceções à regra global)
!docs_tc.py
!merge_markdown.py
!extract_data_from_markdown.py
!generate_embedings.py
!limpa_csv.py
!evaluate_coverage.py
!generate_report.py
!generate_report_html.py
!assistente/index.html
!assistente/about.html
!assistente/mudanca.html
!README.md
!requirements.txt
```

#### Arquivos de Cache Python
```gitignore	
pycache/
*.py[cod]
*$py.class
```
#### Ambiente Virtual
```gitignore
venv/
```

- Ajuste o `.gitignore` acima para manter os arquivos `.md` e `.html` que são parte da sua documentação ou da ferramenta em si (como este `README.md` ou o `index.html` da interface).*
- No exemplo acima, `*.json`, `*.csv`, `*.md`, `*.html` são ignorados globalmente, e depois exceções são adicionadas. Seus arquivos de documentação originais em `DocumentosMD/` e o CSV bruto em `DadosQA/` **não serão ignorados** por esta configuração, o que é o desejado.*

## Utilização do `docs-cli`

O `docs_tc.py` é o ponto de entrada principal para utilizar o toolkit. Abra um terminal na raiz do projeto.

### 1. Ajuda Geral e de Comandos:

```bash
docs-cli -h
docs-cli <comando> -h  # Ex: docs-cli merge -h
```
### 2. Execução de Comandos Individuais:

Cada script pode ser chamado por um subcomando. Os nomes de arquivo padrão são usados se não especificados.

#### Consolidar Documentos (`merge`):

```bash
docs-cli merge ./docs/ --output_file corpus_consolidated.md

```

- `./docs/`: Diretório contendo seus arquivos .md originais.
- `-output_file`: (opcional) Nome do arquivo consolidado. Padrão: `corpus_consolidated.md`.

#### Extrair Dados do Markdown Consolidado (`extract`):

```bash
docs-cli extract --input_file corpus_consolidated.md --output_file raw_docs.json
```

- `-input_file`: (Opcional) Arquivo .md consolidado. Padrão: `corpus_consolidated.md`.
- `-output_file`: (Opcional) Arquivo JSON para os dados brutos. Padrão: `raw_docs.json`.

#### Gerar Embeddings (`generate_embeddings`):

```bash
docs-cli generate_embeddings --input_file raw_docs.json --output_file embeddings.json
```

- `-input_file`: (Opcional) Arquivo JSON com os dados brutos. Padrão: `raw_docs.json`.
- `-output_file`: (Opcional) Arquivo JSON para os embeddings. Padrão: `embeddings.json`.

#### Limpar CSV de Q&A (`clean_csv`):

```bash
docs-cli clean_csv ./csv/qa_bruto.csv --output_file qa_processado.csv
```

- `./csv/qa_bruto.csv`: Caminho para o arquivo CSV de perguntas e respostas bruto.
- `-output_file`: (Opcional) Nome do arquivo CSV processado. Padrão: `gartner_filtrado_processed.csv`.

#### Avaliar Cobertura (`evaluate_coverage`):

```bash
docs-cli evaluate qa_processado.csv embeddings.json -k 5 -o evaluation_results.json
```

- `qa_processado.csv`: Caminho para o arquivo CSV de perguntas e respostas processado.
- `embeddings.json`: Caminho para o arquivo JSON com os embeddings.
- `-k`: (Opcional) Número de resultados a retornar. Padrão: 5.
- `-o`: (Opcional) Nome do arquivo JSON para os resultados da avaliação. Padrão: `evaluation_results.json`.
De forma geral, os parâmetros são:

| Parâmetro                | Tipo    | Obrigatório | Descrição                                                                                       |
|--------------------------|---------|-------------|-------------------------------------------------------------------------------------------------|
| `qa_file`                | string  | Sim         | Caminho para o arquivo CSV com perguntas e respostas                                            |
| `embeddings_file`        | string  | Sim         | Caminho para o arquivo JSON com os chunks processados e embeddings                              |
| `-k`, `--top-k`          | inteiro | Não         | Número de chunks mais relevantes a considerar (padrão: `5`)                                       |
| `-o`, `--output`         | string  | Não         | Caminho do arquivo de saída para os resultados (padrão: `evaluation_results.json`)              |

#### Gerar Relatório Markdown (`generate_report`):

```bash
docs-cli generate_report evaluation_results.json --output_file coverage_report.md
```

- `evaluation_results.json`: Caminho para o arquivo JSON com os resultados da avaliação.
- `-output_file`: (Opcional) Nome do arquivo Markdown para o relatório. Padrão: `coverage_report.md`.

#### Gerar Relatório HTML (`generate_report_html`):

```bash
docs-cli generate_report_html evaluation_results.json --output_file coverage_report.html
```

- `evaluation_results.json`: Caminho para o arquivo JSON com os resultados da avaliação.
- `-output_file`: (Opcional) Nome do arquivo HTML para o relatório. Padrão: `coverage_report.html`.

## Executando o Toolkit Completo
Para executar todo o fluxo de trabalho do toolkit, você pode usar o comando principal `docs_tc.py` com o subcomando `full_flow`. Este comando executa todos os passos necessários, desde a consolidação dos documentos até a geração dos relatórios.

```bash
docs-cli full_flow ./docs/ ./csv/qa_bruto.csv --eval_top_k 5 --embeddings_file embedings.json
```

## Manutenção e Versionamento

- NÃO FAÇA COMMIT do seu arquivo `.env` contendo a `GOOGLE_API_KEY`.
- NÃO FAÇA COMMIT dos arquivos de dados gerados automaticamente (como `corpus_consolidated.md`, `raw_docs.json`, `embedings.json`, `evaluation_results.json`, etc.), a menos que tenha um motivo específico para versionar um estado particular desses dados. Adicione-os ao seu `.gitignore`.
- O arquivo CSV original com os dados de Q&A e os arquivos Markdown originais da sua documentação podem e devem ser versionados se fizerem parte da fonte do seu projeto.

---

Dê um alô :)
paulo[at]paulogpd.com.br
