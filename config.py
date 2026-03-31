"""
config.py
Configurações centrais do projeto — tabelas, variáveis e mapeamentos.
Edite aqui para adicionar ou remover recortes da análise.
"""

BASE_URL = "https://apisidra.ibge.gov.br/values"

# Cada entrada define uma consulta completa à API do SIDRA.
# 'classificacao' é o sufixo /cXX/all da URL.
# 'renomear' mapeia os campos genéricos do JSON para nomes legíveis.
# 'filtrar_total' indica se deve remover a linha "Total" da categoria (evita dupla contagem).

TABELAS_CONFIG = {
    "geral": {
        "tabela": "4099",
        "nivel": "n1",
        "local": "all",
        "variavel": "4099",
        "classificacao": "",
        "renomear": {
            "D3N": "trimestre",
            "D3C": "periodo_cod",
            "V":   "taxa",
        },
        "filtrar_total": False,
        "descricao": "Taxa de desocupação geral — Brasil",
    },
    "sexo": {
        "tabela": "4093",
        "nivel": "n1",
        "local": "all",
        "variavel": "4099",
        "classificacao": "/c2/6794,4,5",   # Total, Homens, Mulheres
        "renomear": {
            "D3N": "trimestre",
            "D3C": "periodo_cod",
            "D4N": "sexo",
            "V":   "taxa",
        },
        "filtrar_total": True,   # remove "Total" — queremos só Homens e Mulheres
        "col_categoria": "sexo",
        "descricao": "Taxa de desocupação por sexo",
    },
    "idade": {
        "tabela": "4094",
        "nivel": "n1",
        "local": "all",
        "variavel": "4099",
        "classificacao": "/c58/all",
        "renomear": {
            "D3N": "trimestre",
            "D3C": "periodo_cod",
            "D4N": "faixa_etaria",
            "V":   "taxa",
        },
        "filtrar_total": True,
        "col_categoria": "faixa_etaria",
        "descricao": "Taxa de desocupação por faixa etária",
    },
    "escolaridade": {
        "tabela": "4095",
        "nivel": "n1",
        "local": "all",
        "variavel": "all",
        "classificacao": "/c1568/allxt",
        "calculo_manual": True,
        "renomear": {
            "D3N": "trimestre",
            "D3C": "periodo_cod",
            "D2N": "Variável",
            "D4N": "escolaridade",
            "V":   "valor",
        },
        "filtrar_total": True,
        "col_categoria": "escolaridade",
        "descricao": "Desemprego por escolaridade (cálculo manual)",
    },
    "cor_raca": {
        "tabela": "6402",
        "nivel": "n1",
        "local": "all",
        "variavel": "all",
        "classificacao": "/c86/allxt",
        "calculo_manual": True,
        "renomear": {
            "D3N": "trimestre",
            "D3C": "periodo_cod",
            "D2N": "Variável",
            "D4N": "cor_raca",
            "V":   "valor",
        },
        "filtrar_total": True,
        "col_categoria": "cor_raca",
        "descricao": "Desemprego por cor/raça (cálculo manual)",
    },    
    "regiao": {
        "tabela": "4099",
        "nivel": "n2",
        "local": "all",
        "variavel": "4099",
        "classificacao": "",
        "renomear": {
            "D3N": "trimestre",
            "D3C": "periodo_cod",
            "D1N": "regiao",
            "V":   "taxa",
        },
        "filtrar_total": False,
        "col_categoria": "regiao",
        "descricao": "Taxa de desocupação por grande região",
    },
}

# Paleta de cores para os gráficos (Plotly)
# Escolhida para ser legível, com bom contraste e acessível para daltônicos.
PALETA = [
    "#1D9E75",  # teal
    "#D85A30",  # coral
    "#7F77DD",  # purple
    "#EF9F27",  # amber
    "#378ADD",  # blue
    "#D4537E",  # pink
    "#639922",  # green
    "#888780",  # gray
]

# URL do shapefile do IBGE para o mapa coroplético
URL_SHAPEFILE_REGIOES = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/"
    "malhas_territoriais/malhas_municipais/municipio_2022/"
    "Brasil/BR/BR_Regioes_2022.zip"
)

# Mapeamento entre nome da região no SIDRA → nome no shapefile do IBGE
MAPA_REGIOES = {
    "Norte":     "Norte",
    "Nordeste":  "Nordeste",
    "Sudeste":   "Sudeste",
    "Sul":       "Sul",
    "Centro-Oeste": "Centro-Oeste",
}
