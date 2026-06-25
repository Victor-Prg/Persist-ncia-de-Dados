# Persistência de Dados — Texto vs Binário

Trabalho final integrando um **backend Python (FastAPI)** a um **frontend JavaScript** de ordenação e busca de produtos. O sistema dá "memória" ao aplicativo, permitindo funcionamento offline e comparando a eficiência de formatos de **texto** (JSON, CSV) e **binário** (Pickle, Struct).

## Funcionalidades

- Carregar produtos simulando uma API online
- Salvar dados simultaneamente em 4 formatos de persistência
- Carregar do disco em modo offline (sem internet)
- Comparar tamanho (KB) e tempo de execução (salvar/carregar) entre formatos
- Inspeção visual: preview de arquivos de texto e hexdump de arquivos binários

## Estrutura do projeto

```
.
├── backend/
│   ├── main.py          # API FastAPI (endpoints REST)
│   └── storage.py       # Camada de persistência (JSON, CSV, Pickle, Struct)
├── frontend/
│   └── index.html       # Interface de busca, ordenação e integração com a API
├── data/                # Arquivos gerados em runtime (ignorado pelo Git)
├── requirements.txt     # Dependências Python
└── package.json         # Scripts para subir frontend e API
```

## Tecnologias

| Camada    | Tecnologia                                      |
|-----------|-------------------------------------------------|
| Backend   | Python 3, FastAPI, Uvicorn, Pydantic            |
| Texto     | `json`, `csv` (encoding UTF-8)                |
| Binário   | `pickle`, `struct` (registros de tamanho fixo)  |
| Frontend  | HTML, CSS, JavaScript (fetch API)               |

## Modelo de dados

Cada produto possui a seguinte estrutura:

```json
{
  "id": 1,
  "nome": "Teclado Mecanico",
  "preco": 299.90,
  "categoria": "Perifericos"
}
```

### Dataset de exemplo (7 produtos)

| ID | Nome                  | Preço (R$) | Categoria      |
|----|-----------------------|------------|----------------|
| 1  | Teclado Mecanico      | 299,90     | Perifericos    |
| 2  | Mouse Gamer           | 150,00     | Perifericos    |
| 3  | Monitor Gamer 27      | 1.899,00   | Perifericos    |
| 4  | Headset USB 7.1       | 349,90     | Perifericos    |
| 5  | SSD NVMe 1TB          | 459,00     | Armazenamento  |
| 6  | Memoria RAM 16GB DDR4 | 289,99     | Partes         |
| 7  | Webcam Full HD        | 199,00     | Perifericos    |

### Layout Struct (`dados.bin`)

Formato fixo por registro: **`I30sf20s`** (58 bytes)

| Campo       | Tipo struct | Tamanho |
|-------------|-------------|---------|
| `id`        | `I` (uint32)| 4 bytes |
| `nome`      | `30s`       | 30 bytes|
| `preco`     | `f` (float) | 4 bytes |
| `categoria` | `20s`       | 20 bytes|

O arquivo inicia com um header de 4 bytes (`I`) indicando a quantidade de registros.

## Endpoints da API

| Método | Rota       | Descrição |
|--------|------------|-----------|
| `GET`  | `/carregar` | Simula busca na API original e retorna os dados de exemplo |
| `POST` | `/salvar`   | Grava `dados.json`, `dados.csv`, `dados.pkl` e `dados.bin` |
| `GET`  | `/offline?formato=json` | Lê dados do disco (modo offline). Formatos: `json`, `csv`, `pickle`, `bin` |
| `GET`  | `/comparar` | Retorna tamanhos, tempos, preview de texto e hexdump |

Documentação interativa: [http://localhost:8000/docs](http://localhost:8000/docs)

### Exemplo de resposta — `GET /comparar`

```json
{
  "comparacao": {
    "json":   { "tamanho_kb": 0.21, "tempo_salvar_ms": 1.2, "tempo_carregar_ms": 0.8 },
    "csv":    { "tamanho_kb": 0.09, "tempo_salvar_ms": 0.9, "tempo_carregar_ms": 0.7 },
    "pickle": { "tamanho_kb": 0.13, "tempo_salvar_ms": 0.5, "tempo_carregar_ms": 0.4 },
    "bin":    { "tamanho_kb": 0.12, "tempo_salvar_ms": 0.3, "tempo_carregar_ms": 0.2 }
  },
  "inspecao": {
    "texto_json": "...",
    "texto_csv": "...",
    "hexdump_pickle": "...",
    "hexdump_bin": "..."
  }
}
```

## Como executar

### Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/) (marcar **Add to PATH** na instalação)
- [Node.js](https://nodejs.org/) com [pnpm](https://pnpm.io/)

### 1. Instalar dependências

```powershell
cd "Persist-ncia-de-Dados"
python -m pip install -r requirements.txt
pnpm install
```

### 2. Subir o backend (Terminal 1)

```powershell
cd backend
python -m uvicorn main:app --reload --port 8000
```

Ou, da raiz do projeto:

```powershell
pnpm api
```

### 3. Subir o frontend (Terminal 2)

```powershell
pnpm frontend
```

Acesse: [http://localhost:5173](http://localhost:5173)

## Fluxo de uso

1. **Carregar da API** — busca os produtos do endpoint `/carregar`
2. **Buscar / Ordenar** — filtra por nome ou categoria e ordena a tabela
3. **Salvar em Disco** — grava os 4 arquivos na pasta `data/`
4. **Comparar Formatos** — exibe tabela comparativa e inspeção visual (texto vs hexdump)
5. **Carregar do Arquivo (Offline)** — lê do disco via `/offline` simulando falta de internet

## Boas práticas implementadas

- Uso de `with open(...)` em todas as operações de I/O
- `encoding="utf-8"` em arquivos de texto (JSON e CSV)
- Tratamento de erros com `try/except` e HTTP 404 quando arquivo offline não existe
- CORS habilitado para integração com o frontend

## Arquivos gerados em `data/`

| Arquivo       | Formato   | Tipo    |
|---------------|-----------|---------|
| `dados.json`  | JSON      | Texto   |
| `dados.csv`   | CSV       | Texto   |
| `dados.pkl`   | Pickle    | Binário |
| `dados.bin`   | Struct    | Binário |

> A pasta `data/` está no `.gitignore` — os arquivos são criados localmente ao executar **Salvar em Disco**.

## Autor

**Victor** — [victor-prg](https://github.com/Victor-Prg) · victor.squeiroz.dev@gmail.com
