import os
import json
import requests
from flask import Flask, redirect, request, send_file
import subprocess
from datetime import datetime, timedelta
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

@app.errorhandler(404)
def not_found(e):
    return redirect("/")

@app.route("/success")
def success():
    print("✅ Success page reached.")
    return send_file("/workspace/auth/success.html")

@app.route("/")
def index():
    return """
    <html>
        <head>
            <meta http-equiv="refresh" content="7; url=/auth" />
        </head>
        <body style="font-family:sans-serif;text-align:center;padding-top:60px">
            <h1>⚡ Unlocking Mega Flux...</h1>
            <p>Warming up the service. You’ll be redirected shortly.</p>
        </body>
    </html>
    """

# Step 1: Start auth - THIS IS THE MAIN CHANGE
@app.route("/auth")
def auth():
    # Dynamically determine this pod's unique callback URL
    # request.host will be like '<pod-id>-7860.proxy.runpod.net'
    pod_specific_callback = f"https://{request.host}/callback"

    # The redirect_uri sent to Patreon is now your STATIC helper page.
    # The pod's UNIQUE URL is passed in the 'state' parameter.
    auth_url = (
        f"https://www.patreon.com/oauth2/authorize?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={PATREON_HELPER_CALLBACK}"
        f"&scope=identity%20identity.memberships"
        f"&state={pod_specific_callback}" # <-- Pass unique URL in state
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

    # Exchange code for access token using the static helper URL
    token_resp = requests.post("https://www.patreon.com/api/oauth2/token", data={
        "code": code,
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": PATREON_HELPER_CALLBACK # <-- This is the only change you needed
    }).json()

    access_token = token_resp.get("access_token")
    if not access_token:
        print("❌ Failed to get access token. Patreon response:", token_resp)
        return "Failed to get access token", 400

    # Get identity and memberships (This part remains the same)
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

                    if isinstance(result, tuple):
                        return result

                    return redirect("/success")


    return send_file("/workspace/auth/fail.html"), 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
