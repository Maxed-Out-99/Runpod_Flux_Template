import os
import json
import requests
from flask import Flask, redirect, request, send_file
import subprocess
from datetime import datetime, timedelta
import sys
sys.stdout.reconfigure(encoding='utf-8')


app = Flask(__name__)

def get_env_var(key, required=True, default=None):
    value = os.environ.get(key)
    if value is None:
        if required:
            raise RuntimeError(f"❌ Missing required environment variable: {key}")
        return default
    return value.strip()

# ✅ Use safe env var access
CLIENT_ID = get_env_var("PATREON_CLIENT_ID")
CLIENT_SECRET = get_env_var("PATREON_CLIENT_SECRET")
REDIRECT_URI = get_env_var("PATREON_REDIRECT_URI", required=False, default="http://localhost:7860/callback")

CAMPAIGN_ID = "13913714"  # You’ll get this in Step 3 below
REQUIRED_TIER = "⚡ Power User"  # The exact name of the tier

def download_flux_workflow():
    print("📦 Starting Power User workflow download...")

    hf_token = get_env_var("HF_TOKEN")
    if not hf_token:
        print("❌ Hugging Face token not found.")
        return "❌ HF_TOKEN not set.", 500

    url = "https://huggingface.co/MaxedOut/Power-User-Tools/resolve/main/workflows/Mega%20Flux%20v1.json"
    output_path = "/workspace/Mega Flux v1.json"

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
    return "✅ File downloaded"


@app.route("/success")
def success():
    return send_file("/workspace/auth/success.html")

# Step 1: Start auth
@app.route("/auth")
def auth():
    return redirect(f"https://www.patreon.com/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=identity%20identity.memberships")

# Step 2: Handle callback and check membership
@app.route("/callback")
def callback():

    code = request.args.get("code")
    if os.path.exists("/workspace/.flux_token"):
        with open("/workspace/.flux_token") as f:
            try:
                ts = datetime.fromisoformat(f.read().strip())
                if datetime.utcnow() - ts <= timedelta(hours=24):
                    print("✅ Already unlocked within last 24h")
                    return redirect("/success")
                else:
                    print("⌛ .flux_token expired")
                    os.remove("/workspace/.flux_token")
            except Exception as e:
                print("⚠️ Couldn't parse timestamp:", e)
                os.remove("/workspace/.flux_token")
    if not code:
        return "No code provided", 400

    # Exchange code for access token
    token_resp = requests.post("https://www.patreon.com/api/oauth2/token", data={
        "code": code,
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }).json()

    access_token = token_resp.get("access_token")
    if not access_token:
        return "Failed to get access token", 400

    # Get identity and memberships
    user_resp = requests.get(
        "https://www.patreon.com/api/oauth2/v2/identity?include=memberships&fields[member]=currently_entitled_tiers&fields[user]=full_name",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    memberships = user_resp.get("included", [])
    if not memberships:
        print("🧪 No memberships returned. Running in test mode.")
        with open("/workspace/.flux_token", "w") as f:
            f.write(datetime.utcnow().isoformat())
        download_flux_workflow()
        return "✅ Access granted (test mode — no membership)."

    for membership in memberships:
        if membership["type"] == "member":
            tiers = membership["relationships"].get("currently_entitled_tiers", {}).get("data", [])
            for tier in tiers:
                tier_id = tier["id"]

                # Lookup tier name
                tier_info = requests.get(
                    f"https://www.patreon.com/api/oauth2/v2/tiers/{tier_id}",
                    headers={"Authorization": f"Bearer {access_token}"}
                ).json()

                name = tier_info.get("data", {}).get("attributes", {}).get("title", "")
                print(f"🧪 Found tier: '{name}'")

                if name == REQUIRED_TIER:
                    with open("/workspace/.flux_token", "w") as f:
                        f.write(datetime.utcnow().isoformat())
                    result = download_flux_workflow()
                    print("🧪 download_flux_workflow() result:", result)

                    # If it's a tuple, return it as a Flask response (error)
                    if isinstance(result, tuple):
                        return result

                    return redirect("/success")


    return send_file("/workspace/auth/fail.html"), 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
