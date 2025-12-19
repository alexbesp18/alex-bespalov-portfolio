# 204: Serverless YouTube Alpha Scout
**Automated Alpha Extraction from Peter Diamandis**

This project creates a serverless "AI Scout" that monitors Peter Diamandis's YouTube channel. When a new video drops, it:
1.  **Extracts the Transcript** (using `youtube-transcript-api`).
2.  **Analyzes for Alpha** (using GPT-4o to find investment insights).
3.  **Emails You a Report** (HTML summary with timestamps).

It runs entirely on **GitHub Actions** (Free Tier), scheduled daily at 13:00 UTC.

---

## 🚀 Setup Instructions

### 1. Fork or Clone this Repo
Ensure you have the `204-serverless-youtube-alpha-scout` folder in your repository.

### 2. Configure Resend (Simplified)
The code is now pre-configured for your details:
- **Sender**: `onboarding@resend.dev`
- **Receiver**: `ab00477@icloud.com`

**You only need ONE thing:**
1.  Go to [Resend API Keys](https://resend.com/api-keys).
2.  Create a new key.
3.  Add it to GitHub Secrets as `EMAIL_PASSWORD`.

### 3. Add GitHub Secrets
Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add ONLY these two secrets:

| Secret Name | Value |
| :--- | :--- |
| `OPENROUTER_API_KEY` | Your [OpenRouter Key](https://openrouter.ai/keys) |
| `EMAIL_PASSWORD` | Your **Resend API Key** (starts with `re_`) |

*(Optional: If you verify a domain later, set `EMAIL_SENDER` to override default)*

### 4. Enable GitHub Actions
1.  Go to the **Actions** tab in your repo.
2.  Ensure workflows are allowed.
3.  You should see "Daily Alpha Scout".

### 5. Manual Test Run
1.  Go to **Actions** -> **Daily Alpha Scout**.
2.  Click **Run workflow**.
3.  Select the branch (usually `main`) and click **Run workflow**.
4.  Check the logs.

---

## 🛠️ Local Development

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Create `.env` file:**
    ```env
    OPENROUTER_API_KEY=your_key
    EMAIL_SENDER=onboarding@resend.dev
    EMAIL_PASSWORD=re_123456
    EMAIL_RECEIVER=your_email
    SMTP_SERVER=smtp.resend.com
    SMTP_PORT=465
    ```

3.  **Run:**
    ```bash
    python main.py
    ```

## 🧩 How It Works
- **`main.py`**: The brain. Parses RSS, fetches transcripts, prompts GPT-4o, sends email.
- **`.github/workflows/daily_alpha.yml`**: The heartbeat. Runs daily or on dispatch.
