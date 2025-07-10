
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

"""A standalone script to initialize the database schema."""

import anyio
import structlog
from pathlib import Path

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

async def initialize_database() -> None:
    """Connects to the database and executes the db_init.sql script."""
    try:
        from app.config import oracle_async
        from app.lib.settings import get_settings
    except ImportError:
        logger.error(
            "Could not import application components. "
            "Please ensure this script is run within the project's virtual environment (e.g., using 'uv run')."
        )
        return

    logger.info("Starting database initialization...")

    settings = get_settings()
    # Construct the absolute path to the SQL script
    # The script is in tools/deploy/oracle, and this script is in tools/
    sql_script_path = Path(__file__).parent / "deploy" / "oracle" / "db_init.sql"

    if not sql_script_path.exists():
        logger.error("Database init script not found!", path=str(sql_script_path))
        return

    logger.info("Found database script.", path=str(sql_script_path))

    try:
        async with oracle_async.get_connection() as conn:
            cursor = conn.cursor()
            logger.info("Successfully connected to the database.")
            try:
                sql_script = sql_script_path.read_text()
                # Split the script into individual statements based on the semicolon (;) delimiter.
                # This is a simple approach; for more complex scripts, a more robust parser might be needed.
                sql_statements = [
                    statement.strip()
                    for statement in sql_script.split(";")
                    if statement.strip()
                ]

                for statement in sql_statements:
                    # The script might contain PL/SQL blocks ending with a forward slash (/).
                    # We handle these by splitting the statement again.
                    for sub_statement in statement.split('/'):
                        if sub_statement.strip():
                            await cursor.execute(sub_statement)

                await conn.commit()
                logger.info("Database schema initialized successfully. ✅")
            finally:
                await cursor.close()
    except Exception as e:
        logger.error("An error occurred during database initialization.", error=str(e), exc_info=True)

if __name__ == "__main__":
    anyio.run(initialize_database)
