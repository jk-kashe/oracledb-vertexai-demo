# ☕ Oracle + Vertex AI Coffee Demo

An intelligent coffee recommendation system showcasing Oracle 23AI vector search with Google Vertex AI integration.

This fork of the original version is intended to work with Oracle Autonomous@GCP.

## Terraform pre-requisites
1. Create a new Google Cloud project.
2. Subscribe to Oracle Database@Google Cloud and complete account linking.

## 🚀 Quick Start

**Note: Install autonomous db wallet (zip file) in oracle user home folder before continuing!**

```bash
# Install required packages
sudo apt install git unzip make

#!!!change to your wallet zip file name
sudo cp Wallet_YOURDB.zip /home/oracle/

sudo su - oracle #run as oracle user from this point
```

These commands should be run as oracle user

```bash
#clone
git clone https://github.com/jk-kashe/oracledb-vertexai-demo
cd oracledb-vertexai-demo
git checkout autonomous #will be moved to main

# Setup environment - follow the prerequisites below for details
make config

# Install dependencies, database and populate data
make install

# Start the application
make run
```

**Note: Embedding are included in the gzipped fixtures.**
If you'd like to regenerate embeddings, you can use:

```sh
uv run app load-vectors
```

### Add a firewall rule

To access the application from the internet, you need to open port `5006` on your client VM's firewall.

