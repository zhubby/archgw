#!/bin/bash
set -eu

# for demo in currency_exchange hr_agent
for demo in currency_exchange
do
  echo "******************************************"
  echo "Running tests for $demo ..."
  echo "****************************************"
  cd ../../samples_python/$demo
  archgw up arch_config.yaml
  docker compose up -d
  cd ../../shared/test_runner
  TEST_DATA=../../samples_python/$demo/test_data.yaml poetry run pytest
  cd ../../samples_python/$demo
  archgw down
  docker compose down -v
  cd ../../shared/test_runner
done
