
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A standalone script to initialize the database schema using sqlplus."""

import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import structlog

# Configure structlog for standalone script logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


def initialize_database() -> None:
    """Connects to the database and executes the db_init.sql script."""
    try:
        from app.lib.settings import get_settings

        settings = get_settings()
    except ImportError:
        logger.error(
            "Could not import application components. "
            "Please ensure this script is run within the project's virtual environment (e.g., using 'uv run')."
        )
        return

    logger.info("Starting database initialization...")

    sql_script_path = Path(__file__).parent / "deploy" / "oracle" / "db_init.sql"

    if not sql_script_path.exists():
        logger.error("Database init script not found!", path=str(sql_script_path))
        return

    logger.info("Found database script.", path=str(sql_script_path))

    # Determine connection details based on configuration
    if settings.db.URL:
        # Autonomous Database configuration
        logger.info("Using Autonomous Database configuration.")
        parsed_url = urlparse(settings.db.URL)
        user = parsed_url.username
        password = parsed_url.password
        dsn = parsed_url.hostname
    else:
        # Standard Database configuration
        logger.info("Using standard database configuration.")
        user = settings.db.USER
        password = settings.db.PASSWORD
        dsn = settings.db.DSN

    if not all([user, password, dsn]):
        logger.error("Database credentials not found. Please check your .env file.")
        return

    try:
        # Construct the sqlplus command
        command = [
            "sqlplus",
            "-S",
            f"{user}/{password}@{dsn}",
            f"@{sql_script_path}",
        ]

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Log the output
        if result.stdout:
            logger.info("sqlplus output:", output=result.stdout)
        if result.stderr:
            logger.error("sqlplus error:", error=result.stderr)

        logger.info("Database schema initialized successfully. ✅")

    except FileNotFoundError:
        logger.error("`sqlplus` command not found. Please ensure the Oracle Instant Client is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        logger.error(
            "An error occurred while running sqlplus.",
            return_code=e.returncode,
            stdout=e.stdout,
            stderr=e.stderr,
            exc_info=True,
        )
    except Exception as e:
        logger.error("An unexpected error occurred.", error=str(e), exc_info=True)


if __name__ == "__main__":
    initialize_database()
