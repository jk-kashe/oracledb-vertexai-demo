#!/bin/bash

# Create tnsnames.ora
echo $ORACLE_TNS_NAMES > tnsnames.ora

# Run app
uv run app run