
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

"""An interactive script to configure the project environment."""

import getpass
import os
import subprocess
from pathlib import Path
import shutil

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


def configure_environment() -> None:
    """Interactively configures the project environment."""
    logger.info("Starting interactive configuration...")

    # --- Get user input ---
    wallet_zip_path_str = input("Enter the full path to your wallet.zip file: ").strip()
    wallet_zip_path = Path(wallet_zip_path_str)

    if not wallet_zip_path.is_file():
        logger.error("Wallet zip file not found at the specified path.", path=wallet_zip_path)
        return

    db_password = getpass.getpass("Enter your Autonomous Database ADMIN user password: ")
    wallet_password = getpass.getpass("Enter your wallet password: ")

    print("\n--- Google Cloud Platform Configuration ---")
    print("You can find your Project ID by selecting your project in the GCP Console.")
    google_project_id = input("Enter your Google Cloud Project ID: ").strip()

    print("\nYou can create or find your API Key at: https://console.cloud.google.com/apis/credentials")
    google_api_key = getpass.getpass("Enter your Google Cloud API Key: ")

    # --- Configure Wallet ---
    logger.info("Configuring Oracle Wallet...")
    wallet_dir = Path.home() / "wallet"

    try:
        if not wallet_dir.exists():
            logger.info(f"Creating new wallet directory at {wallet_dir}")
            wallet_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(["unzip", "-o", str(wallet_zip_path), "-d", str(wallet_dir)], check=True)
            logger.info("Wallet unzipped successfully.")
        else:
            logger.info(f"Using existing wallet directory at {wallet_dir}")

        sqlnet_ora_path = wallet_dir / "sqlnet.ora"
        if sqlnet_ora_path.exists():
            lines = sqlnet_ora_path.read_text().splitlines(True)
            if lines and not lines[0].strip().startswith('#'):
                logger.info("First line of sqlnet.ora is not commented. Commenting it out.")
                lines[0] = '#' + lines[0]
                sqlnet_ora_path.write_text("".join(lines))
            else:
                logger.info("First line of sqlnet.ora is already commented or file is empty.")
        else:
            logger.warning(f"sqlnet.ora not found in wallet directory: {wallet_dir}")

        tns_admin_path = wallet_dir.resolve()
        ora_client_env_path = Path.home() / ".ora_client.env"
        with open(ora_client_env_path, "w") as f:
            f.write(f"export TNS_ADMIN={tns_admin_path}\n")
        logger.info(f"TNS_ADMIN set in {ora_client_env_path}")

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error("Failed to configure wallet.", error=str(e), exc_info=True)
        return

    # --- Create and populate .env file ---
    logger.info("Creating and configuring .env file...")
    env_autonomous_path = Path(".env.autonomous")
    env_path = Path(".env")

    if not env_autonomous_path.exists():
        logger.error(".env.autonomous file not found. Cannot create .env.")
        return

    shutil.copy(env_autonomous_path, env_path)

    # Update passwords
    with open(env_path, "r") as f:
        lines = f.readlines()

    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("DATABASE_URL="):
                f.write(f'DATABASE_URL="oracle+oracledb://ADMIN:{db_password}@ora_medium"\n')
            elif line.startswith("WALLET_PASSWORD="):
                f.write(f'WALLET_PASSWORD="{wallet_password}"\n')
            elif line.startswith("GOOGLE_PROJECT_ID="):
                f.write(f'GOOGLE_PROJECT_ID={google_project_id}\n')
            elif line.startswith("GOOGLE_API_KEY="):
                f.write(f'GOOGLE_API_KEY={google_api_key}\n')
            else:
                f.write(line)
    logger.info("Database and wallet passwords updated in .env file.")

    # --- Generate and insert SECRET_KEY ---
    logger.info("Generating and adding SECRET_KEY...")
    try:
        secret_key = subprocess.check_output(["openssl", "rand", "-hex", "32"]).decode("utf-8").strip()
        
        with open(env_path, "r") as f:
            lines = f.readlines()

        key_exists = False
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("SECRET_KEY="):
                    f.write(f"SECRET_KEY={secret_key}\n")
                    key_exists = True
                else:
                    f.write(line)
            if not key_exists:
                f.write(f"\nSECRET_KEY={secret_key}\n")

        logger.info("SECRET_KEY generated and updated in .env file.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error("Failed to generate SECRET_KEY. Please generate it manually.", error=str(e), exc_info=True)

    logger.info("Configuration complete! 🎉")
    logger.info("Please ensure GOOGLE_PROJECT_ID and GOOGLE_API_KEY are set in your .env file.")


if __name__ == "__main__":
    configure_environment()
