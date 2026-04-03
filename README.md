# Gestor de Avaliações e Performance IA

Sistema de suporte à decisão que utiliza Agentes de IA para automatizar o cruzamento de dados entre performance de funcionários, políticas de remuneração e histórico financeiro (ERP). O objetivo é garantir recomendações de mérito baseadas em dados e conformidade com as regras corporativas.

## Definição do Problema e Público

### Público-Alvo

Gestores de Recursos Humanos (RH), Business Partners e Analistas de Cargos e Salários (Compensation & Benefits).

### O Problema

Em organizações com processos manuais, a revisão salarial sofre com:

    - Erros de Compliance: Concessão de aumentos sem respeitar o interstício mínimo exigido pela empresa.

    - Inconsistência Analítica: Dificuldade em comparar notas de performance de diferentes áreas sob o mesmo critério.

    - Sobrecarga de Dados: Necessidade de consultar simultaneamente planilhas de notas, documentos PDF de políticas e bancos de dados de histórico, o que gera lentidão e fadiga na tomada de decisão.

## Solução Proposta

Uma aplicação baseada em IA Agentica que atua como um Auditor de Performance. O sistema utiliza ferramentas específicas para acessar diferentes fontes de dados e aplicar lógica matemática rigorosa, eliminando a subjetividade e o erro humano no processamento inicial das informações.

## KPIs de Sucesso

### Métricas de Negócio
    
    - Tempo de Processamento: Redução do tempo necessário para gerar uma prévia de elegibilidade de aumentos saláriais e bônus de performance.

    - Conformidade de Regras: Redução do erro humano e subjetividade no cruzamento de dados com a política da empresa.

    - Transparência: Capacidade de justificar cada recomendação com os dados brutos extraídos das ferramentas.

### Métricas Técnicas

    - Precisão Decimal: Verificação de que a IA processou as médias com até 3 casas decimais sem arredondamentos indevidos.

    - Taxa de Sucesso de Execução: Percentual de conclusão bem-sucedida das tarefas de leitura de Arquivos externos e banco de dados sem falhas de conexão.

## Plano de Validação

Hipótese: O agente de IA consegue realizar a triagem de elegibilidade com a mesma precisão de um analista sênior, em menos de 10% do tempo original.

    - Fase 1 (Interna): Teste com 50 perfis fictícios variando entre elegíveis e inelegíveis para validar os filtros de data e nota.

    - Fase 2 (Usuários Reais): Apresentação dos relatórios gerados para 3 gestores de RH para validação da utilidade das justificativas apresentadas.

    - Fase 3 (Mensuração): Comparação do tempo gasto na revisão manual versus a revisão assistida pela ferramenta.

## Decisões Técnicas

A solução foi construída utilizando os seguintes pilares e ferramentas:

    - Interpretador Python 3.12: Escolhido para suporte às versões mais recentes das bibliotecas de IA e melhor gerenciamento de tipos.

    - ChatOpenAI (gpt-4o-mini): Configurado com temperature 0.1 para garantir que a saída seja determinística e matemática, evitando alucinações em cálculos de datas e médias.

    - SQLite (ERP Simulado): Banco de dados local para persistência do histórico financeiro, permitindo consultas SQL reais de forma portátil.

    - Pandas com Float Format: Leitura e formatação rigorosa de informações para garantir que o LLM receba dados mais precisos.

    - LangChain Agents: Estrutura que permite ao modelo decidir dinamicamente qual ferramenta consultar com base na necessidade da pergunta.

    - RAG (Retrieval-Augmented Generation): Aplicado para a leitura da Política de Remuneração em PDF. Em vez de treinar um modelo com as regras da empresa, o agente recupera o contexto relevante do documento em tempo real, garantindo que a resposta esteja sempre fundamentada na norma vigente.

    - Tool Use (Agentes): O modelo não apenas gera texto, mas executa ações. Foram desenvolvidas ferramentas customizadas para consulta de bancos de dados SQL e manipulação de DataFrames, permitindo que a IA interaja com o ecossistema de dados da empresa de forma estruturada.

    - Cadeia de Pensamento (Chain-of-Thought): O prompt foi desenhado para forçar o modelo a decompor o problema (Cálculo de data > Comparação de nota > Validação de bônus) antes de emitir o veredito final.

## Trade-offs

    - Custo vs. Latência: O modelo mini foi escolhido pelo baixo custo e alta velocidade, embora exija um System Prompt mais descritivo para manter a lógica comparada a modelos maiores.

    - Local vs. Cloud: O banco SQLite local facilita o desenvolvimento e prototipação, mas limita a escalabilidade e o acesso multiusuário que um banco como PostgreSQL ofereceria.

## Expansão e Próximos Passos

Após a validação da hipótese inicial, o projeto prevê as seguintes evoluções para se tornar um produto de prateleira:

### Interface do Usuário (UI/UX)

Substituição da interface de linha de comando (CLI) por um Dashboard Administrativo (utilizando Streamlit ou React). O objetivo é permitir que o gestor de RH visualize o "Caminho do Pensamento" da IA de forma gráfica, facilitando auditorias rápidas.

### Conectividade e Padrão MCP (Model Context Protocol)

Para escalar a solução em ambientes corporativos complexos, a arquitetura evoluirá para o padrão MCP. Isso permitirá:

    - Conexão plug-and-play com bancos de dados robustos (PostgreSQL, Oracle, SAP).

    - Criação de conectores padronizados que podem ser reutilizados por outros agentes da companhia.

    - Maior segurança na camada de transporte de dados entre o ERP oficial e o modelo de linguagem.

## Como Executar

### Configuração de Ambiente

1. Instale as dependências:
```bash
pip install -r src/gestor/requirements.txt
```

2. Configure o arquivo .env na pasta src/gestor/ com as chaves e caminhos necessários.

3. Inicialize o banco de dados simulado:
```bash
python src/gestor/setup_db.py
```
### Execução

Inicie a aplicação principal:

```bash
python src/gestor/app.py
```