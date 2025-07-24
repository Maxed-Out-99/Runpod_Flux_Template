import os
import json
import requests
from flask import Flask, redirect, request, send_file, send_from_directory
import subprocess
from datetime import datetime, timedelta, timezone
import sys
sys.stdout.reconfigure(encoding='utf-8')


app = Flask(__name__)

# THIS IS YOUR NEW STATIC HELPER URL FROM STEP 2
# Set it as an environment variable in your RunPod Template for best practice
PATREON_HELPER_CALLBACK = os.environ.get("PATREON_HELPER_CALLBACK", "https://maxed-out-99.github.io/patreon-auth/callback.html")

def get_env_var(key, required=True, default=None):
    # ... (rest of the function is the same) ...
    value = os.environ.get(key)
    if value is None:
        if required:
            raise RuntimeError(f"❌ Missing required environment variable: {key}")
        return default
    return value.strip()

# ✅ Use safe env var access
CLIENT_ID = get_env_var("PATREON_CLIENT_ID")
CLIENT_SECRET = get_env_var("PATREON_CLIENT_SECRET")
CAMPAIGN_ID = "13913714"
REQUIRED_TIER = "⚡ Power User"

def download_flux_workflow():
    print("📦 Starting Power User workflow download...")

    hf_token = get_env_var("HF_TOKEN")
    if not hf_token:
        print("❌ Hugging Face token not found.")
        return "❌ HF_TOKEN not set.", 500

    url = "https://huggingface.co/MaxedOut/Power-User-Tools/resolve/main/workflows/Mega%20Flux%20v1.json"
    output_path = "/workspace/ComfyUI/user/default/workflows/Mega Flux v1.json"

    print(f"🔗 Download URL: {url}")
    print(f"📁 Target path: {output_path}")
    print("🔐 Using Hugging Face token.")

    command = [
        "curl", "-L",
        "-H", f"Authorization: Bearer {hf_token}",
        url,
        "-o", output_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ CURL failed to download file.")
        print("📄 STDERR:", result.stderr.strip())
        print("📄 STDOUT:", result.stdout.strip())
        return "❌ Failed to download Power User file.", 500

    if not os.path.exists(output_path):
        print("⚠️ CURL completed but file not found at target path.")
        return "❌ File not saved.", 500

    print("✅ Power User file downloaded successfully.")
    print(f"📦 Saved to: {output_path}")
    return "✅ File downloaded", 200

# + NEW, MORE RELIABLE CODE
def download_mega_scripts():
    print("📥 Downloading Mega helper scripts...")
    hf_token = get_env_var("HF_TOKEN")
    if not hf_token:
        return "❌ HF_TOKEN not set.", 500

    base_url = "https://huggingface.co/MaxedOut/Power-User-Tools/resolve/main/scripts/"
    scripts = ["download_all_mega_files.py", "download_small_mega_files.py"]
    scripts_dir = "/workspace/scripts"
    os.makedirs(scripts_dir, exist_ok=True) # Ensure directory exists
    
    all_scripts_downloaded = True # Flag to track success

    for script in scripts:
        url = f"{base_url}{script}"
        output_path = os.path.join(scripts_dir, script)
        command = ["curl", "-L", "-H", f"Authorization: Bearer {hf_token}", url, "-o", output_path]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0 or not os.path.exists(output_path):
            print(f"❌ FAILED to download {script}.")
            print(f"📄 STDERR: {result.stderr.strip()}")
            all_scripts_downloaded = False # Set flag to false on failure
        else:
            print(f"✅ {script} downloaded successfully.")

    if all_scripts_downloaded:
        return "✅ All helper scripts downloaded.", 200
    else:
        return "❌ Failed to download one or more helper scripts.", 500

@app.errorhandler(404)
def not_found(e):
    return redirect("/")

@app.route("/success")
def success():
    print("✅ Success page reached.")
    return send_file("/workspace/auth/success.html")

# NEW CODE -- USE THIS INSTEAD
@app.route("/")
def index():
    print("✅ Index page served.")
    return send_file("/workspace/auth/index.html")

# Step 1: Start auth
@app.route("/auth")
def auth():
    # Get the pod ID and port number reliably from RunPod's environment variables
    pod_id = get_env_var("RUNPOD_POD_ID")
    port = get_env_var("RUNPOD_PORT_7860_TCP_PORT", required=False, default="7860") # Default to 7860 if not found

    # Construct the reliable public proxy URL
    pod_specific_callback = f"https://{pod_id}-{port}.proxy.runpod.net/callback"

    # The rest of the function remains the same
    auth_url = (
        f"https://www.patreon.com/oauth2/authorize?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={PATREON_HELPER_CALLBACK}"
        f"&scope=identity%20identity.memberships"
        f"&state={pod_specific_callback}"
    )
    return redirect(auth_url)

# Step 2: Handle callback and check membership
@app.route("/callback")
@app.route("/callback/")
def callback():
    code = request.args.get("code")
    if os.path.exists("/workspace/.flux_token"):
        with open("/workspace/.flux_token") as f:
            try:
                ts = datetime.fromisoformat(f.read().strip())
                # Use timezone.utc to correctly compare with the saved timestamp
                if datetime.now(timezone.utc) - ts <= timedelta(hours=24):
                    print("✅ Already unlocked within last 24h")
                    return redirect("/success")
            except Exception as e:
                
                print(f"⚠️ Couldn't parse timestamp: {e}")
                os.remove("/workspace/.flux_token")

    if not code:
        return "No code provided", 400

    token_resp = requests.post("https://www.patreon.com/api/oauth2/token", data={
        "code": code,
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": PATREON_HELPER_CALLBACK
    }).json()

    access_token = token_resp.get("access_token")
    if not access_token:
        print(f"❌ Failed to get access token. Patreon response: {token_resp}")
        return "Failed to get access token", 400

    api_url = (
        "https://www.patreon.com/api/oauth2/v2/identity"
        "?include=memberships.currently_entitled_tiers"
        "&fields[user]=full_name"
        "&fields[tier]=title"
    )
    user_resp = requests.get(api_url, headers={"Authorization": f"Bearer {access_token}"}).json()
    print(f"🕵️ Patreon API Response: {user_resp}")

    included_data = user_resp.get('included', [])
    if not included_data:
        print("❌ No 'included' data found in API response. Denying access.")
        return send_file("/workspace/auth/fail.html"), 403

    # Create a simple lookup map of all tiers by their ID
    tiers_by_id = {item['id']: item['attributes'] for item in included_data if item['type'] == 'tier'}

    # Find all of the user's memberships in the included data
    memberships = [item for item in included_data if item['type'] == 'member']

    for membership in memberships:
        # Get the IDs of the tiers for this specific membership
        entitled_tiers_data = membership.get('relationships', {}).get('currently_entitled_tiers', {}).get('data', [])

        for tier_summary in entitled_tiers_data:
            tier_id = tier_summary['id']

            # Look up the full tier object in our map
            if tier_id in tiers_by_id:
                tier_title = tiers_by_id[tier_id].get('title', '')
                print(f"-> Comparing API name '{tier_title}' with required name '{REQUIRED_TIER}'")

                # --- NEW CODE ---
                if tier_title == REQUIRED_TIER:
                    print("✅ Power User tier found!")

                    # Check results of initial downloads before finalizing
                    flux_msg, flux_status = download_flux_workflow()
                    if flux_status != 200: return flux_msg, flux_status

                    scripts_msg, scripts_status = download_mega_scripts()
                    if scripts_status != 200: return scripts_msg, scripts_status

                    with open("/workspace/.flux_token", "w") as f:
                        f.write(datetime.now(timezone.utc).isoformat())
                    return redirect("/success")
                
    print("❌ Power User tier not found in user's memberships.")
    return send_file("/workspace/auth/fail.html"), 403

@app.route("/download/<version>")
def download_mega(version):
    script_map = {"all": "download_all_mega_files.py", "small": "download_small_mega_files.py"}
    if version not in script_map:
        return "Invalid version specified", 404

    script_name = script_map[version]
    script_path = os.path.join("/workspace/scripts", script_name)
    
    if not os.path.exists(script_path):
        return f"Script {script_name} not found.", 500

    # Clean up any old ".done" files before starting a new download
    done_file = f"/workspace/logs/download_{version}.done"
    if os.path.exists(done_file):
        os.remove(done_file)

    try:
        log_dir = "/workspace/logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"download_{version}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")
        with open(log_file_path, "w") as log_file:
            subprocess.Popen(["python3", script_path], stdout=log_file, stderr=subprocess.STDOUT)
    except Exception as e:
        print(f"🔥🔥🔥 CRITICAL ERROR trying to start subprocess for {script_name} 🔥🔥🔥")
        print(f"Exception: {e}")
        return "An unexpected error occurred while trying to start the download.", 500

    # Redirect to the new status-checking page
    return redirect(f"/downloading/{version}")

@app.route("/downloading/<version>")
def downloading_status(version):
    if version not in ["all", "small"]:
        return "Invalid version specified", 404
        
    done_file = f"/workspace/logs/download_{version}.done"
    
    if os.path.exists(done_file):
        # The .done file exists, so redirect to success with a "complete" message
        return redirect(f"/success?status={version}_complete")
    else:
        # The .done file is not there yet, show the waiting page
        return send_file("/workspace/auth/downloading.html")

# Add this entire new function to app.py
@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serves images from the /workspace/auth/images/ directory."""
    return send_from_directory('/workspace/auth/images', filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
