
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

"""A truly standalone script to initialize the database schema using sqlplus."""

import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import structlog
from dotenv import load_dotenv

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
    logger.info("Starting database initialization...")

    # Load environment variables from .env file
    env_path = Path(".env")
    if env_path.is_file():
        logger.info(f"Loading environment variables from {env_path.resolve()}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.warning(".env file not found. Relying on existing environment variables.")

    sql_script_path = Path(__file__).parent / "deploy" / "oracle" / "db_init.sql"

    if not sql_script_path.exists():
        logger.error("Database init script not found!", path=str(sql_script_path))
        return

    logger.info("Found database script.", path=str(sql_script_path))

    # Determine connection details from environment variables
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        logger.info("Using DATABASE_URL for Autonomous Database configuration.")
        parsed_url = urlparse(db_url)
        user = parsed_url.username
        password = parsed_url.password
        dsn = parsed_url.hostname
    else:
        logger.info("Using standard database configuration from environment.")
        user = os.getenv("DATABASE_USER", "app")
        password = os.getenv("DATABASE_PASSWORD", "super-secret")
        dsn = os.getenv("DATABASE_DSN")

    if not all([user, password, dsn]):
        logger.error("Database credentials not found. Please check your .env file.")
        return

    # Set TNS_ADMIN for wallet-based connections if the variable is set
    env = os.environ.copy()
    tns_admin_path = os.getenv("TNS_ADMIN")
    if tns_admin_path:
        env["TNS_ADMIN"] = tns_admin_path
        logger.info("TNS_ADMIN found in environment.", tns_admin=tns_admin_path)

    try:
        # Read the SQL script content
        sql_script_content = sql_script_path.read_text()

        # Construct the sqlplus command. We will pipe the script to stdin.
        connect_string = f'{user}/"{password}"@{dsn}'
        command = ["sqlplus", "-S", connect_string]

        logger.info("Executing sqlplus and piping script content to stdin...")

        # Use Popen and communicate to safely handle stdin, stdout, and stderr
        # This is the robust way to prevent deadlocks.
        process = subprocess.Popen(
            command, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            env=env
        )
        
        stdout, stderr = process.communicate(input=sql_script_content)

        # Log the output
        if stdout:
            logger.info("sqlplus output:", output=stdout.strip())
        if stderr:
            logger.error("sqlplus error:", error=stderr.strip())

        if process.returncode != 0:
            logger.error("Database initialization failed.", return_code=process.returncode)
        else:
            logger.info("Database schema initialized successfully. ✅")

    except FileNotFoundError:
        logger.error("`sqlplus` command not found. Please ensure the Oracle Instant Client is installed and in your PATH.")
    except Exception as e:
        logger.error("An unexpected error occurred.", error=str(e), exc_info=True)


if __name__ == "__main__":
    initialize_database()
