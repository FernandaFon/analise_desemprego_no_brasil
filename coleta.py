"""
coleta.py
Funções de coleta e limpeza dos dados da API SIDRA/IBGE.
"""

import time
import requests
import pandas as pd
from config import BASE_URL, TABELAS_CONFIG


# ---------------------------------------------------------------------------
# Coleta
# ---------------------------------------------------------------------------

def coletar_tabela(cfg: dict, tentativas: int = 3, espera: float = 2.0) -> pd.DataFrame:
    """
    Faz o request à API SIDRA e retorna um DataFrame limpo.

    Parâmetros
    ----------
    cfg : dict
        Entrada do TABELAS_CONFIG para a tabela desejada.
    tentativas : int
        Número de tentativas em caso de falha de rede.
    espera : float
        Segundos de espera entre tentativas.

    Retorno
    -------
    pd.DataFrame com colunas já renomeadas e taxa convertida para float.
    """
    url = (
        f"{BASE_URL}"
        f"/t/{cfg['tabela']}"
        f"/{cfg['nivel']}/{cfg['local']}"
        f"/v/{cfg['variavel']}"
        f"/p/all"
        f"{cfg['classificacao']}"
    )

    for tentativa in range(1, tentativas + 1):
        try:
            print(f"  → Consultando: {url}")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            break
        except requests.RequestException as e:
            print(f"  ✗ Tentativa {tentativa}/{tentativas} falhou: {e}")
            if tentativa == tentativas:
                raise
            time.sleep(espera)

    dados = r.json()
    if len(dados) <= 1:
        raise ValueError(f"API retornou sem dados para a tabela {cfg['tabela']}.")

    # Primeira linha é o cabeçalho com nomes dos campos — descartamos
    df = pd.DataFrame(dados[1:])

    # Renomeia apenas as colunas mapeadas, ignora as demais
    df = df.rename(columns=cfg["renomear"])

    # Mantém só as colunas que foram renomeadas (descarta NC, NN, MC, MN, D2C, etc.)
    colunas_uteis = list(cfg["renomear"].values())

    colunas_presentes = [c for c in colunas_uteis if c in df.columns]
    df = df[colunas_presentes].copy()    

    return df


def coletar_todos(config: dict = None) -> dict[str, pd.DataFrame]:
    """
    Coleta todas as tabelas definidas em TABELAS_CONFIG.

    Retorno
    -------
    dict no formato {"geral": df_geral, "sexo": df_sexo, ...}
    """
    if config is None:
        config = TABELAS_CONFIG

    dfs = {}
    for nome, cfg in config.items():
        print(f"\n[{nome.upper()}] {cfg['descricao']}")
        try:
            dfs[nome] = coletar_tabela(cfg)
            print(f"  ✓ {len(dfs[nome])} linhas coletadas.")
        except Exception as e:
            print(f"  ✗ Erro ao coletar '{nome}': {e}")
            dfs[nome] = pd.DataFrame()   # DataFrame vazio para não travar o fluxo

    return dfs


# ---------------------------------------------------------------------------
# Limpeza e padronização
# ---------------------------------------------------------------------------

