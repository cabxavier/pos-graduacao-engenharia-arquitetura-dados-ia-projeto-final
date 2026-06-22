import csv, sys, random, datetime as dt

random.seed(42)
out = sys.argv[1] if len(sys.argv) > 1 else "PrecoTaxaTesouroDireto.csv"

ipca = [
    ("Tesouro IPCA+ 2026", dt.date(2026,8,15), 6.10),
    ("Tesouro IPCA+ 2029", dt.date(2029,5,15), 6.45),
    ("Tesouro IPCA+ com Juros Semestrais 2035", dt.date(2035,5,15), 6.55),
    ("Tesouro IPCA+ 2035", dt.date(2035,5,15), 6.60),
    ("Tesouro IPCA+ com Juros Semestrais 2045", dt.date(2045,5,15), 6.62),
    ("Tesouro IPCA+ com Juros Semestrais 2055", dt.date(2055,5,15), 6.65),
]
pre = [
    ("Tesouro Prefixado 2025", dt.date(2025,1,1), 10.40),
    ("Tesouro Prefixado 2027", dt.date(2027,1,1), 11.20),
    ("Tesouro Prefixado 2029", dt.date(2029,1,1), 11.85),
    ("Tesouro Prefixado com Juros Semestrais 2031", dt.date(2031,1,1), 12.05),
    ("Tesouro Prefixado com Juros Semestrais 2033", dt.date(2033,1,1), 12.25),
]

def br(x): return f"{x:.2f}".replace(".", ",")

rows = []
base_date = dt.date(2026, 6, 10)
for titulo, venc, taxa_ref in ipca + pre:
    is_pre = titulo.startswith("Tesouro Prefixado")
    pu_ref = 100000 / ((1 + taxa_ref/100) ** max(1, (venc.year - 2026))) if is_pre else \
             1000 * (1 - taxa_ref/100/12)
    pu_ref = max(180.0, min(pu_ref, 4200.0))
    d, n = base_date, 0
    while n < 60:
        if d.weekday() < 5:
            taxa_c = taxa_ref + random.uniform(-0.08, 0.08)
            taxa_v = taxa_c + random.uniform(0.04, 0.10)
            pu_v = pu_ref * (1 + random.uniform(-0.01, 0.01))
            pu_c = pu_v * (1 + random.uniform(0.0005, 0.0025))
            pu_b = (pu_c + pu_v) / 2
            rows.append([titulo, venc.strftime("%d/%m/%Y"), d.strftime("%d/%m/%Y"),
                         br(taxa_c), br(taxa_v), br(pu_c), br(pu_v), br(pu_b)])
            n += 1
        d -= dt.timedelta(days=1)

with open(out, "w", newline="", encoding="latin-1") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Tipo Titulo","Data Vencimento","Data Base","Taxa Compra Manha",
                "Taxa Venda Manha","PU Compra Manha","PU Venda Manha","PU Base Manha"])
    w.writerows(rows)
print(f"Gerado {out}: {len(rows)} linhas "
      f"({sum(r[0].startswith('Tesouro IPCA') for r in rows)} IPCA / "
      f"{sum(r[0].startswith('Tesouro Prefixado') for r in rows)} PRE).")
