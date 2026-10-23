# 🤖 Sandeep's AI Job Hunter Agent

Automated job hunting and recommendation pipeline powered by Google Gemini and Telegram.

## 🎯 How It Works

1. **Daily Automated Scan**:
   - Triggers every day at **12:00 PM IST** (06:30 UTC) in the cloud via **GitHub Actions**.
   - Zero local server required; runs even if your laptop is powered off.

2. **Strict Two-Tier Search Strategy**:
   - **Tier 1 (Global Remote)**: Scrapes global boards (Jobicy, Remotive, RemoteOK) for Worldwide / Visa Relocation roles paying in USD/EUR. Disqualifies domestic US/UK remotes and all contract/freelance roles.
   - **Tier 2 (National Indian Remote/Hybrid)**: Automatically triggers if Tier 1 yields < 3 matches. Scrapes verified Indian remote/hybrid roles (Power BI, SQL, BigQuery, Analytics) while avoiding on-site roles in Delhi/NCR.

3. **Gemini Adaptive Scoring & Continuous Learning**:
   - Gemini evaluates each listing against Sandeep's profile and IndiaMART experience.
   - **Interactive Feedback Loop**: Each Telegram card includes `[✅ I Applied]` and `[❌ Skip / Not for me]` buttons.
   - User feedback (applied roles and skip reasons) is persisted in SQLite (`jobs.db`) and dynamically fed as few-shot memory into future Gemini prompts.

---

## 🔐 Required GitHub Secrets

To enable the daily GitHub Actions cloud runner, add these 3 secrets under **Repository Settings → Secrets and variables → Actions**:

- `GEMINI_API_KEY`: Your Google AI Studio API key.
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot token from @BotFather.
- `TELEGRAM_CHAT_ID`: Your Telegram numeric Chat ID.
