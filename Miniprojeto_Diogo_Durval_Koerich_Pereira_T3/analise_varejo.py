"""Mini-Projeto Avaliativo - Análise Exploratória da Base Varejo.

Aluno: Diogo Durval Koerich Pereira
Turma: T3

O programa lê a base compactada ou o CSV descompactado, diagnostica problemas
de qualidade, realiza a limpeza mínima, calcula estatísticas descritivas e
gera agrupamentos e gráficos. Todo o processamento é reproduzível com pandas.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


COLUNAS_ESPERADAS = [
    "DATA",
    "CO_ID",
    "CL_ID",
    "CL_GENERO",
    "CL_EC",
    "CL_FHL",
    "CL_SEG",
    "PR_ID",
    "PR_CAT",
    "PR_NOME",
]

COLUNAS_NUMERICAS = ["CO_ID", "CL_ID", "CL_EC", "CL_FHL", "PR_ID"]
COLUNAS_OBRIGATORIAS = ["DATA", "CO_ID", "CL_ID", "PR_ID"]


def inteiro_br(valor: int | float) -> str:
    """Formata um inteiro com ponto como separador de milhares."""
    return f"{int(valor):,}".replace(",", ".")


class Relatorio:
    """Exibe mensagens no terminal e também as guarda para um arquivo TXT."""

    def __init__(self) -> None:
        self.linhas: list[str] = []

    def escrever(self, texto: object = "") -> None:
        linha = str(texto)
        print(linha)
        self.linhas.append(linha)

    def salvar(self, caminho: Path) -> None:
        caminho.write_text("\n".join(self.linhas) + "\n", encoding="utf-8")


def argumentos() -> argparse.Namespace:
    """Define parâmetros opcionais para execução no VS Code ou Colab."""
    pasta_projeto = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="AED da base de varejo")
    parser.add_argument(
        "--arquivo",
        type=Path,
        default=pasta_projeto / "dados" / "Base Varejo.csv.zip",
        help="Caminho do CSV ou ZIP com um único CSV.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=pasta_projeto / "resultados",
        help="Pasta em que serão gravados os resultados.",
    )
    return parser.parse_args()


def carregar_base(caminho: Path, relatorio: Relatorio) -> pd.DataFrame:
    """Carrega o arquivo separado por ponto e vírgula, inclusive dentro de ZIP."""
    if not caminho.exists():
        alternativas = [
            Path("Base Varejo.csv.zip"),
            Path("Base Varejo.csv"),
            Path("Varejo.csv"),
        ]
        caminho = next((item for item in alternativas if item.exists()), caminho)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Base não encontrada em: {caminho}. "
            "Use --arquivo para informar o caminho correto."
        )

    relatorio.escrever("=" * 72)
    relatorio.escrever("1. CARREGAMENTO E ESTRUTURA ORIGINAL")
    relatorio.escrever("=" * 72)
    relatorio.escrever(f"Arquivo: {caminho}")

    # O arquivo fornecido usa ';'. low_memory=False evita inferências parciais.
    df = pd.read_csv(caminho, sep=";", encoding="utf-8", low_memory=False)

    relatorio.escrever(f"Número de registros: {inteiro_br(len(df))}")
    relatorio.escrever(f"Número de colunas: {df.shape[1]}")
    relatorio.escrever("Colunas e tipos de dados:")
    relatorio.escrever(df.dtypes.to_string())

    ausentes = sorted(set(COLUNAS_ESPERADAS) - set(df.columns))
    if ausentes:
        raise ValueError(f"Colunas obrigatórias ausentes na base: {ausentes}")

    return df


def diagnosticar_base(df: pd.DataFrame, relatorio: Relatorio) -> dict[str, int | float]:
    """Reporta nulos, colunas vazias, duplicatas e inconsistências básicas."""
    relatorio.escrever()
    relatorio.escrever("=" * 72)
    relatorio.escrever("2. DIAGNÓSTICO DE QUALIDADE")
    relatorio.escrever("=" * 72)

    perfil_nulos = pd.DataFrame(
        {
            "nulos": df.isna().sum(),
            "percentual": (df.isna().mean() * 100).round(2),
        }
    )
    relatorio.escrever("Valores nulos por coluna:")
    relatorio.escrever(perfil_nulos.to_string())

    colunas_vazias = [coluna for coluna in df.columns if df[coluna].isna().all()]
    duplicatas = int(df.duplicated().sum())
    taxa_duplicatas = duplicatas / len(df) * 100 if len(df) else 0.0

    datas_convertidas = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors="coerce")
    datas_invalidas = int(datas_convertidas.isna().sum())

    categoria_normalizada = df["PR_CAT"].astype("string").str.strip().str.upper()
    categorias_nao_informadas = int(
        (categoria_normalizada.isna() | categoria_normalizada.isin({"", "#N/D", "#N/A", "N/D", "N/A"})).sum()
    )

    relatorio.escrever()
    relatorio.escrever(f"Colunas 100% vazias: {colunas_vazias}")
    relatorio.escrever(
        f"Linhas totalmente duplicadas: {inteiro_br(duplicatas)} ({taxa_duplicatas:.2f}%)"
    )
    relatorio.escrever(f"Datas inválidas ou vazias: {inteiro_br(datas_invalidas)}")
    relatorio.escrever(
        "Categorias vazias ou marcadas como #N/D: "
        f"{inteiro_br(categorias_nao_informadas)}"
    )

    return {
        "registros_originais": len(df),
        "colunas_originais": df.shape[1],
        "colunas_totalmente_vazias": len(colunas_vazias),
        "duplicatas": duplicatas,
        "taxa_duplicatas": taxa_duplicatas,
        "datas_invalidas": datas_invalidas,
        "categorias_nao_informadas": categorias_nao_informadas,
    }


def limpar_base(
    df_original: pd.DataFrame, relatorio: Relatorio
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Executa limpeza de nulos, tipos, categorias, IDs e duplicatas."""
    relatorio.escrever()
    relatorio.escrever("=" * 72)
    relatorio.escrever("3. LIMPEZA E REGRAS DE NEGÓCIO")
    relatorio.escrever("=" * 72)

    df = df_original.copy()

    # As colunas Unnamed foram criadas por separadores excedentes no fim das linhas.
    colunas_vazias = [coluna for coluna in df.columns if df[coluna].isna().all()]
    df = df.drop(columns=colunas_vazias)
    relatorio.escrever(f"Colunas 100% vazias removidas: {colunas_vazias}")

    # Remove espaços laterais e transforma strings vazias em nulos reais.
    for coluna in df.select_dtypes(include=["object", "string"]).columns:
        df[coluna] = df[coluna].astype("string").str.strip()
        df[coluna] = df[coluna].replace(r"^\s*$", pd.NA, regex=True)

    # Converte datas e números; valores incompatíveis passam a NaN/NaT.
    df["DATA"] = pd.to_datetime(df["DATA"], format="%d/%m/%Y", errors="coerce")
    for coluna in COLUNAS_NUMERICAS:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    # Categoria é descritiva: ausência não exige apagar a venda.
    marcadores_nulos = {"#N/D", "#N/A", "N/D", "N/A", "NULL", "NONE"}
    mascara_categoria = df["PR_CAT"].isna() | df["PR_CAT"].str.upper().isin(marcadores_nulos)
    categorias_preenchidas = int(mascara_categoria.sum())
    df.loc[mascara_categoria, "PR_CAT"] = "Sem Categoria"

    # Outros atributos descritivos recebem rótulo explícito, preservando a linha.
    for coluna, rotulo in {
        "CL_GENERO": "Não Informado",
        "CL_SEG": "Não Informado",
        "PR_NOME": "Sem Nome",
    }.items():
        df[coluna] = df[coluna].fillna(rotulo)

    # Número de filhos é uma contagem. Se houver ausência, usa-se a moda inteira.
    # A moda mantém o domínio discreto e evita excluir todas as compras do cliente.
    filhos_imputados = int(df["CL_FHL"].isna().sum())
    if filhos_imputados:
        moda_filhos = df["CL_FHL"].mode(dropna=True)
        valor_imputacao = int(moda_filhos.iloc[0]) if not moda_filhos.empty else 0
        df["CL_FHL"] = df["CL_FHL"].fillna(valor_imputacao)

    # Estado civil também é uma categoria codificada. Se faltar, a moda é mais
    # adequada que uma média, que poderia criar um código inexistente.
    estado_civil_imputados = int(df["CL_EC"].isna().sum())
    if estado_civil_imputados:
        moda_estado_civil = df["CL_EC"].mode(dropna=True)
        valor_estado_civil = int(moda_estado_civil.iloc[0]) if not moda_estado_civil.empty else 0
        df["CL_EC"] = df["CL_EC"].fillna(valor_estado_civil)

    # A base fornecida não possui altura, largura, comprimento ou peso. Caso uma
    # versão ampliada possua essas dimensões, elas são convertidas e imputadas
    # pela mediana, método menos sensível a valores extremos.
    candidatas_dimensoes = {
        "ALTURA", "LARGURA", "COMPRIMENTO", "PESO",
        "PR_ALTURA", "PR_LARGURA", "PR_COMPRIMENTO", "PR_PESO",
    }
    dimensoes_existentes = sorted(candidatas_dimensoes.intersection(df.columns))
    dimensoes_imputadas = 0
    for coluna in dimensoes_existentes:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
        quantidade = int(df[coluna].isna().sum())
        if quantidade:
            df[coluna] = df[coluna].fillna(df[coluna].median())
            dimensoes_imputadas += quantidade

    if not dimensoes_existentes:
        relatorio.escrever(
            "Dimensões físicas: a base fornecida não contém colunas de altura, "
            "largura, comprimento ou peso; nenhum valor foi inventado."
        )

    # IDs e data definem a rastreabilidade da venda. Sem eles, a linha não pode
    # ser atribuída corretamente e é removida em vez de receber um valor fictício.
    antes_obrigatorias = len(df)
    df = df.dropna(subset=COLUNAS_OBRIGATORIAS)
    removidas_obrigatorias = antes_obrigatorias - len(df)

    # IDs devem ser inteiros positivos. CL_FHL não pode ser negativo.
    mascara_ids_validos = (
        df["CO_ID"].gt(0) & df["CL_ID"].gt(0) & df["PR_ID"].gt(0)
    )
    ids_invalidos = int((~mascara_ids_validos).sum())
    df = df.loc[mascara_ids_validos].copy()
    df.loc[df["CL_FHL"].lt(0), "CL_FHL"] = pd.NA
    df["CL_FHL"] = df["CL_FHL"].fillna(0)

    for coluna in COLUNAS_NUMERICAS:
        df[coluna] = df[coluna].astype("Int64")

    # Regra do identificador de compra: cada CO_ID deve pertencer a somente um
    # cliente e uma data, embora apareça em várias linhas (um item por linha).
    consistencia_compra = df.groupby("CO_ID").agg(
        datas_distintas=("DATA", "nunique"),
        clientes_distintos=("CL_ID", "nunique"),
    )
    compras_conflitantes = consistencia_compra.index[
        (consistencia_compra["datas_distintas"] > 1)
        | (consistencia_compra["clientes_distintos"] > 1)
    ]
    linhas_compras_conflitantes = int(df["CO_ID"].isin(compras_conflitantes).sum())
    if linhas_compras_conflitantes:
        df = df.loc[~df["CO_ID"].isin(compras_conflitantes)].copy()

    # Uma compra pode ter vários produtos; portanto, CO_ID repetido não é uma
    # duplicata. Só removemos repetições em todas as colunas relevantes.
    antes_duplicatas = len(df)
    subconjunto_duplicata = [coluna for coluna in COLUNAS_ESPERADAS if coluna in df.columns]
    df = df.drop_duplicates(subset=subconjunto_duplicata).reset_index(drop=True)
    duplicatas_removidas = antes_duplicatas - len(df)

    relatorio.escrever(
        "Categorias preenchidas com 'Sem Categoria': "
        f"{inteiro_br(categorias_preenchidas)}"
    )
    relatorio.escrever(
        "Valores de número de filhos imputados pela moda: "
        f"{inteiro_br(filhos_imputados)}"
    )
    relatorio.escrever(
        "Valores de estado civil imputados pela moda: "
        f"{inteiro_br(estado_civil_imputados)}"
    )
    relatorio.escrever(
        "Valores de dimensões físicas imputados pela mediana: "
        f"{inteiro_br(dimensoes_imputadas)}"
    )
    relatorio.escrever(
        "Linhas removidas por ausência de data/ID obrigatório: "
        f"{inteiro_br(removidas_obrigatorias)}"
    )
    relatorio.escrever(
        f"Linhas removidas por IDs não positivos: {inteiro_br(ids_invalidos)}"
    )
    relatorio.escrever(
        "Compras com conflito entre CO_ID, cliente e data: "
        f"{inteiro_br(len(compras_conflitantes))}"
    )
    relatorio.escrever(
        "Linhas pertencentes a compras conflitantes removidas: "
        f"{inteiro_br(linhas_compras_conflitantes)}"
    )
    relatorio.escrever(
        f"Duplicatas exatas removidas: {inteiro_br(duplicatas_removidas)}"
    )
    relatorio.escrever(f"Registros finais: {inteiro_br(len(df))}")
    relatorio.escrever(f"Tipos após a limpeza:\n{df.dtypes.to_string()}")

    resumo = {
        "categorias_preenchidas": categorias_preenchidas,
        "filhos_imputados": filhos_imputados,
        "estado_civil_imputados": estado_civil_imputados,
        "dimensoes_imputadas": dimensoes_imputadas,
        "removidas_obrigatorias": removidas_obrigatorias,
        "ids_invalidos": ids_invalidos,
        "compras_conflitantes": len(compras_conflitantes),
        "linhas_compras_conflitantes": linhas_compras_conflitantes,
        "duplicatas_removidas": duplicatas_removidas,
        "registros_finais": len(df),
    }
    return df, resumo


