**Descrição da Tarefa / Task Description**  
Documentar em um único arquivo Markdown a definição, configuração e exemplos de uso de cada agente que compõe seu sistema baseado em Codex. Este documento deve servir como referência rápida para desenvolvedores e integradores entendendo como instanciar e chamar cada agente, quais permissões e variáveis de ambiente são necessárias, e oferecer exemplos de chamadas (inputs/outputs).

---

## 1. Visão Geral / Overview  
- **Objetivo / Purpose**  
  - Fornecer instruções claras sobre como configurar, instanciar e usar cada agente no projeto.  
  - Explaining the role of each agent, its responsibilities, and how it interacts with other components.  

- **Público-Alvo / Audience**  
  - Desenvolvedores que irão integrar os agentes no pipeline.  
  - DevOps encarregado do deploy e configuração de variáveis de ambiente.  
  - Tech writers que precisam manter ou expandir a documentação do sistema.  

---

## 2. Estrutura do Arquivo / File Structure  
```markdown
Agents.md
├── 1-VisaoGeral.md        ← Esta seção (Overview)
├── 2-EnvSetup              ← Configuração de ambiente e variáveis
├── 3-AgentDefinitions      ← Definição de cada agente
│   ├── AgentA.md           ← Exemplo de agente específico
│   ├── AgentB.md
│   └── ...
├── 4-UsageExamples         ← Exemplos de uso em código ou CLI
├── 5-Notes                 ← Casos especiais, troubleshooting, best practices
└── 6-Changelog             ← Histórico de mudanças no Agents.md
```
> (_Em projetos simples, pode-se concentrar tudo em um único Agents.md dividido por títulos e subtítulos._)

---

## 3. Configuração de Ambiente / Environment Setup  
### 3.1 Variáveis de Ambiente / Environment Variables  
- **OPENAI_API_KEY**  
  - _Descrição / Description:_ Chave secreta para autenticar chamadas à API do OpenAI Codex.  
  - _Exemplo:_  
    ```bash
    export OPENAI_API_KEY="sua-chave-aqui"
    ```  
- **GEMINI_API_KEY (opcional)**  
  - _Útil se você alterna entre provedores de LLMs (Codex e Google Gemini)._  
  -  
- **DEEPINFRA_API_KEY (opcional)**  

_Se houver outras credenciais (por ex., chaves para repositório, tokens de CI/CD), liste-as aqui._  

### 3.2 Requisitos de Sistema / System Requirements  
- Python >= 3.8  
- Pacotes (pode usar `requirements.txt` ou `pyproject.toml`):  
  ```text
  openai
  google-cloud-language (se necessário)
  docs-cli-toolkit (se usar embeddings)
  python-dotenv (opcional, para carregar .env)
  ```  
- Configurar `.env` (opcional):  
  ```dotenv
  OPENAI_API_KEY=sua-chave
  GEMINI_API_KEY=sua-outra-chave
  ```  

---

## 4. Definição de Agentes / Agent Definitions  

> Cada seção abaixo representa um agente distinto que o sistema utiliza.  
> Use nomenclatura consistente (por ex., `agent_name.camelCase` ou `AGENT_NAME_SCREAMING_SNAKE`) conforme o padrão do seu projeto.

### 4.1 Agent de Análise de Documentação / Documentation Analysis Agent  
- **Nome do Agente / Agent Name:**  
  ```
  documentation_analyzer
  ```  
- **Responsabilidade / Responsibility:**  
  - Receber um bloco de Markdown ou JSON contendo documentação em bruto.  
  - Retornar um par de valores:  
    1. Resumo dos pontos-chave.  
    2. Recomendações de melhoria de fluxo (e.g., headings faltando, checkpoints sem exemplos).  
- **Código de Instanciação / Instantiation Code:**  
  ```python
  from codex_agents import DocumentationAnalyzerAgent

  doc_agent = DocumentationAnalyzerAgent(
      api_key=os.getenv("OPENAI_API_KEY"),
      model="code-davinci-002",
      temperature=0.2
  )
  ```  
