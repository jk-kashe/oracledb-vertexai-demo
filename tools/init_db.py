
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
    logger.info("Attempting to load application settings...")
    try:
        from dotenv import load_dotenv
        from app.lib.settings import get_settings

        # Explicitly load the .env file for this script
        env_file = Path(".env")
        if env_file.is_file():
            logger.info("Found .env file, loading environment variables.")
            load_dotenv(env_file, override=True)
            logger.info(".env file loaded.")
        else:
            logger.warning(".env file not found. Using environment variables.")

        settings = get_settings()
        logger.info("Application settings loaded successfully.")

    except ImportError as e:
        logger.error(
            "Could not import application components.",
            error=str(e),
            exc_info=True,
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
        logger.info("Using Autonomous Database configuration.")
        parsed_url = urlparse(settings.db.URL)
        user = parsed_url.username
        password = parsed_url.password
        dsn = parsed_url.hostname
    else:
        logger.info("Using standard database configuration.")
        user = settings.db.USER
        password = settings.db.PASSWORD
        dsn = settings.db.DSN

    if not all([user, password, dsn]):
        logger.error("Database credentials not found. Please check your .env file.")
        return

    try:
        # Construct the sqlplus command
        connect_string = f'{user}/"{password}"@{dsn}'
        command = ["sqlplus", "-S", connect_string, f"@{sql_script_path}"]

        logger.info("Executing command...", command=" ".join(command))

        # Use Popen to stream output in real-time for better debugging
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        logger.info("sqlplus process started. Reading output...")

        # Stream and log stdout
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                if line:
                    logger.info("sqlplus stdout:", line=line.strip())

        # Wait for the process to finish and capture stderr
        stdout, stderr = process.communicate()

        if stderr:
            logger.error("sqlplus stderr:", error=stderr.strip())

        if process.returncode != 0:
            logger.error(
                "Database initialization failed.",
                return_code=process.returncode,
            )
        else:
            logger.info("Database schema initialized successfully. ✅")

    except FileNotFoundError:
        logger.error("`sqlplus` command not found. Please ensure the Oracle Instant Client is installed and in your PATH.")
    except Exception as e:
        logger.error("An unexpected error occurred while running sqlplus.", error=str(e), exc_info=True)


if __name__ == "__main__":
    initialize_database()
