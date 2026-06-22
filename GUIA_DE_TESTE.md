# Guia de Teste na AWS — passo a passo

Siga na ordem. Tudo no **Windows + Docker Desktop**, com o **Anaconda Prompt** aberto.
Quando aparecer `<...>`, substitua pelo seu valor.

---

## 0. Pré-requisitos (confira antes de começar)

- [ ] **Docker Desktop** aberto e rodando (ícone verde).
- [ ] Conta **AWS** ativa e o **AWS Console** logado no navegador.
- [ ] Ambiente conda criado (resolve o problema do Python 3.14):
  ```bash
  conda env create -f environment.yml
  conda activate tesouro
  python -m ipykernel install --user --name tesouro --display-name "Python (tesouro)"
  ```
- [ ] Entre na pasta do projeto:
  ```bash
  cd "<CAMINHO_DO_PROJETO>/ProjetoFinal"
  ```


---

## 1. AWS — criar buckets e descobrir seu Account ID / usuário

### 1.1 Criar 2 buckets S3
Console AWS → **S3** → **Create bucket** (duas vezes). Região **us-east-1 (N. Virginia)**.

> Crie os buckets com EXATAMENTE estes nomes (já estão nos arquivos do projeto):
> - `my-bucket-cabxavier-01`  (IPCA)
> - `my-bucket-cabxavier-02`  (PRE)
> Se algum nome já estiver em uso por outra conta, me avise que eu reconfiguro tudo.

### 1.2 Descobrir Account ID e nome do usuário IAM
Console AWS → canto superior direito (seu nome) → o número de 12 dígitos é o **Account ID**.
Console → **IAM** → **Users** → veja o **nome do usuário** dono da access key
`<SEU_ACCESS_KEY_ID>` (a que está no `.env`). Anote: `arn:aws:iam::<ACCOUNT_ID>:user/<USUARIO>`.

### 1.3 Permissão de escrita nos buckets
As políticas JÁ estão prontas (Account ID `<ACCOUNT_ID>`, usuário `<USUARIO_IAM>`).
Para cada bucket: **S3 → bucket → Permissions → Bucket policy → Edit** e cole:
- bucket `my-bucket-cabxavier-01` → conteúdo de `iam/bucket-policy-01.json`
- bucket `my-bucket-cabxavier-02` → conteúdo de `iam/bucket-policy-02.json`
(é só copiar e colar, sem editar nada)

---

## 2. Nomes dos buckets — JÁ CONFIGURADOS (você não precisa editar nada)

Os arquivos já apontam para os SEUS buckets:
- IPCA  -> `my-bucket-cabxavier-01`  (sink ipca + notebook + iam/bucket-policy-01.json)
- PRE   -> `my-bucket-cabxavier-02`  (sink pre  + notebook + iam/bucket-policy-02.json)
- Políticas IAM já com Account ID `<ACCOUNT_ID>` e usuário `<USUARIO_IAM>`.

Basta, no passo 1.1, criar os buckets EXATAMENTE com esses nomes na região us-east-1,
e no passo 1.3 colar `iam/bucket-policy-01.json` no bucket -01 e `...-02.json` no -02.

---

## 3. Rede Docker compartilhada
```bash
docker network create tesouro-net
```

## 4. Build da imagem custom do Kafka Connect
```bash
cd custom-kafka-connector-image
docker buildx build . -t connect-custom:1.0.0
cd ..
```
(demora alguns minutos na 1ª vez — baixa os conectores JDBC e S3)

## 5. Subir o PostgreSQL
```bash
cd postgres
docker-compose up -d
cd ..
docker ps        # confirme o container "postgres" rodando
```

## 6. Ingestão: rodar o notebook importar.ipynb
```bash
jupyter notebook
```
No navegador: abra `notebooks/importar.ipynb`, selecione o kernel **Python (tesouro)**
e rode todas as células (Shift+Enter). Ele baixa o CSV oficial do Tesouro e cria as
tabelas `dadostesouroipca` e `dadostesouropre`.

**✅ ENTREGÁVEL 1 — print das tabelas no Postgres:** abra o **DBeaver** (host `localhost`,
porta `5432`, db/user/senha = `postgres`) e tire um print das duas tabelas com dados.

## 7. Subir a plataforma Confluent
```bash
docker-compose up -d
docker ps        # broker, connect, schema-registry, ksqldb, rest-proxy
```
> Se a porta **8082** der erro: `netstat -ano | findstr :8082` e
> `taskkill /PID <PID> /F` (terminal como administrador). Depois `docker-compose up -d` de novo.

## 8. Criar os tópicos
```bash
bash scripts/criar_topicos.sh
```
Deve listar `postgres-dadostesouroipca` e `postgres-dadostesouropre`.

## 9. Registrar os conectores (source + sink)
```bash
bash scripts/registrar_conectores.sh
```
Aguarde ~30s. Verifique se os dados chegaram aos tópicos:
```bash
docker exec -it broker kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic postgres-dadostesouroipca --from-beginning --max-messages 5
```
Verifique os logs do Connect (não pode ter ERROR):
```bash
docker logs --tail 50 connect
```

**✅ ENTREGÁVEL 2 — print/log do Spark e dos pipelines:** guarde a saída acima.

## 10. Verificar a entrega no S3 (camada Bronze)
Console AWS → S3 → seu bucket → pasta `raw-data/kafka/...`. Devem aparecer arquivos
`.json`. Pode levar alguns segundos (o sink agrupa de 2 em 2 — `flush.size: 2`).

**✅ ENTREGÁVEL 3 — print dos dados no S3** (mostrando as pastas/partições e um JSON).

## 11. Silver e Gold com Spark
```bash
cd spark
docker-compose up -d        # usa o spark/.env com suas chaves AWS
```
Abra `http://localhost:8888`, faça upload de `notebooks/etl-spark.ipynb` e rode.
Ele lê o Bronze do S3, gera **Silver** (`processed-data/.../silver/`) e **Gold**
(`analytics/.../gold/`) em Parquet, de volta no S3.

**✅ Validação final:** confira no S3 as pastas `processed-data/.../silver/` e
`analytics/.../gold/` com arquivos `.parquet`.

---

## Encerrar tudo (quando terminar)
```bash
docker-compose down                 # na raiz (Confluent)
cd postgres && docker-compose down && cd ..
cd spark && docker-compose down && cd ..
```

## Segurança (importante)
- Após validar, **revogue a access key** `<SEU_ACCESS_KEY_ID>` no IAM e gere outra.
- Não suba `.env_kafka_connect`, `spark/.env` nem `cesar.xavier_accessKeys.csv` para o Git.

## Problemas comuns
| Sintoma | Causa provável | Solução |
|---|---|---|
| Connect com ERROR de S3 `AccessDenied` | política do bucket ou chave errada | revise passo 1.3 e o `.env` |
| Bucket "already exists" | nome não é único | escolha outro nome (passo 1.1) |
| Nada aparece no S3 | poucos registros < flush.size | aguarde ou rode importar.ipynb de novo |
| Spark `NoSuchMethodError`/s3a | jars incompatíveis | use as versões do `etl-spark.ipynb` (hadoop-aws 3.3.4) |
| `connection refused` no Postgres pelo Connect | rede | confirme `docker network create tesouro-net` antes de subir |