1.  In the Google Cloud Console, navigate to **VPC Network** -> **Firewall**.
2.  Click **CREATE FIREWALL RULE**.
3.  Configure the rule with the following settings:
    * **Name:** `coffee-app` (or another descriptive name)
    * **Targets:** `All instances in the network` (**Note:** This is for demo purposes. For production, you should apply the rule to a specific service account or network tag.)
    * **Source filter:** `IPv4 ranges`
    * **Source IPv4 ranges:** `0.0.0.0/0` (**Security Note:** It's much safer to use your own public IP address here. You can find it by searching for "what is my ip address".)
    * **Protocols and ports:**
        * Select **Specified protocols and ports**.
        * Check **TCP** and enter `5006`.
4.  Click **Create**.

### Finding Your VM's Public IP Address

To connect to the demo, you'll need the public IP address of your client VM.

1.  In the Google Cloud Console, navigate to **Compute Engine** > **VM instances**.
2.  Find your client VM in the list.
3.  The public IP address is listed in the **External IP** column. Copy this address to use in your browser.


Visit http://your-client-vm-public-ip:5006 to try the demo!

## Prerequisites

### Autonomous Database and Client VM

It is assumed that you have Oracle Autonomous@GCP and a client machine configured. These steps are currently out of scope for this guide.

## Additional configuration notes

#### GOOGLE_PROJECT_ID

1. in the GCP console, click on "My First Project" (or another project you are using)
2. Copy the ID (not Name!)
3. Update the `GOOGLE_PROJECT_ID` variable in your `.env` file with the project ID you copied.

#### API KEY

##### Step 1: Navigate to the Credentials Page


   1. Go to the Google Cloud Console: https://console.cloud.google.com/ (https://console.cloud.google.com/)
   2. Make sure the correct GCP project (the one where you have your Autonomous Database and will run your application) is selected
      at the top of the page.
   3. Open the navigation menu (the "hamburger" icon ☰) in the top-left corner.
   4. Go to APIs & Services > Credentials.

#####  Step 2: Create the API Key

   1. On the Credentials page, click the + CREATE CREDENTIALS button at the top.
   2. Select API key from the dropdown menu.
   3. A dialog box will appear showing your newly created API key. Copy this key immediately. You will use this value in your .env
      file.

#####  Step 3: Secure Your API Key (Highly Recommended)

  An unrestricted API key is a security risk. Anyone who finds it can use it and generate charges on your account. You should
  always restrict your keys.

   1. In the dialog box that showed your new key, click EDIT API KEY (or find the key in the list on the Credentials page and click
      the pencil icon to edit it).
   2. Under Key restrictions, apply the following:
       * Application restrictions: Since this is a backend application, the best practice is to restrict the key to the IP address
         of the server where it will run. Select IP addresses (web servers, cron jobs, etc.) and add the IP address of the GCE
         instance you plan to use.
       * API restrictions: Select Restrict key. From the dropdown, choose the specific APIs the key should be allowed to call. For
         this project, you will need to enable the Vertex AI API.

#####  Step 4: Enable the Necessary APIs

  An API key only grants access to APIs that you have explicitly enabled for your project.

   1. Open the navigation menu (☰) again.
   2. Go to APIs & Services > Library.
   3. Search for Vertex AI API.
   4. Click on it and then click the Enable button. If it's already enabled, you're all set.
   5. The .env.example file also mentions "maps-and-stuff". If you were to add a feature that uses Google Maps (e.g., to show shop
      locations), you would also need to search for and enable the Maps JavaScript API or other relevant mapping APIs here.





## 🖼️ Screenshots

### Coffee Chat Interface

![Cymbal Coffee Chat Interface](docs/screenshots/cymbal_chat.png)
_AI-powered coffee recommendations with real-time performance metrics_

### Performance Dashboard

![Performance Dashboard](docs/screenshots/performance_dashboard.png)
_Live monitoring of Oracle vector search performance and system metrics_

## 📚 Documentation

For complete implementation and development guides, see the [`docs/system/`](docs/system/) directory:

- **[Technical Overview](docs/system/01-technical-overview.md)** - High-level technical concepts
- **[Oracle Architecture](docs/system/02-oracle-architecture.md)** - Oracle 23AI unified platform
- **[Implementation Guide](docs/system/05-implementation-guide.md)** - Step-by-step build guide

### Recent Architecture Updates

- **[Architecture Updates](docs/architecture-updates.md)** - Recent improvements including:
  - Native HTMX integration with Litestar
  - Centralized exception handling system
  - Unified cache information API
  - Enhanced cache hit tracking
- **[HTMX Events Reference](docs/htmx-events.md)** - Complete list of custom HTMX events
- **[HTMX Migration Summary](docs/htmx-migration-summary.md)** - Details of the HTMX native integration
- **[Demo Scenarios](docs/system/07-demo-scenarios.md)** - Live demonstration scripts

## 🏗️ Architecture

This demo uses:

- **Oracle 23AI** - Complete data platform with native vector search
- **Vertex AI** - Google's generative AI platform for embeddings and chat
- **Minimal Abstractions** - Direct Oracle database access for clarity (and performance). No ORM
- **Litestar** - High-performance async Python framework
- **HTMX** - Real-time UI updates without JavaScript complexity

## 🎯 Key Features

This implementation is designed for conference demonstration with:

- **Real-time Chat Interface** - Personalized coffee recommendations with AI personas
- **Live Performance Metrics** - Oracle vector search timing and cache hit rates
- **In-Memory Caching** - High-performance response caching using Oracle
- **Native Vector Search** - Semantic similarity search without external dependencies
- **Intent Routing** - Natural language understanding via exemplar matching
- **Performance Dashboard** - Real-time monitoring of all system components

## 🔧 Development Commands

```bash
# Database operations
uv run app load-fixtures        # Load sample data
uv run app load-vectors         # Generate embeddings
uv run app truncate-tables      # Reset all data
uv run app clear-cache          # Clear response cache

# Export/Import (for faster demo startup)
uv run app dump-data           # Export all data with embeddings
uv run app dump-data --table intent_exemplar  # Export specific table
uv run app dump-data --path /tmp/backup --no-compress  # Custom options

# Development
uv run app run                 # Start the application
uv run pytest                  # Run tests
make lint                      # Code quality checks
```

## 📖 Additional Resources

- [Original Blog Post](https://cloud.google.com/blog/topics/partners/ai-powered-coffee-nirvana-runs-on-oracle-database-on-google-cloud/) - Origin story
- [Oracle 23AI Vector Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/vecse/) - Vector search documentation
- [Litestar Documentation](https://docs.litestar.dev) - Framework documentation
- [System Documentation](docs/system/) - Complete technical guides
