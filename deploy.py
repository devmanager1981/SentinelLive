"""
Sentinel Live - Cloud Run Deployment Script
Deploys backend and frontend from separate deploy directories.
Works on Windows (PowerShell) and Linux/Mac.
"""

import os
import sys
import shutil
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Configuration
REGION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "").strip().strip('"\'')
FIRESTORE_DB = os.getenv("GOOGLE_FIRESTORE_DB", "").strip().strip('"\'')
API_KEY = os.getenv("GOOGLE_AISTUDIO_KEY", "").strip().strip('"\'')
BACKEND_SERVICE = "sentinel-backend"
FRONTEND_SERVICE = "sentinel-frontend"


def run(cmd, check=True):
    """Run a shell command and print output."""
    print(f"\n> {cmd}\n")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if check and result.returncode != 0:
        print(f"\nCommand failed with exit code {result.returncode}")
        sys.exit(1)
    return result


def stage_files(target_dir, source_dirs):
    """Copy source files into deploy target directory."""
    for src in source_dirs:
        dest = os.path.join(target_dir, os.path.basename(src))
        if os.path.isdir(src):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
    print(f"Staged files into {target_dir}")


def cleanup(target_dir, names):
    """Remove staged files from deploy directory."""
    for name in names:
        path = os.path.join(target_dir, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)
    print(f"Cleaned up {target_dir}")


def get_service_url(service):
    """Get the URL of a deployed Cloud Run service."""
    result = subprocess.run(
        f'gcloud run services describe {service} --region {REGION} --format "value(status.url)"',
        shell=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def main():
    print("=" * 50)
    print("Sentinel Live - Cloud Run Deployment")
    print("=" * 50)

    # Validate
    if not API_KEY:
        print("ERROR: GOOGLE_AISTUDIO_KEY not set in .env")
        sys.exit(1)
    if not PROJECT_ID:
        print("ERROR: GOOGLE_PROJECT_ID not set in .env")
        sys.exit(1)
    if not FIRESTORE_DB:
        print("ERROR: GOOGLE_FIRESTORE_DB not set in .env")
        sys.exit(1)

    print(f"\nProject:  {PROJECT_ID}")
    print(f"Region:   {REGION}")
    print(f"Database: {FIRESTORE_DB}")
    print(f"API Key:  {API_KEY[:8]}...{API_KEY[-4:]}")

    # Set project
    run(f"gcloud config set project {PROJECT_ID}")

    # Enable APIs
    print("\nEnabling required APIs...")
    run("gcloud services enable run.googleapis.com cloudbuild.googleapis.com firestore.googleapis.com --quiet")

    # Build env vars string (no quotes, gcloud handles it)
    backend_env = f"GOOGLE_AISTUDIO_KEY={API_KEY},GOOGLE_PROJECT_ID={PROJECT_ID},GOOGLE_FIRESTORE_DB={FIRESTORE_DB}"

    # ---- BACKEND ----
    print("\n" + "=" * 50)
    print("Deploying Backend")
    print("=" * 50)

    stage_files("deploy/backend", ["requirements.txt", "server"])

    run(
        f"gcloud run deploy {BACKEND_SERVICE}"
        f" --source deploy/backend"
        f" --platform managed"
        f" --region {REGION}"
        f" --allow-unauthenticated"
        f' --set-env-vars "{backend_env}"'
        f" --memory 1Gi"
        f" --cpu 1"
        f" --timeout 300"
        f" --max-instances 10"
        f" --min-instances 0"
        f" --port 8080"
    )

    cleanup("deploy/backend", ["requirements.txt", "server"])

    backend_url = get_service_url(BACKEND_SERVICE)
    print(f"\nBackend deployed at: {backend_url}")

    # ---- FRONTEND ----
    print("\n" + "=" * 50)
    print("Deploying Frontend")
    print("=" * 50)

    stage_files("deploy/frontend", ["requirements.txt", "web"])

    frontend_env = f"{backend_env},BACKEND_URL={backend_url}"

    run(
        f"gcloud run deploy {FRONTEND_SERVICE}"
        f" --source deploy/frontend"
        f" --platform managed"
        f" --region {REGION}"
        f" --allow-unauthenticated"
        f' --set-env-vars "{frontend_env}"'
        f" --memory 1Gi"
        f" --cpu 1"
        f" --timeout 300"
        f" --max-instances 10"
        f" --min-instances 0"
        f" --port 8501"
    )

    cleanup("deploy/frontend", ["requirements.txt", "web"])

    frontend_url = get_service_url(FRONTEND_SERVICE)
    print(f"\nFrontend deployed at: {frontend_url}")

    # ---- SUMMARY ----
    print("\n" + "=" * 50)
    print("Deployment Complete!")
    print("=" * 50)
    print(f"\nBackend URL:  {backend_url}")
    print(f"Frontend URL: {frontend_url}")
    print(f"\nNext steps:")
    print(f"1. Open {frontend_url} in your browser")
    print(f"2. Click 'Establish Neural Link'")
    print(f"3. Update .env: BACKEND_URL={backend_url}")
    print(f"4. Run: python streamer.py")


if __name__ == "__main__":
    main()
