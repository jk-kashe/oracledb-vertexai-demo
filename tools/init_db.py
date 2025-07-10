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

"""
A standalone script to initialize the database schema using sqlplus.
This script reads the application's configuration to connect to the database.
"""

import os
import subprocess
from pathlib import Path

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
    """
    Connects to the database using sqlplus and executes the db_init.sql script.
    """
    try:
        # Dynamically import settings from the application
        from app.lib.settings import get_settings

        settings = get_settings()
        logger.info("Successfully loaded application settings.")
    except ImportError:
        logger.error(
            "Could not import application components. "
            "Please ensure this script is run from the project root "
            "within the project's virtual environment (e.g., using 'uv run')."
        )
        return

    logger.info("Starting database initialization...")

    # The SQL script is located relative to this file's parent directory
    sql_script_path = Path(__file__).parent / "deploy" / "oracle" / "db_init.sql"

    if not sql_script_path.exists():
        logger.error("Database init script not found!", path=str(sql_script_path))
        return

    logger.info("Found database script.", path=str(sql_script_path))

    # Get database credentials from settings.
    # The user should be a privileged user (e.g., ADMIN) that can run the script.
    user = settings.db.USER
    password = settings.db.PASSWORD
    dsn = settings.db.DSN

    if not all([user, password, dsn]):
        logger.error(
            "Database credentials (USER, PASSWORD, DSN) not found in settings. "
            "Please check your .env file."
        )
        return

    # For Autonomous Database, the wallet (config_dir) must be set up.
    # We set the TNS_ADMIN environment variable to point to the wallet directory.
    env = os.environ.copy()
    if settings.db.config_dir:
        tns_admin = str(Path(settings.db.config_dir).resolve())
        env["TNS_ADMIN"] = tns_admin
        logger.info(
            "TNS_ADMIN set for Autonomous Database connection.", tns_admin=tns_admin
        )

    try:
        # Construct the sqlplus command.
        # The connection string is in the format: user/password@dsn
        # The -S flag runs sqlplus in "silent" mode.
        connect_string = f"{user}/{password}@{dsn}"
        command = ["sqlplus", "-S", connect_string, f"@{sql_script_path}"]

        logger.info("Executing database initialization script via sqlplus...")

        # Execute the command. We capture stdout and stderr.
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=env,
            check=False,  # We check the return code manually
        )

        # Log the output from sqlplus
        if process.stdout:
            # The script enables DBMS_OUTPUT, so we log it here.
            logger.info("sqlplus output:", output=process.stdout.strip())
        if process.stderr:
            logger.error("sqlplus error:", error=process.stderr.strip())

        # Check if the command was successful
        if process.returncode != 0:
            logger.error(
                "Database initialization failed.",
                return_code=process.returncode,
            )
        else:
            logger.info("Database schema initialized successfully. ✅")

    except FileNotFoundError:
        logger.error(
            "`sqlplus` command not found. "
            "Please ensure the Oracle Instant Client is installed and in your PATH."
        )
    except Exception as e:
        logger.error(
            "An unexpected error occurred while running sqlplus.",
            error=str(e),
            exc_info=True,
        )


if __name__ == "__main__":
    initialize_database()