"""
PROVA LOCAL — mesma lógica do etl-spark.ipynb (Bronze->Silver->Gold) com PySpark
real, lendo Bronze JSON local e gravando Parquet local. Única diferença para o
ambiente do enunciado: caminhos locais no lugar de s3a://.
"""
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (col, from_unixtime, to_date, avg, count,
                                    round as sround, row_number, min as smin, max as smax)

BRONZE = "evidencias/bronze"
LAKE   = "evidencias/lakehouse"
CHAVE  = ["Tipo", "Data_Vencimento", "Data_Base"]   # chave de negócio

spark = (SparkSession.builder
    .appName("ETL Tesouro - Bronze/Silver/Gold (PROVA LOCAL)")
    .master("local[*]")
    .config("spark.sql.shuffle.partitions", "4")
    .config("spark.ui.enabled", "false")
    .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
def banner(t): print("\n" + "="*72 + f"\n{t}\n" + "="*72)

# ---------------- BRONZE ----------------
banner("CAMADA BRONZE — leitura dos JSON brutos (formato Kafka Connect S3 Sink)")
df_bronze_ipca = spark.read.json(f"{BRONZE}/postgres-dadostesouroipca/")
df_bronze_pre  = spark.read.json(f"{BRONZE}/postgres-dadostesouropre/")
print(f"Bronze IPCA: {df_bronze_ipca.count()} registros | Bronze PRE: {df_bronze_pre.count()} registros")
print("Schema (Data_* e dt_update como epoch ms / bigint):")
df_bronze_ipca.printSchema()
df_bronze_ipca.show(5, truncate=False)

# ---------------- SILVER ----------------
banner("CAMADA SILVER — descarte de inválidos, dedup por chave de negócio, datas, normalização")
def to_silver(df, nome):
    bruto = df.count()
    # 1) descartar registros inválidos (preço de compra/venda ausente)
    df_valid = df.filter(col("PUCompraManha").isNotNull() & col("PUVendaManha").isNotNull())
    invalidos = bruto - df_valid.count()
    # 2) dedup por chave de negócio mantendo o registro mais recente (dt_update)
    w = Window.partitionBy(*CHAVE).orderBy(col("dt_update").desc())
    df_dedup = (df_valid.withColumn("_rn", row_number().over(w))
                        .filter(col("_rn") == 1).drop("_rn"))
    removidos = df_valid.count() - df_dedup.count()
    # 3) conversão de datas (epoch ms -> data legível) + normalização
    df_sil = (df_dedup
        .withColumn("Data_Vencimento", to_date(from_unixtime(col("Data_Vencimento")/1000)))
        .withColumn("Data_Base",       to_date(from_unixtime(col("Data_Base")/1000)))
        .withColumn("dt_update",        from_unixtime(col("dt_update")/1000, "yyyy-MM-dd HH:mm:ss")))
    print(f"[{nome}] bruto={bruto} | inválidos descartados={invalidos} | "
          f"duplicatas/versões removidas={removidos} | Silver final={df_sil.count()}")
    return df_sil

df_silver_ipca = to_silver(df_bronze_ipca, "IPCA")
df_silver_pre  = to_silver(df_bronze_pre,  "PRE")
print("\nSchema Silver (datas convertidas):"); df_silver_ipca.printSchema()
print("Amostra Silver IPCA:")
df_silver_ipca.orderBy("Data_Base").show(5, truncate=False)
df_silver_ipca.write.mode("overwrite").parquet(f"{LAKE}/ipca/silver/")
df_silver_pre.write.mode("overwrite").parquet(f"{LAKE}/pre/silver/")
print(f"Silver gravada em Parquet: {LAKE}/ipca/silver e {LAKE}/pre/silver")

# ---------------- GOLD ----------------
banner("CAMADA GOLD — agregações analíticas por tipo de título")
def to_gold(df):
    return (df.groupBy("Tipo").agg(
        sround(avg("PUCompraManha"), 2).alias("Media_PUCompraManha"),
        sround(avg("PUVendaManha"),  2).alias("Media_PUVendaManha"),
        sround(avg("CompraManha"),   4).alias("Media_TaxaCompra"),
        sround(smin("PUCompraManha"),2).alias("Min_PUCompra"),
        sround(smax("PUCompraManha"),2).alias("Max_PUCompra"),
        count("*").alias("Total_Registros")))
df_gold_ipca = to_gold(df_silver_ipca); df_gold_pre = to_gold(df_silver_pre)
print("GOLD IPCA:"); df_gold_ipca.show(truncate=False)
print("GOLD PRE:");  df_gold_pre.show(truncate=False)
df_gold_ipca.write.mode("overwrite").parquet(f"{LAKE}/ipca/gold/")
df_gold_pre.write.mode("overwrite").parquet(f"{LAKE}/pre/gold/")

# ---------------- SPARK SQL ----------------
banner("SPARK SQL — consulta analítica sobre a camada Gold")
df_gold_ipca.unionByName(df_gold_pre).createOrReplaceTempView("gold_tesouro")
spark.sql("""
    SELECT Tipo, Total_Registros, Media_PUCompraManha, Media_TaxaCompra
    FROM gold_tesouro ORDER BY Media_PUCompraManha DESC
""").show(truncate=False)

banner("VALIDAÇÃO — Parquet relido")
for p in [f"{LAKE}/ipca/silver", f"{LAKE}/pre/silver", f"{LAKE}/ipca/gold", f"{LAKE}/pre/gold"]:
    print(f"  {p}: {spark.read.parquet(p).count()} registros (relido OK)")
spark.stop()
print("\nETL concluído com sucesso.")
