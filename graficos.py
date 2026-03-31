"""
graficos.py
Funções de visualização para cada recorte da análise.
Todas retornam uma figura Plotly que pode ser exibida no notebook
ou exportada com fig.write_image() / fig.write_html().
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import PALETA


# ---------------------------------------------------------------------------
# Helpers compartilhados
# ---------------------------------------------------------------------------

LAYOUT_BASE = dict(
    font_family="'IBM Plex Sans', sans-serif",
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=60, r=40, t=80, b=60),
    xaxis=dict(showgrid=False, showline=True, linecolor="#ddd"),
    yaxis=dict(showgrid=True, gridcolor="#f0f0f0", showline=False, ticksuffix="%"),
)


def _layout_base_sem_eixos_margin():
    """Evita conflito ao passar margin/xaxis/yaxis explícitos depois do spread."""
    return {
        k: v
        for k, v in LAYOUT_BASE.items()
        if k not in ("xaxis", "yaxis", "margin")
    }


def _aplicar_layout(fig, titulo, subtitulo="Fonte: IBGE — PNAD Contínua Trimestral"):
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(
            text=f"<b>{titulo}</b><br><sup style='color:#888'>{subtitulo}</sup>",
            font_size=16,
            x=0.02,
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# 1. Linha temporal — desemprego geral
# ---------------------------------------------------------------------------

def grafico_linha_geral(df_geral: pd.DataFrame) -> go.Figure:
    """
    Linha temporal da taxa de desocupação geral no Brasil (2012–presente).
    Marca em destaque o pico histórico (pandemia 2020) e o valor mais recente.
    """
    df = df_geral.copy()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["data"], y=df["taxa"],
        mode="lines",
        name="Taxa de desocupação",
        line=dict(color=PALETA[0], width=2.5),
        fill="tozeroy",
        fillcolor=f"rgba(29,158,117,0.08)",
        hovertemplate="%{x|%b/%Y}: <b>%{y:.1f}%</b><extra></extra>",
    ))

    # Marca o pico
    idx_pico = df["taxa"].idxmax()
    pico = df.loc[idx_pico]
    fig.add_annotation(
        x=pico["data"], y=pico["taxa"],
        text=f"<b>Pico: {pico['taxa']:.1f}%</b><br>{pico['trimestre']}",
        showarrow=True, arrowhead=2, arrowcolor="#D85A30",
        font=dict(size=11, color="#D85A30"),
        bgcolor="white", bordercolor="#D85A30", borderwidth=1,
        ax=40, ay=-40,
    )

    # Marca o valor mais recente
    ultimo = df.iloc[-1]
    fig.add_annotation(
        x=ultimo["data"], y=ultimo["taxa"],
        text=f"<b>{ultimo['taxa']:.1f}%</b><br>({ultimo['trimestre']})",
        showarrow=True, arrowhead=2, arrowcolor=PALETA[0],
        font=dict(size=11, color=PALETA[0]),
        bgcolor="white", bordercolor=PALETA[0], borderwidth=1,
        ax=-60, ay=-40,
    )

    # Faixa da pandemia
    fig.add_vrect(
        x0="2020-01-01", x1="2021-06-01",
        fillcolor="#FEE9E1", opacity=0.5, layer="below", line_width=0,
        annotation_text="Pandemia", annotation_position="top left",
        annotation_font_size=10, annotation_font_color="#D85A30",
    )

    _aplicar_layout(fig, "Taxa de desocupação no Brasil (2012–2025)")
    fig.update_yaxes(range=[0, df["taxa"].max() * 1.15])
    return fig


# ---------------------------------------------------------------------------
# 2. Linha múltipla — por sexo
# ---------------------------------------------------------------------------

def grafico_sexo(df_sexo: pd.DataFrame) -> go.Figure:
    """
    Duas linhas — Homens vs. Mulheres — ao longo do tempo.
    """
    fig = go.Figure()

    cores = {"Homens": PALETA[3], "Mulheres": PALETA[3+1]}
    # Fallback: usa paleta sequencial se os valores forem diferentes
    categorias = df_sexo["sexo"].unique()
    cores_map = {cat: PALETA[i % len(PALETA)] for i, cat in enumerate(categorias)}

    for cat in categorias:
        sub = df_sexo[df_sexo["sexo"] == cat]
        fig.add_trace(go.Scatter(
            x=sub["data"], y=sub["taxa"],
            mode="lines",
            name=cat,
            line=dict(color=cores_map[cat], width=2),
            hovertemplate=f"{cat} — %{{x|%b/%Y}}: <b>%{{y:.1f}}%</b><extra></extra>",
        ))

    _aplicar_layout(fig, "Taxa de desocupação por sexo")
    return fig


# ---------------------------------------------------------------------------
# 3. Linha múltipla — por faixa etária
# ---------------------------------------------------------------------------

def grafico_idade(df_idade: pd.DataFrame) -> go.Figure:
    """
    Linhas por faixa etária. Jovens (14–24) normalmente se destacam.
    """
    fig = go.Figure()
    categorias = df_idade["faixa_etaria"].unique()

    for i, cat in enumerate(categorias):
        sub = df_idade[df_idade["faixa_etaria"] == cat]
        fig.add_trace(go.Scatter(
            x=sub["data"], y=sub["taxa"],
            mode="lines",
            name=cat,
            line=dict(color=PALETA[i % len(PALETA)], width=2),
            hovertemplate=f"{cat}<br>%{{x|%b/%Y}}: <b>%{{y:.1f}}%</b><extra></extra>",
        ))

    _aplicar_layout(fig, "Taxa de desocupação por faixa etária")
    return fig


# ---------------------------------------------------------------------------
# 4. Heatmap — escolaridade × ano
# ---------------------------------------------------------------------------

def grafico_heatmap_escolaridade(df_esc: pd.DataFrame) -> go.Figure:
    """
    Heatmap: linhas = nível de escolaridade, colunas = ano.
    Revela como a crise afetou grupos com menos instrução de forma mais intensa.
    """
    # Agrega por ano (média dos trimestres)
    df_anual = (
        df_esc.groupby(["escolaridade", "ano"])["taxa"]
        .mean()
        .reset_index()
        .pivot(index="escolaridade", columns="ano", values="taxa")
    )

    fig = go.Figure(go.Heatmap(
        z=df_anual.values,
        x=df_anual.columns.astype(str),
        y=df_anual.index,
        colorscale=[
            [0.0, "#E1F5EE"],
            [0.5, "#EF9F27"],
            [1.0, "#D85A30"],
        ],
        hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>%{x}: <b>%{z:.1f}%</b><extra></extra>",
        colorbar=dict(title="Taxa (%)", ticksuffix="%"),
    ))

    fig.update_layout(
        **_layout_base_sem_eixos_margin(),
        title=dict(
            text="<b>Taxa de desocupação por escolaridade e ano</b><br>"
                 "<sup style='color:#888'>Média anual dos trimestres — Fonte: IBGE/PNAD Contínua</sup>",
            font_size=16, x=0.02,
        ),
        xaxis=dict(title="Ano", showgrid=False),
        yaxis=dict(title="", autorange="reversed"),
        margin=dict(l=280, r=40, t=90, b=60),
    )
    return fig


# ---------------------------------------------------------------------------
# 5. Barras agrupadas — por cor/raça (último ano disponível)
# ---------------------------------------------------------------------------

# Cores estáveis e legenda ordenada (evita “bagunça” visual)
_CORES_COR_RACA = {
    "Branca": "#378ADD",
    "Preta": "#D4537E",
    "Parda": "#EF9F27",
}
_ORDEM_COR_RACA = ("Branca", "Preta", "Parda")


def _preparar_cor_raca(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por (data, cor_raca) — média se houver duplicatas."""
    d = df[["data", "cor_raca", "taxa"]].copy()
    d = d.groupby(["data", "cor_raca"], as_index=False)["taxa"].mean()
    return d.sort_values(["cor_raca", "data"])


