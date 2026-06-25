"""
API de persistência — Trabalho Final (ordenação/busca com memória offline).
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from storage import (
    BIN_PATH,
    DADOS_EXEMPLO,
    LOADERS,
    PATHS,
    PKL_PATH,
    hexdump,
    medir_carregar,
    medir_salvar,
    preview_texto,
    preview_texto_completo,
    salvar_todos,
    tamanho_kb,
)

app = FastAPI(
    title="Persistência de Dados — Texto vs Binário",
    description="Backend para salvar, carregar offline e comparar formatos de persistência.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Produto(BaseModel):
    id: int
    nome: str
    preco: float
    categoria: str


class SalvarRequest(BaseModel):
    produtos: list[Produto] | None = None


@app.get("/carregar")
def carregar():
    """Simula busca na API original e devolve os dados para o frontend."""
    return {"produtos": DADOS_EXEMPLO, "fonte": "api"}


@app.post("/salvar")
def salvar(body: SalvarRequest | None = None):
    """Grava os dados nos quatro formatos simultaneamente."""
    produtos = (
        [p.model_dump() for p in body.produtos]
        if body and body.produtos
        else DADOS_EXEMPLO
    )
    try:
        salvar_todos(produtos)
        return {
            "mensagem": "Dados salvos com sucesso nos 4 formatos.",
            "quantidade": len(produtos),
            "arquivos": {fmt: str(PATHS[fmt]) for fmt in PATHS},
        }
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gravar em disco: {exc}") from exc


@app.get("/offline")
def offline(
    formato: str = Query(
        default="json",
        description="Formato a carregar: json, csv, pickle ou bin",
    ),
):
    """Lê dados do disco (modo offline) quando não há internet."""
    formato = formato.lower()
    if formato not in LOADERS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato inválido. Use: {', '.join(LOADERS)}",
        )

    path = PATHS[formato]
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo '{path.name}' não encontrado. Execute POST /salvar primeiro.",
        )

    try:
        produtos = LOADERS[formato]()
        return {
            "produtos": produtos,
            "fonte": "offline",
            "formato": formato,
            "arquivo": str(path),
        }
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ler arquivo offline ({formato}): {exc}",
        ) from exc


@app.get("/comparar")
def comparar():
    """
    Compara tamanho (KB) e tempo de salvar/carregar dos 4 formatos.
    Inclui preview de texto (JSON/CSV) e hexdump dos binários (PKL/BIN).
    """
    from storage import DADOS_EXEMPLO as produtos

    # Garante que todos os arquivos existam para medição justa
    try:
        salvar_todos(produtos)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao preparar arquivos: {exc}") from exc

    formatos = {}
    for nome in ("json", "csv", "pickle", "bin"):
        try:
            tempo_salvar = medir_salvar(nome, produtos)
            tempo_carregar = medir_carregar(nome)
            formatos[nome] = {
                "tamanho_kb": tamanho_kb(nome),
                "tempo_salvar_ms": round(tempo_salvar * 1000, 4),
                "tempo_carregar_ms": round(tempo_carregar * 1000, 4),
            }
        except OSError as exc:
            formatos[nome] = {"erro": str(exc)}

    inspecao = {
        "texto_json": preview_texto_completo("json"),
        "texto_csv": preview_texto("csv"),
        "hexdump_pickle": hexdump(PKL_PATH),
        "hexdump_bin": hexdump(BIN_PATH),
        "struct_layout": "I30sf20s  (id: uint32 | nome: 30 bytes | preco: float | categoria: 20 bytes)",
    }

    return {
        "comparacao": formatos,
        "inspecao": inspecao,
        "resumo": {
            "menor_arquivo": min(
                formatos,
                key=lambda f: formatos[f].get("tamanho_kb", float("inf")),
            ),
            "mais_rapido_salvar": min(
                formatos,
                key=lambda f: formatos[f].get("tempo_salvar_ms", float("inf")),
            ),
            "mais_rapido_carregar": min(
                formatos,
                key=lambda f: formatos[f].get("tempo_carregar_ms", float("inf")),
            ),
        },
    }