def limpar_df(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Aplica limpeza padrão a qualquer DataFrame coletado do SIDRA.

    Operações:
    - Converte 'taxa' para float (trata '-' e valores ausentes como NaN)
    - Converte 'periodo_cod' para datetime (ex: '201201' → 2012-Q1)
    - Cria coluna 'ano' para agregações anuais
    - Remove a linha 'Total' da categoria, se necessário
    - Remove linhas com taxa NaN
    """
    df = df.copy()

    # 1. Converte valores numéricos (taxa OU valor)
    if cfg.get("calculo_manual"):
        if "valor" in df.columns:
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    else:
        if "taxa" in df.columns:
            df["taxa"] = pd.to_numeric(df["taxa"], errors="coerce")

    # 2. Converte periodo_cod → datetime trimestral
    if "periodo_cod" in df.columns:
        df["periodo_cod"] = df["periodo_cod"].astype(str)

        # SIDRA costuma retornar trimestre como YYYYTT (ex.: 201201, 201204).
        # Mantém apenas strings de 6 dígitos.
        df = df[df["periodo_cod"].str.match(r"^\d{6}$", na=False)]

        df["ano"] = df["periodo_cod"].str[:4].astype(int)
        # Trimestre vem nos 2 últimos dígitos ("01".."04")
        df["trimestre_num"] = df["periodo_cod"].str[-2:].astype(int)
        # Cria uma data no primeiro mês de cada trimestre (jan, abr, jul, out)
        df["data"] = pd.to_datetime(
            df["ano"].astype(str) + "-" +
            ((df["trimestre_num"] - 1) * 3 + 1).astype(str).str.zfill(2) + "-01"
        )

    # 3. Remove categoria "Total" quando há subcategorias
    col_cat = cfg.get("col_categoria")
    if cfg.get("filtrar_total") and col_cat and col_cat in df.columns:
        df = df[~df[col_cat].str.lower().str.contains("total", na=False)]

    if "taxa" in df.columns:
        df = df.dropna(subset=["taxa"])
    elif "valor" in df.columns:
        df = df.dropna(subset=["valor"])

    # 5. Ordena cronologicamente
    if "data" in df.columns:
        df = df.sort_values("data").reset_index(drop=True)

    return df


def limpar_todos(dfs: dict, config: dict = None) -> dict[str, pd.DataFrame]:
    """
    Aplica limpar_df() a cada DataFrame do dicionário.
    """
    if config is None:
        config = TABELAS_CONFIG

    return {
        nome: limpar_df(df, config[nome])
        for nome, df in dfs.items()
        if not df.empty
    }

# ---------------------------------------------------------------------------
# Cálculo de indicadores
# ---------------------------------------------------------------------------

def calcular_taxa(df: pd.DataFrame, col_categoria: str) -> pd.DataFrame:
    """
    Calcula a taxa de desocupação a partir de valores absolutos.

    Fórmula:
    taxa = desocupados / (ocupados + desocupados) * 100
    """
    df = df.copy()

    if "Variável" not in df.columns or "valor" not in df.columns:
        raise ValueError("DataFrame precisa conter as colunas 'Variável' e 'valor'.")

    # Filtra apenas valores absolutos (evita coeficientes de variação e percentuais)
    var = df["Variável"].astype(str)
    is_cv = var.str.contains("coeficiente de variação", case=False, na=False)
    is_pct = var.str.contains("distribuição percentual|percentual", case=False, na=False)
    base = df[~is_cv & ~is_pct].copy()

    # Mantém apenas as contagens absolutas de ocupados/desocupados na semana de referência.
    # (Isso evita misturar "taxas", "níveis" e outras variáveis derivadas quando existirem.)
    ocupados = base[
        base["Variável"].str.contains(r"^Pessoas.*ocupadas na semana de referência$", case=False, na=False)
    ].copy()
    desocupados = base[
        base["Variável"].str.contains(r"^Pessoas.*desocupadas na semana de referência$", case=False, na=False)
    ].copy()

    merged = ocupados.merge(
        desocupados,
        on=["periodo_cod", col_categoria],
        suffixes=("_ocupados", "_desocupados"),
        how="inner",
    )

    merged["taxa"] = (
        merged["valor_desocupados"] /
        (merged["valor_desocupados"] + merged["valor_ocupados"])
    ) * 100

    # Normaliza para o mesmo "shape" esperado pelos gráficos
    out = merged[[
        "periodo_cod",
        col_categoria,
        "trimestre_desocupados",
        "valor_ocupados",
        "valor_desocupados",
        "taxa",
    ]].rename(columns={"trimestre_desocupados": "trimestre"})

    out["periodo_cod"] = out["periodo_cod"].astype(str)
    out = out[out["periodo_cod"].str.match(r"^\d{6}$", na=False)].copy()
    out["ano"] = out["periodo_cod"].str[:4].astype(int)
    out["trimestre_num"] = out["periodo_cod"].str[-2:].astype(int)
    out["data"] = pd.to_datetime(
        out["ano"].astype(str) + "-" +
        ((out["trimestre_num"] - 1) * 3 + 1).astype(str).str.zfill(2) + "-01"
    )
    out = out.sort_values("data").reset_index(drop=True)

    return out
