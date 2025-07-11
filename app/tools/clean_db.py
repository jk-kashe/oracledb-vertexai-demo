
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

"""A standalone script to drop the database user and all objects."""

import os
import subprocess
import logging
from pathlib import Path
from urllib.parse import urlparse

import structlog
from dotenv import load_dotenv

# Configure basic logging to show INFO level messages.
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Configure structlog for structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def clean_database() -> None:
    """Connects to the database and executes the drop_all.sql script."""
    logger.info("Starting database cleanup...")

    # Load environment variables from .env file
    env_path = Path(".env")
    if env_path.is_file():
        logger.info(f"Loading environment variables from {env_path.resolve()}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.warning(".env file not found. Relying on existing environment variables.")

    sql_script_path = Path(__file__).parent / "drop_all.sql"

    if not sql_script_path.exists():
        logger.error("Database drop script not found!", path=str(sql_script_path))
        return

    logger.info("Found database drop script.", path=str(sql_script_path))

    # Determine ADMIN connection details from environment variables
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        logger.info("Using DATABASE_URL for admin connection.")
        parsed_url = urlparse(db_url)
        admin_user = parsed_url.username
        admin_password = parsed_url.password
        dsn = parsed_url.hostname
    else:
        logger.info("Using standard database configuration for admin connection.")
        admin_user = os.getenv("DATABASE_USER")
        admin_password = os.getenv("DATABASE_PASSWORD")
        dsn = os.getenv("DATABASE_DSN")

    if not all([admin_user, admin_password, dsn]):
        logger.error("ADMIN database credentials not found. Please check your .env file.")
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

        # Construct the sqlplus command.
        connect_string = f'{admin_user}/"{admin_password}"@{dsn}'
        command = ["sqlplus", "-S", connect_string]

        logger.info("Executing sqlplus and piping script content to stdin...")

        # Use Popen and communicate to safely handle stdin, stdout, and stderr
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
            logger.error("Database cleanup failed.", return_code=process.returncode)
        else:
            logger.info("Database cleanup successful. ✅")

    except FileNotFoundError:
        logger.error("`sqlplus` command not found. Please ensure the Oracle Instant Client is installed and in your PATH.")
    except Exception as e:
        logger.error("An unexpected error occurred.", error=str(e), exc_info=True)


if __name__ == "__main__":
    clean_database()