def resumir_serie_filhos(serie: pd.Series) -> pd.DataFrame:
    """Resume uma série numérica com todos os parâmetros pedidos na rubrica."""
    moda = serie.mode(dropna=True).tolist()
    valores = {
        "contagem": int(serie.count()),
        "media": float(serie.mean()),
        "mediana": float(serie.median()),
        "desvio_padrao": float(serie.std()),
        "moda": ", ".join(str(int(valor)) for valor in moda),
        "maximo": int(serie.max()),
        "minimo": int(serie.min()),
    }
    return pd.DataFrame(
        [(chave, valor) for chave, valor in valores.items()],
        columns=["estatistica", "valor"],
    )


def calcular_estatisticas_filhos(
    df: pd.DataFrame, relatorio: Relatorio
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcula a estatística exigida e uma visão complementar por cliente."""
    relatorio.escrever()
    relatorio.escrever("=" * 72)
    relatorio.escrever("4. ESTATÍSTICAS DO NÚMERO DE FILHOS")
    relatorio.escrever("=" * 72)

    # A rubrica pede explicitamente as estatísticas da coluna CL_FHL. Portanto,
    # esta é a tabela principal e considera todas as linhas da base limpa.
    estatisticas_coluna = resumir_serie_filhos(df["CL_FHL"])
    relatorio.escrever("Estatísticas exigidas — coluna CL_FHL da base limpa:")
    relatorio.escrever(estatisticas_coluna.to_string(index=False))

    # Como o mesmo cliente aparece em várias compras, também calculamos uma
    # visão complementar com um registro por cliente. Ela evita que clientes
    # frequentes tenham peso maior na interpretação demográfica.
    inconsistentes = int((df.groupby("CL_ID")["CL_FHL"].nunique() > 1).sum())
    filhos_cliente = df.groupby("CL_ID")["CL_FHL"].agg(
        lambda serie: serie.mode().iloc[0]
    )
    estatisticas_cliente = resumir_serie_filhos(filhos_cliente)

    relatorio.escrever()
    relatorio.escrever("Estatísticas complementares — um registro por cliente:")
    relatorio.escrever(
        f"Clientes com valores divergentes de CL_FHL: {inconsistentes} "
        "(nesses casos seria usada a moda do cliente)."
    )
    relatorio.escrever(estatisticas_cliente.to_string(index=False))
    return estatisticas_coluna, estatisticas_cliente


def gerar_agrupamentos(
    df: pd.DataFrame, relatorio: Relatorio
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Produz três padrões: gênero, categoria e evolução mensal."""
    relatorio.escrever()
    relatorio.escrever("=" * 72)
    relatorio.escrever("5. PADRÕES DE AGRUPAMENTO")
    relatorio.escrever("=" * 72)

    por_genero = (
        df.groupby("CL_GENERO", dropna=False)
        .agg(
            volume_itens=("PR_ID", "size"),
            compras_unicas=("CO_ID", "nunique"),
            clientes_unicos=("CL_ID", "nunique"),
        )
        .sort_values("volume_itens", ascending=False)
    )
    por_genero["participacao_itens_pct"] = (
        por_genero["volume_itens"] / por_genero["volume_itens"].sum() * 100
    ).round(2)
    por_genero["itens_por_compra"] = (
        por_genero["volume_itens"] / por_genero["compras_unicas"]
    ).round(2)

    por_categoria = (
        df.groupby("PR_CAT", dropna=False)
        .agg(
            volume_itens=("PR_ID", "size"),
            compras_unicas=("CO_ID", "nunique"),
            clientes_unicos=("CL_ID", "nunique"),
        )
        .sort_values("volume_itens", ascending=False)
    )
    por_categoria["participacao_itens_pct"] = (
        por_categoria["volume_itens"] / por_categoria["volume_itens"].sum() * 100
    ).round(2)

    df_temporal = df.assign(MES=df["DATA"].dt.to_period("M").astype(str))
    por_mes = df_temporal.groupby("MES").agg(
        volume_itens=("PR_ID", "size"),
        compras_unicas=("CO_ID", "nunique"),
        clientes_unicos=("CL_ID", "nunique"),
    )

    relatorio.escrever("Agrupamento 1 — gênero do cliente:")
    relatorio.escrever(por_genero.to_string())
    relatorio.escrever()
    relatorio.escrever("Agrupamento 2 — categoria do produto:")
    relatorio.escrever(por_categoria.to_string())
    relatorio.escrever()
    relatorio.escrever("Agrupamento 3 — evolução mensal (primeiros e últimos meses):")
    relatorio.escrever(pd.concat([por_mes.head(3), por_mes.tail(3)]).to_string())

    return por_genero, por_categoria, por_mes


def gerar_graficos(
    por_genero: pd.DataFrame,
    por_categoria: pd.DataFrame,
    por_mes: pd.DataFrame,
    pasta_saida: Path,
) -> None:
    """Salva visualizações simples e legíveis para apoiar os agrupamentos."""
    plt.style.use("seaborn-v0_8-whitegrid")

    figura, eixo = plt.subplots(figsize=(8, 4.5))
    por_genero["volume_itens"].sort_values().plot.barh(ax=eixo, color="#4472C4")
    eixo.set_title("Volume de itens por gênero do cliente")
    eixo.set_xlabel("Registros de itens")
    eixo.set_ylabel("Gênero")
    figura.tight_layout()
    figura.savefig(pasta_saida / "grafico_genero.png", dpi=150)
    plt.close(figura)

    figura, eixo = plt.subplots(figsize=(9, 5))
    por_categoria["volume_itens"].sort_values().plot.barh(ax=eixo, color="#70AD47")
    eixo.set_title("Volume de itens por categoria")
    eixo.set_xlabel("Registros de itens")
    eixo.set_ylabel("Categoria")
    figura.tight_layout()
    figura.savefig(pasta_saida / "grafico_categorias.png", dpi=150)
    plt.close(figura)

    figura, eixo = plt.subplots(figsize=(11, 4.5))
    por_mes["volume_itens"].plot(ax=eixo, color="#ED7D31", linewidth=2)
    eixo.set_title("Evolução mensal do volume de itens")
    eixo.set_xlabel("Mês")
    eixo.set_ylabel("Registros de itens")
    eixo.tick_params(axis="x", rotation=60)
    figura.tight_layout()
    figura.savefig(pasta_saida / "grafico_evolucao_mensal.png", dpi=150)
    plt.close(figura)


def gerar_conclusoes(
    df: pd.DataFrame,
    diagnostico: dict[str, int | float],
    limpeza: dict[str, int],
    estatisticas_coluna: pd.DataFrame,
    estatisticas_cliente: pd.DataFrame,
    por_genero: pd.DataFrame,
    por_categoria: pd.DataFrame,
    por_mes: pd.DataFrame,
    relatorio: Relatorio,
) -> list[str]:
    """Gera seis conclusões objetivas, incluindo uma limitação remanescente."""
    estat_coluna = estatisticas_coluna.set_index("estatistica")["valor"]
    estat_cliente = estatisticas_cliente.set_index("estatistica")["valor"]
    genero_lider = str(por_genero.index[0])
    categoria_lider = str(por_categoria.index[0])
    mes_pico = str(por_mes["volume_itens"].idxmax())

    conclusoes = [
        (
            f"A base tinha {inteiro_br(diagnostico['registros_originais'])} linhas e "
            f"{int(diagnostico['colunas_originais'])} colunas; "
            f"{int(diagnostico['colunas_totalmente_vazias'])} colunas "
            "totalmente vazias, originadas por separadores excedentes, foram removidas."
        ),
        (
            f"Foram eliminadas {inteiro_br(limpeza['duplicatas_removidas'])} duplicatas exatas "
            f"({float(diagnostico['taxa_duplicatas']):.2f}% da base original), restando "
            f"{inteiro_br(len(df))} registros de itens."
        ),
        (
            f"A categoria ausente foi padronizada como 'Sem Categoria'; após a limpeza, "
            f"ela representa {por_categoria.loc['Sem Categoria', 'participacao_itens_pct']:.2f}% "
            "do volume de itens."
        ),
        (
            f"O gênero {genero_lider} concentrou "
            f"{por_genero.iloc[0]['participacao_itens_pct']:.2f}% dos itens, enquanto "
            f"{categoria_lider} foi a categoria líder, com "
            f"{por_categoria.iloc[0]['participacao_itens_pct']:.2f}%."
        ),
        (
            f"Na coluna CL_FHL, a média foi {float(estat_coluna['media']):.3f}, "
            f"com mediana {float(estat_coluna['mediana']):.0f} e moda "
            f"{estat_coluna['moda']}. Na visão complementar de "
            f"{inteiro_br(float(estat_cliente['contagem']))} clientes únicos, a média foi "
            f"{float(estat_cliente['media']):.3f}. "
            f"O maior volume mensal ocorreu em {mes_pico}."
        ),
        (
            "Limitação remanescente: a base não possui quantidade, preço ou valor monetário. "
            "Assim, 'volume de itens' significa número de linhas após a deduplicação e não "
            "receita ou unidades físicas comprovadas; duplicatas exatas também poderiam "
            "representar várias unidades do mesmo produto, hipótese impossível de confirmar."
        ),
    ]

    relatorio.escrever()
    relatorio.escrever("=" * 72)
    relatorio.escrever("6. CONCLUSÕES")
    relatorio.escrever("=" * 72)
    for numero, conclusao in enumerate(conclusoes, start=1):
        relatorio.escrever(f"{numero}. {conclusao}")

    return conclusoes


def salvar_resultados(
    df: pd.DataFrame,
    estatisticas_coluna: pd.DataFrame,
    estatisticas_cliente: pd.DataFrame,
    por_genero: pd.DataFrame,
    por_categoria: pd.DataFrame,
    por_mes: pd.DataFrame,
    conclusoes: list[str],
    pasta_saida: Path,
) -> None:
    """Grava a base limpa, tabelas analíticas e conclusões em arquivos reutilizáveis."""
    pasta_saida.mkdir(parents=True, exist_ok=True)
    df.to_csv(pasta_saida / "df_limpo.csv", index=False, encoding="utf-8")
    estatisticas_coluna.to_csv(
        pasta_saida / "estatisticas_filhos.csv", index=False, encoding="utf-8"
    )
    estatisticas_cliente.to_csv(
        pasta_saida / "estatisticas_filhos_por_cliente.csv",
        index=False,
        encoding="utf-8",
    )
    por_genero.to_csv(pasta_saida / "agrupamento_genero.csv", encoding="utf-8")
    por_categoria.to_csv(pasta_saida / "agrupamento_categoria.csv", encoding="utf-8")
    por_mes.to_csv(pasta_saida / "agrupamento_mensal.csv", encoding="utf-8")
    (pasta_saida / "conclusoes.txt").write_text(
        "\n".join(f"{i}. {texto}" for i, texto in enumerate(conclusoes, start=1)) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Coordena todas as etapas da análise exploratória."""
    args = argumentos()
    args.saida.mkdir(parents=True, exist_ok=True)
    relatorio = Relatorio()

    df_original = carregar_base(args.arquivo, relatorio)
    diagnostico = diagnosticar_base(df_original, relatorio)
    df_limpo, resumo_limpeza = limpar_base(df_original, relatorio)
    estatisticas_coluna, estatisticas_cliente = calcular_estatisticas_filhos(
        df_limpo, relatorio
    )
    por_genero, por_categoria, por_mes = gerar_agrupamentos(df_limpo, relatorio)
    conclusoes = gerar_conclusoes(
        df_limpo,
        diagnostico,
        resumo_limpeza,
        estatisticas_coluna,
        estatisticas_cliente,
        por_genero,
        por_categoria,
        por_mes,
        relatorio,
    )
    salvar_resultados(
        df_limpo,
        estatisticas_coluna,
        estatisticas_cliente,
        por_genero,
        por_categoria,
        por_mes,
        conclusoes,
        args.saida,
    )
    gerar_graficos(por_genero, por_categoria, por_mes, args.saida)
    relatorio.salvar(args.saida / "relatorio_execucao.txt")

    print("\nAnálise concluída.")
    print(f"Resultados gravados em: {args.saida.resolve()}")


if __name__ == "__main__":
    main()
