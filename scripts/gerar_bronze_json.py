import csv, json, os, datetime as dt

SRC = "data/PrecoTaxaTesouroDireto.csv"
BRONZE = "evidencias/bronze"
BASE_TS = int(dt.datetime(2026, 6, 11, tzinfo=dt.timezone.utc).timestamp() * 1000)

def to_ms(d):
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)
def parse_date(s):
    dd, mm, yy = s.split("/"); return dt.date(int(yy), int(mm), int(dd))
def num(s):
    s = (s or "").strip().replace(",", ".")
    return float(s) if s not in ("", "nan") else None

def read_rows(path):
    for enc in ("latin-1", "utf-8"):
        try:
            with open(path, encoding=enc) as f:
                return list(csv.DictReader(f, delimiter=";"))
        except UnicodeDecodeError:
            continue
    raise RuntimeError("Não consegui ler o CSV em latin-1 nem utf-8")

rows_ipca, rows_pre = [], []
for r in read_rows(SRC):
    tipo = r["Tipo Titulo"]
    base = parse_date(r["Data Base"])
    rec = {
        "CompraManha":   num(r["Taxa Compra Manha"]),
        "VendaManha":    num(r["Taxa Venda Manha"]),
        "PUCompraManha": num(r["PU Compra Manha"]),
        "PUVendaManha":  num(r["PU Venda Manha"]),
        "PUBaseManha":   num(r["PU Base Manha"]),
        "Data_Vencimento": to_ms(parse_date(r["Data Vencimento"])),
        "Data_Base":       to_ms(base),
        "Tipo": tipo,  # nome completo do titulo (chave de negocio correta)
        # determinístico: mesma Data_Base -> mesmo dt_update
        "dt_update": BASE_TS + (base - dt.date(2026,1,1)).days * 86_400_000,
    }
    (rows_ipca if "IPCA" in tipo else rows_pre).append(rec)

n_base_ipca, n_base_pre = len(rows_ipca), len(rows_pre)

# -------- anomalias (apenas no IPCA) --------
import copy
# (A) duplicata exata do 1o registro
rows_ipca.append(copy.deepcopy(rows_ipca[0]))
# (B) par versão antiga/nova da MESMA chave de negócio
chave = copy.deepcopy(rows_ipca[5])
antiga = copy.deepcopy(chave); antiga["dt_update"] = chave["dt_update"] - 86_400_000
antiga["PUCompraManha"] = round(chave["PUCompraManha"] * 0.5, 2)   # valor "errado" antigo
nova = copy.deepcopy(chave);  nova["dt_update"]  = chave["dt_update"] + 86_400_000
nova["PUCompraManha"]  = round(chave["PUCompraManha"] * 1.001, 2)  # correção mais recente
rows_ipca += [antiga, nova]
# (C) registro inválido: PU nulo
invalido = copy.deepcopy(rows_ipca[9])
invalido["PUCompraManha"] = None; invalido["PUVendaManha"] = None; invalido["PUBaseManha"] = None
invalido["dt_update"] = BASE_TS + 999_000_000   # único, p/ não colidir
rows_ipca.append(invalido)

def dump(rows, topic):
    d = os.path.join(BRONZE, topic); os.makedirs(d, exist_ok=True)
    for i in range(0, len(rows), 2):
        fname = f"{topic}+0+{i:010d}.json"
        with open(os.path.join(d, fname), "w", encoding="utf-8") as f:
            for rec in rows[i:i+2]:
                f.write(json.dumps(rec) + "\n")
    return len(rows)

ti = dump(rows_ipca, "postgres-dadostesouroipca")
tp = dump(rows_pre,  "postgres-dadostesouropre")
print(f"Bronze IPCA: {ti} registros ({n_base_ipca} base + 4 anomalias: dup, antiga, nova, inválido)")
print(f"Bronze PRE : {tp} registros")
print("Esperado na Silver IPCA: 360 únicos válidos "
      "(remove 1 dup exata, colapsa par antiga/nova em 1, descarta 1 inválido,"
      " e a 'nova' substitui a chave original -> 360+1(nova distinta?) ver teste).")
