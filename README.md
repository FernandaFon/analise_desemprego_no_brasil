# Análise PNAD Contínua — Taxa de desocupação no Brasil

Projeto em Python que coleta dados da **API SIDRA** (IBGE), limpa e padroniza séries trimestrais da **PNAD Contínua Trimestral** e gera visualizações interativas com **Plotly** (notebook `analise_pnad.ipynb`).

## O que este repositório faz

- Consulta tabelas do SIDRA para taxa de desocupação **geral**, por **sexo**, **faixa etária**, **escolaridade**, **cor ou raça** e **grande região**.
- Para escolaridade e cor/raça, baixa contagens absolutas (`v/all`) com classificações específicas e calcula a taxa a partir de **ocupados** e **desocupados** na semana de referência.
- Produz gráficos de linha, heatmap, barras por região/cor/raca e mapa (GeoJSON), com opção de exportar PNG/HTML.

## Requisitos

- **Python 3.13+** (conforme `pyproject.toml`).
- Recomendado: [**uv**](https://github.com/astral-sh/uv) para gerenciar o ambiente e dependências.

## Estrutura do projeto

```
analise/
├── analise_pnad.ipynb   # Notebook principal — execute daqui
├── config.py            # URLs SIDRA, tabelas, classificações e paleta
├── coleta.py            # Coleta HTTP, limpeza, cálculo manual da taxa
├── graficos.py          # Funções Plotly (gráficos e exportação)
├── pyproject.toml       # Dependências do projeto
└── graficos/            # Criada ao exportar PNG/HTML (opcional)
```

## Como rodar

### Com uv (recomendado)

Na raiz do repositório:

```bash
uv sync
uv run jupyter notebook analise_pnad.ipynb
```

### Alternativa (pip)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
python3 -m pip install -e .
jupyter notebook analise_pnad.ipynb
```

No Linux, `python` pode não existir no PATH; use `python3`.

### Dependências principais

| Pacote   | Uso |
|----------|-----|
| `requests` | Chamadas à API SIDRA |
| `pandas`   | Dados e agregações |
| `plotly`   | Gráficos interativos |
| `kaleido`  | Exportação de PNG (`fig.write_image`) |
| `jupyter` / `notebook` | Execução do notebook |
| `geopandas` | Dependência opcional para mapas mais avançados; o mapa no notebook usa Plotly + GeoJSON |

## Fluxo dos dados

1. **`config.TABELAS_CONFIG`** — define, para cada recorte, tabela SIDRA, nível territorial (`n1`/`n2`), variáveis e sufixo de classificação (`/c...`).
2. **`coleta.coletar_todos()`** — monta as URLs e monta `DataFrame`s com colunas renomeadas.
3. **`coleta.limpar_todos()`** — converte `periodo_cod` (formato `AAAATT`, ex.: `202504`), cria `data`, `ano` e trimestre; remove linhas “Total” quando configurado.
4. **`coleta.calcular_taxa()`** — só para `escolaridade` e `cor_raca`: cruza ocupados e desocupados por `periodo_cod` e categoria, e calcula a taxa (ver metodologia abaixo).
5. **`graficos.*`** — gera as figuras Plotly.

## Tabelas SIDRA utilizadas

| Recorte        | Tabela | Variável na API | Classificação / notas |
|----------------|--------|-----------------|-----------------------|
| **Geral** (Brasil) | 4099   | 4099            | Taxa direta           
| **Sexo**           | 4093   | 4099            | `c2`: homens, mulheres (sem total)
| **Faixa etária**   | 4094   | 4099            | `c58/all`               
| **Escolaridade**   | 4095   | `all`             | `c1568/allxt` (nível de instrução; sem total) + cálculo manual
| **Cor ou raça**    | **6402**   | `all`             | `c86/allxt` (cor/raça; sem total) + cálculo manual
| **Região**         | 4099   | 4099            | Nível `n2` (grandes regiões)

A documentação oficial do formato da URL está em [Ajuda da API SIDRA](https://apisidra.ibge.gov.br/home/ajuda). Descrições de tabelas: [SIDRA — PNAD Contínua](https://sidra.ibge.gov.br/pesquisa/pnadct).

## Metodologia — taxa nos recortes manuais (escolaridade e cor/raça)

A API retorna valores em **mil pessoas** para variáveis como “Pessoas … ocupadas na semana de referência” e “Pessoas … desocupadas na semana de referência”. O código:

- Ignora coeficientes de variação e linhas de percentuais derivados.
- Cruza **ocupados** e **desocupados** na mesma categoria (escolaridade ou cor/raça) e no mesmo `periodo_cod`.
- Calcula:
[
\text{taxa (\%)} = \frac{\text{desocupados}}{\text{desocupados} + \text{ocupados}} \times 100
]
Isso equivale à taxa de desocupação no grupo (desocupados em relação à população ocupada + desocupada naquele recorte).

## Gráficos gerados no notebook

1. Linha temporal — desocupação geral (com faixa de pandemia e anotações).
2. Linhas — por sexo.
3. Linhas — por faixa etária.
4. Heatmap — escolaridade × ano (média anual dos trimestres).
5. Barras horizontais e linha temporal — cor ou raça (cores consistentes por grupo).
6. Mapa por estado (GeoJSON) e linhas por grande região.

## Exportar figuras

No notebook, a última seção cria a pasta `graficos/` e salva PNG e HTML. Exige **Kaleido** instalado para `write_image`.

## Ajustes técnicos já incorporados no código

- **Trimestre** (`periodo_cod`): uso dos dois últimos dígitos no formato `AAAATT` (ex.: `201201` → 1º trimestre de 2012).
- **Escolaridade**: classificação `C1568` com `allxt` para trazer categorias sem o total agregado.
- **Cor ou raça**: tabela **6402** (mercado de trabalho por cor/raça), não apenas população por cor.
- **Plotly**: `update_yaxes` (não `update_yaxis`); layout sem passar `margin` duas vezes em `update_layout`.
- **Gráficos de cor/raça**: agregação por data e categoria, cores fixas e eixo Y com range explícito para leitura mais clara.

## Referências e links úteis

- [Portal PNAD Contínua — IBGE](https://www.ibge.gov.br/estatisticas/sociais/trabalho/17270-pnad-continua.html)
- [SIDRA — tabelas PNAD Contínua (trimestral)](https://sidra.ibge.gov.br/pesquisa/pnadct/tabelas)
- [SIDRA — tabelas PNAD Contínua (mensal)](https://sidra.ibge.gov.br/pesquisa/pnadcm/tabelas) (outra pesquisa; não confundir com a trimestral)
- [Ajuda da API SIDRA](https://apisidra.ibge.gov.br/home/ajuda)
- [API de agregados IBGE (documentação)](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3)
- Exemplos de URLs: tabelas [4093](https://sidra.ibge.gov.br/tabela/descricao/4093), [4094](https://sidra.ibge.gov.br/tabela/descricao/4094), [4095](https://sidra.ibge.gov.br/tabela/descricao/4095), [4099](https://sidra.ibge.gov.br/tabela/descricao/4099)

---

**Fonte dos dados:** IBGE — Pesquisa Nacional por Amostra de Domicílios Contínua Trimestral.
