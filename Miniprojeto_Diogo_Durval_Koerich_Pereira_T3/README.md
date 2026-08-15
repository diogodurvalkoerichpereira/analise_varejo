# Mini-Projeto — Análise Exploratória da Base Varejo

**Disciplina:** Visualização de Dados e Business Intelligence  
**Módulo:** 1 — Semana 07  
**Aluno:** Diogo Durval Koerich Pereira  
**Turma:** T3

## Objetivo

Este projeto realiza uma Análise Exploratória de Dados (AED) da base **Varejo** com Python e pandas. O processo identifica problemas de qualidade, aplica regras de limpeza, gera as estatísticas da quantidade de filhos dos clientes e explora padrões de compras por gênero, categoria e mês.

## Estrutura do projeto

```text
Miniprojeto_Diogo_Durval_Koerich_Pereira_T3/
├── analise_varejo.py
├── README.md
├── README_Diogo_Durval_Koerich_Pereira_T3.md
├── requirements.txt
├── dados/
│   └── Base Varejo.csv.zip
└── resultados/
    ├── df_limpo.csv
    ├── estatisticas_filhos.csv
    ├── estatisticas_filhos_por_cliente.csv
    ├── agrupamento_genero.csv
    ├── agrupamento_categoria.csv
    ├── agrupamento_mensal.csv
    ├── conclusoes.txt
    ├── relatorio_execucao.txt
    └── grafico_*.png
```

## Como executar

Requisitos: Python 3.10 ou superior.

```bash
python -m venv .venv
```

No Windows, ative o ambiente e instale as bibliotecas:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python analise_varejo.py
```

No Linux ou macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python analise_varejo.py
```

O script também aceita caminhos personalizados:

```bash
python analise_varejo.py --arquivo "dados/Base Varejo.csv.zip" --saida "resultados"
```

## Dicionário das colunas

| Coluna | Interpretação utilizada |
|---|---|
| `DATA` | Data da compra |
| `CO_ID` | Identificador da compra |
| `CL_ID` | Identificador do cliente |
| `CL_GENERO` | Gênero do cliente |
| `CL_EC` | Código do estado civil |
| `CL_FHL` | Número de filhos do cliente |
| `CL_SEG` | Segmento do cliente |
| `PR_ID` | Identificador do produto |
| `PR_CAT` | Categoria do produto |
| `PR_NOME` | Nome do produto |

## Etapas de ETL e qualidade dos dados

**Extração:** o arquivo é lido de forma estruturada com `pandas.read_csv()`, usando o separador `;`. O pandas também lê diretamente o CSV contido no ZIP.

**Transformação:** as colunas totalmente vazias são removidas; espaços são padronizados; datas e números são convertidos; marcadores `#N/D` da categoria são tratados como ausência; IDs e a regra de identificação da compra são validados; e duplicatas exatas são eliminadas.

**Carga:** a base transformada é gravada em `resultados/df_limpo.csv`, acompanhada de tabelas de estatísticas, agrupamentos, gráficos e relatório textual.

A qualidade dos dados é essencial porque nulos, tipos incorretos e duplicatas podem alterar contagens e conclusões. As escolhas de tratamento foram:

- categorias ausentes são preenchidas com **Sem Categoria**, pois apagar a linha eliminaria uma venda válida;
- datas ou IDs obrigatórios ausentes são removidos, pois não é correto inventar a identificação da compra;
- eventual ausência em `CL_FHL` é imputada pela moda, preservando o caráter inteiro da variável;
- uma repetição de `CO_ID` não é eliminada, pois uma compra possui vários produtos; somente linhas iguais em todas as colunas relevantes são consideradas duplicatas;
- a base fornecida não possui altura, largura, comprimento ou peso. Portanto, dimensões físicas não foram inventadas; o código documenta como as trataria pela mediana se estivessem presentes.

## Resultados da base analisada

- A base original possui **830.000 registros e 14 colunas**. Quatro colunas `Unnamed` estavam 100% vazias devido a separadores excedentes e foram removidas.
- Foram removidas **96.553 duplicatas exatas (11,63%)**, restando **733.447 registros de itens**.
- Todas as datas foram convertidas com sucesso; os **18.471 identificadores de compra** respeitam a regra de pertencer a um único cliente e a uma única data.
- Os **3.650 registros `#N/D`** foram identificados antes da deduplicação e padronizados como `Sem Categoria`. Após a limpeza, são 3.228 registros, ou **0,44%** dos itens.

## Estatísticas do número de filhos — requisito da rubrica

O arquivo `estatisticas_filhos.csv` contém as estatísticas calculadas diretamente sobre a coluna `CL_FHL` da base limpa, como solicitado no edital.

| Estatística | Resultado |
|---|---:|
| Contagem | 733.447 registros |
| Média | 1,146 |
| Mediana | 0 |
| Desvio padrão | 1,4169 |
| Moda | 0 |
| Máximo | 4 |
| Mínimo | 0 |

Como análise complementar, `estatisticas_filhos_por_cliente.csv` calcula os mesmos parâmetros usando um registro por cliente, evitando que clientes com mais compras tenham peso maior na leitura demográfica. Nessa visão, há 1.000 clientes, média 1,136, mediana 0, desvio padrão 1,4133, moda 0, máximo 4 e mínimo 0.

## Agrupamentos e insights

1. O gênero feminino representa **382.427 itens (52,14%)** e 9.615 compras únicas, superando o gênero masculino, com 351.020 itens (47,86%) e 8.856 compras.
2. **Alimentos** lidera as categorias, com **384.197 itens (52,38%)**. Em seguida aparecem Higiene (18,77%) e Limpeza (17,54%).
3. Na coluna `CL_FHL`, a mediana e a moda são zero, embora a média seja 1,146. Na visão por cliente único, a média é 1,136; ambas chegam ao máximo de quatro filhos.
4. O maior volume mensal ocorreu em **outubro de 2021**, com 28.575 registros de itens após a limpeza.
5. Os marcadores de categoria ausente são pouco numerosos após o tratamento (0,44%), mas devem continuar sendo monitorados para não prejudicar análises por categoria.
6. A base não contém preço, valor ou quantidade. Logo, os agrupamentos medem ocorrências de itens e compras únicas, não faturamento. Além disso, algumas linhas idênticas podem representar várias unidades legítimas do mesmo produto; sem uma coluna de quantidade, essa hipótese não pode ser confirmada.

## Visualizações geradas

Após executar o script, os gráficos ficam em `resultados/`:

- `grafico_genero.png` — comparação do volume de itens por gênero;
- `grafico_categorias.png` — ranking das categorias;
- `grafico_evolucao_mensal.png` — evolução mensal de 2019 a 2022.

## Atendimento aos critérios de avaliação

| Critério | Evidência no projeto |
|---|---|
| Versionamento e documentação | `README.md`, README individual e estrutura pronta para repositório público |
| Leitura estruturada do CSV | função `carregar_base()` com `pandas.read_csv()` |
| Nulos e condicionais | diagnóstico por coluna, `Sem Categoria`, modas e justificativas documentadas |
| Regras de negócio e datas | conversão com `pd.to_datetime()` e validação de `CO_ID` por cliente/data |
| Padrões de agrupamento | gênero, categoria e evolução mensal com `groupby()` |
| Estatísticas de filhos | contagem, média, mediana, desvio padrão, moda, máximo e mínimo |
| Relatório final | seis conclusões no README, no terminal e em `resultados/conclusoes.txt` |

## Fonte dos dados

Base Varejo, disponibilizada no Kaggle: <https://www.kaggle.com/datasets/namespaiva/base-varejo>