- **Parâmetros de Inicialização / Initialization Parameters:**  
  | Parâmetro     | Tipo    | Descrição                                  | Padrão     |
  |---------------|---------|--------------------------------------------|------------|
  | `api_key`     | string  | Chave da API OpenAI Codex                  | ―          |
  | `model`       | string  | Identificador do modelo Codex a ser usado   | `"code-davinci-002"` |
  | `temperature` | float   | Grau de aleatoriedade na geração de texto   | `0.2`      |
  | `max_tokens`  | int     | Número máximo de tokens na resposta         | `1024`     |

- **Métodos Principais / Main Methods:**  
  1. `analyze(markdown_text: str) -> Dict[str, Any]`  
     - _Entrada:_ Texto em Markdown (ou string JSON)  
     - _Saída:_  
       ```jsonc
       {
         "summary": "Resumo conciso de até 150 palavras.",
         "recommendations": [
           "Adicionar exemplo de código na seção 3.",
           "Unificar título 'Introdução' com 'Overview' para consistência."
         ]
       }
       ```
  2. `evaluate_coverage(qa_csv_path: str, embeddings_path: str) -> CoverageReport`  
     - _Entrada:_ Caminho para um CSV de perguntas/respostas e arquivo JSON de embeddings.  
     - _Saída:_ Objeto contendo métricas de cobertura, gaps e clippings.  

- **Permissões / Required Permissions:**  
  - Acesso à Internet para chamadas HTTP ao endpoint do OpenAI.  
  - Permissão de leitura de diretórios contendo arquivos Markdown.  
  - Permissão de escrita para gerar relatórios em Markdown/HTML.  

---

### 4.2 Agent de Geração de Embeddings / Embedding Generation Agent  
- **Nome do Agente / Agent Name:**  
  ```
  embeddings_generator
  ```  
- **Responsabilidade / Responsibility:**  
  - Consumir um arquivo JSON estruturado (`raw_docs.json`) gerado pelo `extract`.  
  - Chamar o endpoint de embeddings do Codex (ou outro LLM) para cada chunk de texto.  
  - Retornar um JSON com os vetores de embeddings.  
- **Código de Instanciação / Instantiation Code:**  
  ```python
  from codex_agents import EmbeddingsGeneratorAgent

  embed_agent = EmbeddingsGeneratorAgent(
      api_key=os.getenv("OPENAI_API_KEY"),
      model="text-embedding-ada-002",  # ou outro modelo adequado
      batch_size=20
  )
  ```  
- **Parâmetros de Inicialização / Initialization Parameters:**  
  | Parâmetro    | Tipo   | Descrição                                            | Padrão        |
  |--------------|--------|------------------------------------------------------|---------------|
  | `api_key`    | string | Chave da API OpenAI                                  | ―             |
  | `model`      | string | Identificador do modelo de embeddings                | `"text-embedding-ada-002"` |
  | `batch_size` | int    | Quantidade de itens por chamada batch (para paralelizar) | `20`         |

- **Métodos Principais / Main Methods:**  
  1. `generate(input_json_path: str, output_json_path: str) -> None`  
     - _Entrada:_  
       - `input_json_path`: caminho para o arquivo JSON de chunks.  
       - `output_json_path`: caminho onde será salvo o JSON com embeddings.  
     - _Saída:_ Nenhuma (gera um arquivo no disco).  
  2. `batch_generate(chunks: List[str]) -> List[List[float]]`  
     - _Entrada:_ Lista de strings de texto.  
     - _Saída:_ Lista de vetores (cada vetor é uma lista de floats).  

- **Dependências / Dependencies:**  
  - `docs-cli-toolkit` (para lidar com formatos intermediários).  
  - `openai` ou `google-cloud-language` (para chamadas ao provedor de embeddings).  

---

### 4.3 Agent de Relatório / Reporting Agent  
- **Nome do Agente / Agent Name:**  
  ```
  report_generator
  ```  
- **Responsabilidade / Responsibility:**  
  - Consumir resultados de avaliação (`evaluation_results.json`).  
  - Gerar relatórios em Markdown (`coverage_report.md`) e HTML (`coverage_report.html`).  
  - Inserir cabeçalho padrão, sumário automático e seções de métricas.  