def grafico_cor_raca(df_cor: pd.DataFrame, ano: int = None) -> go.Figure:
    """
    Barras horizontais com a taxa por cor/raça no ano mais recente disponível
    (ou no ano especificado). Ordena do maior para o menor.
    """
    if ano is None:
        ano = df_cor["ano"].max()

    df_ano = (
        df_cor[df_cor["ano"] == ano]
        .groupby("cor_raca")["taxa"]
        .mean()
        .reset_index()
        .sort_values("taxa", ascending=True)
    )

    cores = [_CORES_COR_RACA.get(r, PALETA[i % len(PALETA)]) for i, r in enumerate(df_ano["cor_raca"])]

    fig = go.Figure(go.Bar(
        x=df_ano["taxa"],
        y=df_ano["cor_raca"],
        orientation="h",
        marker_color=cores,
        text=df_ano["taxa"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        hovertemplate="<b>%{y}</b>: %{x:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        **_layout_base_sem_eixos_margin(),
        title=dict(
            text=f"<b>Taxa de desocupação por cor/raça — {ano}</b><br>"
                 "<sup style='color:#888'>Média anual dos trimestres — Fonte: IBGE/PNAD Contínua</sup>",
            font_size=16, x=0.02,
        ),
        xaxis=dict(
            title="Taxa (%)",
            ticksuffix="%",
            showgrid=True,
            gridcolor="#f0f0f0",
            range=[0, max(float(df_ano["taxa"].max()) * 1.15, 1.0)],
        ),
        yaxis=dict(title=""),
        margin=dict(l=140, r=80, t=90, b=60),
    )
    return fig


# ---------------------------------------------------------------------------
# 6. Linha — cor/raça ao longo do tempo
# ---------------------------------------------------------------------------

def grafico_cor_raca_temporal(df_cor: pd.DataFrame) -> go.Figure:
    """
    Linhas por cor/raça ao longo do tempo — evidencia disparidades estruturais.
    """
    d = _preparar_cor_raca(df_cor)
    fig = go.Figure()

    categorias = [c for c in _ORDEM_COR_RACA if c in set(d["cor_raca"])]
    categorias += sorted(set(d["cor_raca"]) - set(categorias))

    for cat in categorias:
        sub = d[d["cor_raca"] == cat].sort_values("data")
        cor = _CORES_COR_RACA.get(cat, PALETA[categorias.index(cat) % len(PALETA)])
        fig.add_trace(go.Scatter(
            x=sub["data"],
            y=sub["taxa"],
            mode="lines",
            name=cat,
            line=dict(color=cor, width=2.5),
            hovertemplate=f"<b>{cat}</b><br>%{{x|%b/%Y}}: <b>%{{y:.1f}}%</b><extra></extra>",
        ))

    ymax = d["taxa"].max()
    _aplicar_layout(fig, "Evolução da taxa de desocupação por cor/raça")
    fig.update_layout(
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            traceorder="normal",
        ),
    )
    fig.update_yaxes(range=[0, ymax * 1.12], ticksuffix="%")
    return fig


# ---------------------------------------------------------------------------
# 7. Mapa coroplético — por região (último trimestre disponível)
# ---------------------------------------------------------------------------

def grafico_mapa_regioes(df_regiao: pd.DataFrame) -> go.Figure:
    """
    Mapa coroplético do Brasil por grande região, usando Plotly (sem GeoPandas).
    Usa o GeoJSON público do IBGE.
    
    Nota: para versão com GeoPandas (mais detalhada, por estado),
    use a função grafico_mapa_geopandas() em mapas.py.
    """
    import json, urllib.request

    # GeoJSON simplificado das regiões brasileiras (fonte: IBGE via GitHub)
    geojson_url = (
        "https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
        "master/public/data/brazil-states.geojson"
    )

    # Agrega por região no último trimestre disponível
    ultimo_periodo = df_regiao["periodo_cod"].max()
    df_mapa = df_regiao[df_regiao["periodo_cod"] == ultimo_periodo].copy()
    trimestre_label = df_mapa["trimestre"].iloc[0] if len(df_mapa) > 0 else ""

    # Mapa de regiões para agrupar estados
    estado_para_regiao = {
        "Acre": "Norte", "Amazonas": "Norte", "Roraima": "Norte",
        "Rondônia": "Norte", "Pará": "Norte", "Amapá": "Norte", "Tocantins": "Norte",
        "Maranhão": "Nordeste", "Piauí": "Nordeste", "Ceará": "Nordeste",
        "Rio Grande do Norte": "Nordeste", "Paraíba": "Nordeste",
        "Pernambuco": "Nordeste", "Alagoas": "Nordeste", "Sergipe": "Nordeste",
        "Bahia": "Nordeste",
        "Minas Gerais": "Sudeste", "Espírito Santo": "Sudeste",
        "Rio de Janeiro": "Sudeste", "São Paulo": "Sudeste",
        "Paraná": "Sul", "Santa Catarina": "Sul", "Rio Grande do Sul": "Sul",
        "Mato Grosso do Sul": "Centro-Oeste", "Mato Grosso": "Centro-Oeste",
        "Goiás": "Centro-Oeste", "Distrito Federal": "Centro-Oeste",
    }

    taxa_por_regiao = df_mapa.set_index("regiao")["taxa"].to_dict()

    # Cria DataFrame com um valor por estado (herdado da sua região)
    rows = []
    for estado, regiao in estado_para_regiao.items():
        taxa = taxa_por_regiao.get(regiao)
        rows.append({"estado": estado, "regiao": regiao, "taxa": taxa})
    df_estados = pd.DataFrame(rows)

    # Baixa o GeoJSON
    try:
        with urllib.request.urlopen(geojson_url, timeout=15) as resp:
            geojson = json.loads(resp.read())
    except Exception:
        # Fallback: mapa de barras por região se GeoJSON não carregar
        return grafico_barras_regioes(df_regiao)

    fig = px.choropleth(
        df_estados,
        geojson=geojson,
        locations="estado",
        featureidkey="properties.name",
        color="taxa",
        color_continuous_scale=["#E1F5EE", "#EF9F27", "#D85A30"],
        hover_name="estado",
        hover_data={"regiao": True, "taxa": ":.1f", "estado": False},
        labels={"taxa": "Taxa (%)"},
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="white",
    )
    fig.update_layout(
        title=dict(
            text=f"<b>Taxa de desocupação por região — {trimestre_label}</b><br>"
                 "<sup style='color:#888'>Fonte: IBGE — PNAD Contínua Trimestral</sup>",
            font_size=16, x=0.02,
        ),
        coloraxis_colorbar=dict(title="Taxa (%)", ticksuffix="%"),
        margin=dict(l=0, r=0, t=90, b=0),
        paper_bgcolor="white",
        font_family="'IBM Plex Sans', sans-serif",
    )
    return fig


def grafico_barras_regioes(df_regiao: pd.DataFrame) -> go.Figure:
    """
    Fallback: barras horizontais por região ao longo do tempo.
    """
    df_anual = (
        df_regiao.groupby(["regiao", "ano"])["taxa"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        df_anual,
        x="ano", y="taxa",
        color="regiao",
        color_discrete_sequence=PALETA,
        markers=True,
        labels={"taxa": "Taxa (%)", "ano": "Ano", "regiao": "Região"},
    )
    _aplicar_layout(fig, "Taxa de desocupação por grande região (média anual)")
    return fig
