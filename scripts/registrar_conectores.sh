#!/usr/bin/env bash
# Registra os 2 source (JDBC) e os 2 sink (S3) no Kafka Connect.
set -e
CONNECT=http://localhost:8083/connectors
echo ">> Source IPCA";  curl -s -X POST -H "Content-Type: application/json" --data @connectors/source/connect_jdbc_postgres_ipca.config $CONNECT | head -c 300; echo
echo ">> Source PRE";   curl -s -X POST -H "Content-Type: application/json" --data @connectors/source/connect_jdbc_postgres_pre.config  $CONNECT | head -c 300; echo
echo ">> Sink IPCA";    curl -s -X POST -H "Content-Type: application/json" --data @connectors/sink/connect_s3_sink_ipca.config         $CONNECT | head -c 300; echo
echo ">> Sink PRE";     curl -s -X POST -H "Content-Type: application/json" --data @connectors/sink/connect_s3_sink_pre.config          $CONNECT | head -c 300; echo
echo; echo "--- Status dos conectores ---"
curl -s $CONNECT | tr ',' '\n'