- **Código de Instanciação / Instantiation Code:**  
  ```python
  from codex_agents import ReportGeneratorAgent

  report_agent = ReportGeneratorAgent(
      output_dir="reports/",
      template_path="templates/report_template.md"
  )
  ```  
- **Parâmetros de Inicialização / Initialization Parameters:**  
  | Parâmetro       | Tipo   | Descrição                                | Padrão            |
  |-----------------|--------|------------------------------------------|-------------------|
  | `output_dir`    | string | Diretório onde salvará os relatórios      | `"reports/"`      |
  | `template_path` | string | Caminho para um arquivo template em Markdown | `"templates/report_template.md"` |

- **Métodos Principais / Main Methods:**  
  1. `generate_markdown(evaluation_json: str) -> str`  
     - _Entrada:_ Caminho para JSON com resultados (`evaluation_results.json`).  
     - _Saída:_ String contendo todo o conteúdo em Markdown.  
  2. `generate_html(evaluation_json: str) -> str`  
     - _Entrada:_ Mesma do método acima.  
     - _Saída:_ String em HTML formatado.  

---

## 5. Exemplos de Uso / Usage Examples  

### 5.1 Exemplo de Chamada via CLI para AgentA  
```bash
# Analisando documentação consolidate.md com DocumentationAnalyzerAgent:
python main.py analyze-doc --input docs/consolidated.md --output reports/analysis.json
```  
- _Explicação:_  
  - `main.py analyze-doc` invoca o DocumentationAnalyzerAgent.  
  - `--input` aponta para o Markdown consolidado.  
  - `--output` indica onde salvar o JSON de saída.  

### 5.2 Pipeline Completo / Full Pipeline Example  
```bash
# 1. Consolida os arquivos Markdown
docs-cli merge docs/ --output_file corpus_consolidated.md

# 2. Extrai dados estruturados
docs-cli extract --input_file corpus_consolidated.md --output_file raw_docs.json

# 3. Gera embeddings (utilizando EmbeddingsGeneratorAgent internamente)
docs-cli generate_embeddings --input_file raw_docs.json --output_file embeddings.json

# 4. Avalia cobertura (usando DocumentationAnalyzerAgent)
docs-cli evaluate qa-data.csv embeddings.json --output_file evaluation_results.json

# 5. Gera relatório em Markdown e HTML (usando ReportGeneratorAgent)
docs-cli report_md --input_file evaluation_results.json --output_file coverage_report.md
docs-cli report_html --input_file evaluation_results.json --output_file coverage_report.html
```  
- _Observações / Notes:_  
  - Verifique a disponibilidade das chaves de API antes de executar cada etapa.  
  - Em cada chamada, o agente apropriado é instanciado segundo a definição em Agents.md.  

---

## 6. Notas e Melhores Práticas / Notes & Best Practices  
- **Versionamento de Agents.md**  
  - Mantenha uma seção de changelog ao final do arquivo (ver seção 7) para registrar adições e alterações em agentes.  
- **Separação de Responsabilidades**  
  - Cada agente deve ter uma única responsabilidade (“Single Responsibility Principle”). Se um agente começar a crescer demais, considere fatiar sua lógica em sub-agentes.  
- **Segurança**  
  - Nunca comite chaves de API ou tokens sensíveis no repositório. Use `.gitignore` para arquivos de configuração local (por ex., `.env`).  
- **Logs e Monitoramento**  
  - Configure níveis de log (INFO, DEBUG, ERROR) dentro de cada agente para facilitar o diagnóstico de falhas em produção.  
- **Testes Unitários**  
  - Para cada agente, crie testes que cubram:  
    1. Respostas mockadas do Codex (usar fixtures).  
    2. Cenários com respostas vazias ou erros de rede.  
    3. Geração de relatórios em formatos esperados.  
- **Padronização de Nomes / Naming Conventions**  
  - Siga um padrão consistente para identificar agentes, por exemplo:  
    - `documentation_analyzer`  
    - `embeddings_generator`  
    - `report_generator`  

---

