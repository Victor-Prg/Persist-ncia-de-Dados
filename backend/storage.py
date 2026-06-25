"""
Camada de persistência: JSON, CSV, Pickle e Struct (binário de tamanho fixo).
"""

import csv
import json
import pickle
import struct
import time
from pathlib import Path

# Layout fixo: ID (uint32) | Nome (30 bytes) | Preço (float) | Categoria (20 bytes)
STRUCT_FORMAT = "I30sf20s"
RECORD_SIZE = struct.calcsize(STRUCT_FORMAT)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
JSON_PATH = DATA_DIR / "dados.json"
CSV_PATH = DATA_DIR / "dados.csv"
PKL_PATH = DATA_DIR / "dados.pkl"
BIN_PATH = DATA_DIR / "dados.bin"

CSV_FIELDS = ["id", "nome", "preco", "categoria"]

DADOS_EXEMPLO = [
    {"id": 1, "nome": "Teclado Mecanico", "preco": 299.90, "categoria": "Perifericos"},
    {"id": 2, "nome": "Mouse Gamer", "preco": 150.00, "categoria": "Perifericos"},
    {"id": 3, "nome": "Monitor Gamer 27", "preco": 1899.00, "categoria": "Perifericos"},
    {"id": 4, "nome": "Headset USB 7.1", "preco": 349.90, "categoria": "Perifericos"},
    {"id": 5, "nome": "SSD NVMe 1TB", "preco": 459.00, "categoria": "Armazenamento"},
    {"id": 6, "nome": "Memoria RAM 16GB DDR4", "preco": 289.99, "categoria": "Partes"},
    {"id": 7, "nome": "Webcam Full HD", "preco": 199.00, "categoria": "Perifericos"},
]


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _truncate_utf8(text: str, max_bytes: int) -> bytes:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return encoded.ljust(max_bytes, b"\x00")
    truncated = encoded[:max_bytes]
    # Evita cortar no meio de um caractere multibyte
    while truncated and truncated[-1] & 0xC0 == 0x80:
        truncated = truncated[:-1]
    return truncated.ljust(max_bytes, b"\x00")


def _decode_fixed(data: bytes) -> str:
    return data.rstrip(b"\x00").decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def salvar_json(produtos: list[dict]) -> None:
    _ensure_data_dir()
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)


def carregar_json() -> list[dict]:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def salvar_csv(produtos: list[dict]) -> None:
    _ensure_data_dir()
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(produtos)


def carregar_csv() -> list[dict]:
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            {
                "id": int(row["id"]),
                "nome": row["nome"],
                "preco": float(row["preco"]),
                "categoria": row["categoria"],
            }
            for row in reader
        ]


# ---------------------------------------------------------------------------
# Pickle
# ---------------------------------------------------------------------------

def salvar_pickle(produtos: list[dict]) -> None:
    _ensure_data_dir()
    with open(PKL_PATH, "wb") as f:
        pickle.dump(produtos, f)


def carregar_pickle() -> list[dict]:
    with open(PKL_PATH, "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Struct (binário de tamanho fixo)
# ---------------------------------------------------------------------------

def _produto_para_bytes(produto: dict) -> bytes:
    return struct.pack(
        STRUCT_FORMAT,
        int(produto["id"]),
        _truncate_utf8(str(produto["nome"]), 30),
        float(produto["preco"]),
        _truncate_utf8(str(produto["categoria"]), 20),
    )


def _bytes_para_produto(data: bytes) -> dict:
    produto_id, nome_raw, preco, categoria_raw = struct.unpack(STRUCT_FORMAT, data)
    return {
        "id": produto_id,
        "nome": _decode_fixed(nome_raw),
        "preco": round(preco, 2),
        "categoria": _decode_fixed(categoria_raw),
    }


def salvar_bin(produtos: list[dict]) -> None:
    _ensure_data_dir()
    with open(BIN_PATH, "wb") as f:
        header = struct.pack("I", len(produtos))
        f.write(header)
        for produto in produtos:
            f.write(_produto_para_bytes(produto))


def carregar_bin() -> list[dict]:
    with open(BIN_PATH, "rb") as f:
        raw_count = f.read(4)
        if len(raw_count) < 4:
            return []
        count = struct.unpack("I", raw_count)[0]
        produtos = []
        for _ in range(count):
            record = f.read(RECORD_SIZE)
            if len(record) < RECORD_SIZE:
                break
            produtos.append(_bytes_para_produto(record))
        return produtos


# ---------------------------------------------------------------------------
# Salvar / carregar todos os formatos
# ---------------------------------------------------------------------------

SAVERS = {
    "json": salvar_json,
    "csv": salvar_csv,
    "pickle": salvar_pickle,
    "bin": salvar_bin,
}

LOADERS = {
    "json": carregar_json,
    "csv": carregar_csv,
    "pickle": carregar_pickle,
    "bin": carregar_bin,
}

PATHS = {
    "json": JSON_PATH,
    "csv": CSV_PATH,
    "pickle": PKL_PATH,
    "bin": BIN_PATH,
}


def salvar_todos(produtos: list[dict]) -> None:
    for salvar in SAVERS.values():
        salvar(produtos)


def medir_salvar(formato: str, produtos: list[dict]) -> float:
    salvar = SAVERS[formato]
    inicio = time.perf_counter()
    salvar(produtos)
    return time.perf_counter() - inicio


def medir_carregar(formato: str) -> float:
    carregar = LOADERS[formato]
    inicio = time.perf_counter()
    carregar()
    return time.perf_counter() - inicio


def tamanho_kb(formato: str) -> float:
    path = PATHS[formato]
    if not path.exists():
        return 0.0
    return round(path.stat().st_size / 1024, 4)


# ---------------------------------------------------------------------------
# Inspeção visual
# ---------------------------------------------------------------------------

def preview_texto(formato: str, linhas: int = 8) -> str:
    path = PATHS[formato]
    if not path.exists():
        return "(arquivo ainda não existe)"
    with open(path, "r", encoding="utf-8") as f:
        return "".join(f.readline() for _ in range(linhas))


def hexdump(caminho: Path, bytes_por_linha: int = 16, max_linhas: int = 8) -> str:
    if not caminho.exists():
        return "(arquivo ainda não existe)"
    linhas: list[str] = []
    with open(caminho, "rb") as f:
        offset = 0
        for _ in range(max_linhas):
            chunk = f.read(bytes_por_linha)
            if not chunk:
                break
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            linhas.append(f"{offset:08x}  {hex_part:<{bytes_por_linha * 3}}  |{ascii_part}|")
            offset += len(chunk)
    return "\n".join(linhas)
