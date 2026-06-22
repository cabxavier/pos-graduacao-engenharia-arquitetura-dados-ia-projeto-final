CREATE TABLE IF NOT EXISTS public.dadostesouroipca (
    "CompraManha"     DOUBLE PRECISION,
    "VendaManha"      DOUBLE PRECISION,
    "PUCompraManha"   DOUBLE PRECISION,
    "PUVendaManha"    DOUBLE PRECISION,
    "PUBaseManha"     DOUBLE PRECISION,
    "Data_Vencimento" TIMESTAMP,
    "Data_Base"       TIMESTAMP,
    "Tipo"            TEXT,
    dt_update         TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.dadostesouropre (
    "CompraManha"     DOUBLE PRECISION,
    "VendaManha"      DOUBLE PRECISION,
    "PUCompraManha"   DOUBLE PRECISION,
    "PUVendaManha"    DOUBLE PRECISION,
    "PUBaseManha"     DOUBLE PRECISION,
    "Data_Vencimento" TIMESTAMP,
    "Data_Base"       TIMESTAMP,
    "Tipo"            TEXT,
    dt_update         TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ipca_dt_update ON public.dadostesouroipca (dt_update);
CREATE INDEX IF NOT EXISTS idx_pre_dt_update  ON public.dadostesouropre  (dt_update);
