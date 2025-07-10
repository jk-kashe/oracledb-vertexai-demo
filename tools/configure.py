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

"""An interactive script to configure the project environment with masked input."""

import os
import subprocess
import shutil
import sys
from pathlib import Path

# For masked password input
try:
    import termios
    import tty
    UNIX_PLATFORM = True
except ImportError:
    UNIX_PLATFORM = False

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

def getpass_masked(prompt: str = "Password: ") -> str:
    """Reads a password from the terminal with character masking.

    Args:
        prompt: The prompt to display to the user.

    Returns:
        The password entered by the user.
    """
    if not UNIX_PLATFORM:
        # Fallback for non-Unix platforms (like Windows)
        import getpass
        return getpass.getpass(prompt)

    print(prompt, end='', flush=True)
    password = []
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            char = sys.stdin.read(1)
            if char in ('\r', '\n'):
                print()
                break
            if char == '\x7f':  # Backspace
                if password:
                    password.pop()
                    # Move cursor back, print space, move back again
                    print('\b \b', end='', flush=True)
            elif char == '\x03': # Ctrl+C
                raise KeyboardInterrupt
            else:
                password.append(char)
                print('*', end='', flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return "".join(password)

def configure_environment() -> None:
    """Interactively configures the project environment."""
    logger.info("Starting interactive configuration...")

    # --- Get user input ---
    home_dir = Path.home()
    wallet_files = list(home_dir.glob("Wallet*.zip"))

    if len(wallet_files) == 1:
        print(f"Found one wallet file: {wallet_files[0]}")
        use_found_wallet = input("Use this wallet? (Y/n): ").strip().lower()
        if use_found_wallet in ['', 'y', 'yes']:
            wallet_zip_path = wallet_files[0]
        else:
            wallet_zip_path_str = input("Enter the full path to your wallet.zip file: ").strip()
            wallet_zip_path = Path(wallet_zip_path_str)
    elif len(wallet_files) > 1:
        print("Found multiple wallet files:")
        for i, f in enumerate(wallet_files):
            print(f"  {i + 1}: {f}")
        while True:
            try:
                choice = int(input(f"Select a wallet to use (1-{len(wallet_files)}): "))
                if 1 <= choice <= len(wallet_files):
                    wallet_zip_path = wallet_files[choice - 1]
                    break
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a number.")
    else:
        logger.info("No wallet files found in home directory.")
        wallet_zip_path_str = input("Enter the full path to your wallet.zip file: ").strip()
        wallet_zip_path = Path(wallet_zip_path_str)

    if not wallet_zip_path.is_file():
        logger.error("Wallet zip file not found at the specified path.", path=wallet_zip_path)
        return

    db_password = getpass_masked("Enter your Autonomous Database ADMIN user password: ")
    wallet_password = getpass_masked("Enter your wallet password: ")

    print("\n--- Google Cloud Platform Configuration ---")
    print("To find your Google Cloud Project ID:")
    print("1. Go to the Google Cloud Console: https://console.cloud.google.com/")
    print("2. At the top of the page, click on the project name to open the 'Select a project' dialog.")
    print("3. Click on the project name to open the 'Select a project' dialog.")
    print("4. In the dialog, a list of your projects will appear.")
    print("5. Find the project you are using for this demo and copy its 'ID' (e.g., 'single-clock-1234-s1').")
    print("   Do not use the 'Name'.") 
    google_project_id = input("Enter your Google Cloud Project ID: ").strip()

    print("\n--- Google Cloud API Key ---")
    print("To create or find your API Key, go to: https://console.cloud.google.com/apis/credentials")
    print("2. Click the '+ CREATE CREDENTIALS' button at the top.")
    print("3. Select 'API key' from the dropdown menu.")
    print("4. A dialog box will appear showing your new key. Copy this key.")
    print("\nIt is highly recommended to restrict your API key for security:")
    print("1. In the dialog box, click 'EDIT API KEY'.")
    print("2. Under 'API restrictions', select 'Restrict key'.")
    print("3. From the dropdown, select the 'Vertex AI API'.")
    print("   (You may need to enable the Vertex AI API in the API Library first.)")
    google_api_key = getpass_masked("Enter your Google Cloud API Key: ")

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
                lines[0] = '#' + lines[0]
                sqlnet_ora_path.write_text("".join(lines))

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

    lines = env_path.read_text().splitlines()
    key_exists = { "SECRET_KEY": False }

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
            elif line.startswith("SECRET_KEY="):
                key_exists["SECRET_KEY"] = True
                secret_key = subprocess.check_output(["openssl", "rand", "-hex", "32"]).decode("utf-8").strip()
                f.write(f"SECRET_KEY={secret_key}\n")
            else:
                f.write(line + '\n')
        
        if not key_exists["SECRET_KEY"]:
            secret_key = subprocess.check_output(["openssl", "rand", "-hex", "32"]).decode("utf-8").strip()
            f.write(f"SECRET_KEY={secret_key}\n")

    logger.info("Configuration complete! 🎉")
    logger.info("You can now run 'make install' to set up the database and dependencies.")


if __name__ == "__main__":
    try:
        configure_environment()
    except KeyboardInterrupt:
        print("\nConfiguration cancelled by user.")