## 7. Changelog / Histórico de Alterações  
| Data       | Versão | Descrição da Mudança                                        | Autor         |
|------------|--------|-------------------------------------------------------------|---------------|
| 2025-06-04 | 1.0    | Criação inicial de Agents.md contendo 3 definições de agente | Paulo Duarte  |
| 2025-06-10 | 1.1    | Adicionado Agent de Reporting e seção de Notas e Best Practices | Paulo Duarte  |
| `YYYY-MM-DD` | X.Y  | Breve descrição da mudança                                   | Seu Nome      |

---

## 8. Exemplos de Teste / [Opcional] Test Examples  
> _Esta seção é opcional, mas recomendada para demonstrar fluxos de teste dos agentes._  

### 8.1 Teste de `DocumentationAnalyzerAgent`  
- **Entrada de Exemplo / Sample Input:**  
  ```jsonc
  {
    "markdown_text": "# Título Sem Seção

Este é um texto de exemplo sem subtítulos.
"
  }
  ```  
- **Saída Esperada / Expected Output (JSON):**  
  ```jsonc
  {
    "summary": "Este documento apresenta um único título sem seções auxiliares...",
    "recommendations": [
      "Adicionar subtítulos para organizar o conteúdo.",
      "Inserir exemplos de código na seção apropriada."
    ]
  }
  ```  

### 8.2 Teste de `EmbeddingsGeneratorAgent`  
- **Entrada de Exemplo / Sample Input (`raw_docs.json`):**  
  ```jsonc
  {
    "chunks": [
      { "id": 1, "text": "Introdução sobre a ferramenta." },
      { "id": 2, "text": "Detalhes técnicos do módulo de geração." }
    ]
  }
  ```  
- **Comando de Teste / Test Command:**  
  ```bash
  python - << 'EOF'
  from codex_agents import EmbeddingsGeneratorAgent
  agent = EmbeddingsGeneratorAgent(api_key="dummy", model="text-embedding-ada-002", batch_size=1)
  vectors = agent.batch_generate(["Texto A", "Texto B"])
  print(type(vectors), len(vectors))  # Deve ser lista de listas de floats
  EOF
  ```  

---

## 9. Formato de Saída / Output Format  
Sempre utilize UTF-8 para arquivos Markdown.  
- **Linting / Validation:** Use `vale` ou `markdownlint` para verificar estilo e ortografia.  
- **Estrutura de Títulos / Heading Structure:**  
  1. `#` — Nome do agente ou título principal (não repetido dentro do Agents.md; use somente no topo se for dividido em vários arquivos).  
  2. `##` — Seções principais (Overview, Environment Setup, Agent Definitions, etc.).  
  3. `###` — Subseções (cada agente, parâmetros, exemplos).  
  4. Listas e tabelas para detalhar parâmetros e métodos.  

---

## 10. Exemplos do Mundo Real / [Opcional] Real-World Examples  
> (_Se desejar, adicione 1–2 casos completos ilustrando como múltiplos agentes cooperam em um cenário específico._)

### 10.1 Pipeline de Análise e Relatório para Documentação de API  
1. **Merge & Extract**  
   - `docs-cli merge api-docs/ --output_file consolidated_api.md`  
   - `docs-cli extract --input_file consolidated_api.md --output_file raw_doc.json`  
2. **Geração de Embeddings**  
   - `python main.py generate-embeddings --input raw_doc.json --output embeddings.json`  
3. **Avaliação de Cobertura**  
   - `python docs-tc.py evaluate --qa qa-api.csv --embeddings embeddings.json --output eval_results.json`  
4. **Geração de Relatórios**  
   - `python docs-tc.py report-md --input eval_results.json --output api_coverage.md`  
   - `python docs-tc.py report-html --input eval_results.json --output api_coverage.html`  

> (_No cenário acima, `docs-tc.py` detecta automaticamente quais agentes chamar, conforme definido em Agents.md._)

---

### Notas Finais / Final Notes  
- Utilize “senhasegura” para nomear seus projetos ou repositórios internos, se relevante.  
- Ao referir-se a menus suspensos em interfaces de usuário, utilize “dropdown menu” (sem hífen), conforme padrão de UI.  
