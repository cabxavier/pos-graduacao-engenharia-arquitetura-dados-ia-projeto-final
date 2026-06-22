#!/usr/bin/env bash
# Cria os dois tópicos Kafka (rode no host; usa o container "broker").
set -e
for TOPICO in postgres-dadostesouroipca postgres-dadostesouropre; do
  docker exec -i broker kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --partitions 1 --replication-factor 1 \
    --topic "$TOPICO" || true
done
echo "--- Tópicos ---"
docker exec -i broker kafka-topics --bootstrap-server localhost:9092 --list
