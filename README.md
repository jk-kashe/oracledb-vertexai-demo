# ☕ Oracle + Vertex AI Coffee Demo

An intelligent coffee recommendation system showcasing Oracle 23AI vector search with Google Vertex AI integration.

This fork of the original version is intended to work with Oracle Autonomous@GCP.

## 🚀 Quick Start

1. Create a new Google Cloud project.
2. Subscribe to Oracle Database@Google Cloud and complete account linking.
3. Open Cloud Shell and run the following commands:
```
git clone https://github.com/jk-kashe/oracledb-vertexai-demo
cd oracledb-vertexai-demo/tf
```
4. Create a new file called `terraform.tfvars` and enter the following, replacing `PROJECT_ID` with your project ID:
```
project_id = PROJECT_ID
```
5. Run the following commands and accept the deployment:
```
terraform init
terraform apply
```