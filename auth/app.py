import os
import json
import requests
from flask import Flask, redirect, request, send_file
import subprocess
from datetime import datetime, timedelta
import sys
sys.stdout.reconfigure(encoding='utf-8')


app = Flask(__name__)

# ⬇️ Replace these with your real values
CLIENT_ID = os.environ.get("PATREON_CLIENT_ID").strip()
CLIENT_SECRET = os.environ.get("PATREON_CLIENT_SECRET").strip()
REDIRECT_URI = os.environ.get("PATREON_REDIRECT_URI", "http://localhost:7860/callback")

CAMPAIGN_ID = "13913714"  # You’ll get this in Step 3 below
REQUIRED_TIER = "⚡ Power User"  # The exact name of the tier

def download_flux_workflow():

    hf_token = os.environ.get("HF_TOKEN").strip()
    if not hf_token:
        return "❌ Hugging Face token not found. Set HF_TOKEN in .env", 500

    url = "https://huggingface.co/MaxedOut/Power-User-Tools/resolve/main/workflows/Mega%20Flux%20v1.json"
    output_path = "/workspace/Mega Flux v1.json"

    command = [
        "curl", "-L",
        "-H", f"Authorization: Bearer {hf_token}",
        url,
        "-o", output_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Download failed:", result.stderr)
        return "❌ Failed to download Power User file.", 500

    print("✅ Power User file downloaded:", output_path)
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
                    download_flux_workflow()
                    return redirect("/success")

    return send_file("/workspace/auth/fail.html"), 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
