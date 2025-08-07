# app.py - NEW VERSION FOR RUNPOD
import os
import requests
from flask import Flask, redirect, request, send_file, send_from_directory
from datetime import datetime, timezone, timedelta
import sys
sys.stdout.reconfigure(encoding='utf-8')
import subprocess

app = Flask(__name__)

# --- Configuration ---
# Paste the Vercel URL you copied in Part 2
SECURE_PROXY_URL = "https://patreon-proxy.vercel.app/api/get-file" 
# This should be the same public callback helper you used before
PATREON_HELPER_CALLBACK = os.environ.get("PATREON_HELPER_CALLBACK", "https://maxed-out-99.github.io/patreon-auth/callback.html")
CLIENT_ID = os.environ.get("PATREON_CLIENT_ID") # Client ID is public, so it's fine here

@app.route("/")
def index():
    return send_file("/workspace/auth/index.html")

@app.route("/success")
def success():
    return send_file("/workspace/auth/success.html")

@app.route("/auth")
def auth():
    pod_id = os.environ.get("RUNPOD_POD_ID")
    port = os.environ.get("RUNPOD_PORT_7860_TCP_PORT", "7860")
    pod_specific_callback = f"https://{pod_id}-{port}.proxy.runpod.net/callback"
    auth_url = (
        f"https://www.patreon.com/oauth2/authorize?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={PATREON_HELPER_CALLBACK}"
        f"&scope=identity identity.memberships"
        f"&state={pod_specific_callback}"
    )
    return redirect(auth_url)

@app.route("/callback")
@app.route("/callback/")
def callback():
    code = request.args.get("code")
    if not code:
        return "No code provided", 400

    # Your existing check for a recent unlock is good
    if os.path.exists("/workspace/.flux_token"):
        # ... (your timestamp checking logic) ...
        return redirect("/success")

    print("📞 Calling secure proxy to verify and download files...")
    try:
        # --- Download the main workflow ---
        proxy_response_workflow = requests.post(SECURE_PROXY_URL, json={"code": code, "file_type": "workflow"})
        if proxy_response_workflow.status_code != 200:
            return "Failed to get workflow file from proxy.", 403
        
        workflow_path = "/workspace/ComfyUI/user/default/workflows/Mega Flux v1.json"
        os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
        with open(workflow_path, "wb") as f:
            f.write(proxy_response_workflow.content)
        print("✅ Main workflow downloaded.")

        # --- Download the helper scripts ---
        scripts_dir = "/workspace/scripts"
        os.makedirs(scripts_dir, exist_ok=True)
        script_map = {
            "script_download_all": "download_all_mega_files.py",
            "script_download_small": "download_small_mega_files.py",
            "script_download_fp8": "download_all_mega_files_fp8.py"
        }

        for file_type, script_name in script_map.items():
            proxy_response_script = requests.post(SECURE_PROXY_URL, json={"code": code, "file_type": file_type})
            if proxy_response_script.status_code == 200:
                with open(os.path.join(scripts_dir, script_name), "wb") as f:
                    f.write(proxy_response_script.content)
                print(f"✅ Helper script '{script_name}' downloaded.")
            else:
                 print(f"❌ Failed to download '{script_name}'.")
                 # Decide if you want to fail the whole process if one script fails
                 return f"Failed to download script {script_name} from proxy.", 500

        # If everything downloaded successfully, create the token
        with open("/workspace/.flux_token", "w") as f:
            f.write(datetime.now(timezone.utc).isoformat())

        return redirect("/success")

    except requests.exceptions.RequestException as e:
        return f"Error connecting to the secure proxy: {e}", 500

# Keep your other routes for serving images, status pages, etc.
# They do not need to be changed.
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('/workspace/auth/images', filename)

@app.route('/download/<version>')
def download_mega(version):
    # This route which EXECUTES the scripts downloaded in /callback remains the same.
    # The key difference is the scripts no longer contain any secrets.
    # (Your existing code for this route is fine)
    script_map = {
        "all": "download_all_mega_files.py",
        "small": "download_small_mega_files.py",
        "all_fp8": "download_all_mega_files_fp8.py"
    }

    if version not in script_map:
        return "Invalid version specified", 404

    script_name = script_map[version]
    script_path = os.path.join("/workspace/scripts", script_name)
    
    if not os.path.exists(script_path):
        return f"Script {script_name} not found.", 500

    log_file_path = "/workspace/logs/power_user_downloads.log"
    done_file = f"/workspace/logs/download_{version}.done"
    
    # Ensure the /workspace/logs directory exists before trying to write to it.
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Clean up old files before starting a new download
    if os.path.exists(done_file):
        os.remove(done_file)
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    try:
        # Open the log file in append mode and start the process
        with open(log_file_path, "a") as log_file:
            print(f"🚀 Starting download for '{version}'. Log: {log_file_path}")
            subprocess.Popen(
                ["python3", "-u", script_path], # Added -u for unbuffered output
                stdout=log_file, 
                stderr=subprocess.STDOUT,
                cwd="/workspace/scripts"
            )
    except Exception as e:
        print(f"🔥🔥🔥 CRITICAL ERROR trying to start subprocess for {script_name} 🔥🔥🔥")
        print(f"Exception: {e}")
        return "An unexpected error occurred while trying to start the download.", 500

    # Redirect to the existing status-checking page
    return redirect(f"/downloading/{version}")
    
# ... rest of your existing routes (downloading_page, download_status, etc.)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
