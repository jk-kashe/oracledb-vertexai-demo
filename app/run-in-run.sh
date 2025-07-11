#!/bin/bash

# Create tnsnames.ora
echo $ORACLE_TNSNAMES > tnsnames.ora

# Set port
export LITESTAR_PORT=$PORT

# Run app
uv run app run