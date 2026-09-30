<div align="center">

# ⚡ Hammer SelfBot — All-in-One Discord Automation Suite

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Library-discord.py--self-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="discord.py-self" />
  <img src="https://img.shields.io/badge/Status-Maintained%20%26%20Patched-00FFEE?style=for-the-badge" alt="Status" />
  <img src="https://img.shields.io/badge/License-Educational%20Use%20Only-yellow?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <b>A feature-rich, high-performance, and modular Discord Self-Bot utility suite built on modern <code>discord.py-self</code>.</b>
</p>

---

</div>

## 📌 Disclaimer & Credits

> [!IMPORTANT]
> **Author & Attribution Notice:**
> - **Real Creator:** All original core architecture, logic, and feature concepts belong entirely to the **original real creator**.
> - **Maintenance & Bug Fixes:** Maintained, refactored, and patched by **wisep**. **wisep is NOT the original creator of this self-bot.**
> - **What wisep did:**
>   - Completely resolved dependency conflicts (cleaned incompatible packages like `wavelink`/standard `discord.py` overwriting `discord.py-self`).
>   - Upgraded broken and deprecated Discord API v6 endpoints to modern API v9/v10 across all checking & auth modules.
>   - Added browser TLS client headers & user-agent spoofing to avoid immediate rate-limits/captcha flags.
>   - Fixed token checker format parsing (`email:pass:token` multi-delimiter support).
>   - Fixed parameter bugs (`send(..., delete_after=...)`, image formatting, QR code byte handling).
>   - Cleaned redundant files, removed deprecated music subprocess hooks, and streamlined project architecture.

> [!WARNING]
> Self-bots violate Discord's **Terms of Service**. Using this software can result in account termination. This repository is strictly for educational, testing, and security research purposes. Use at your own risk.

---

## ✨ Features Overview

The self-bot contains **22+ loaded categories** accessible through modular cogs:

| Category | Icon | Description |
| :--- | :---: | :--- |
| **Setup & Config** | ⚙️ | Automatic server setup (`.setup`), custom prefixes, embed colors, webhook logger routing, and modes. |
| **Token & Checker** | 🔍 | Fast batch checking of Discord tokens (`.check`, `.tokens`, `.tcheck`), Nitro status, boost inventory, and phone verification (`.checkphone`). |
| **Server Boost Tools** | 🚀 | Automated token joiner and guild booster (`.boost`, `.aboost`, `.btool`) using browser TLS fingerprint simulation (`tls-client`). |
| **Alt Management** | 👥 | Multi-token utilities, token storage management (`alt_tokens_data/`), and server mass-joining. |
| **Crypto & Wallets** | 💰 | Live cryptocurrency rates (LTC, BTC, ETH, SOL, USDT, etc.), multi-wallet tracking (`.bal`, `.sendltc`, `.wallets`), Tatum API integration, and QR generation. |
| **Moderation** | 🛡️ | Comprehensive mod utilities: ban, kick, mute, purge, lock, unlock, role management, and slowmode. |
| **Anti-Nuke** | 🛑 | Guild backup & anti-nuke protection monitoring channel/role/member changes (`.anuke`). |
| **Server Cloner** | 📋 | Deep guild copier (`.copy`) cloning channels, categories, permissions, roles, and emojis directly to another server. |
| **Auto-Advertisement**| 📢 | Automated rotation of marketing ads and ticket messages across configured channels (`.autoad`). |
| **Activity & Status** | 🎮 | Automated rich presence cycler supporting Streaming, Playing, Listening, Watching, and Competing activities with customizable intervals. |
| **Group Chat Tools** | 💬 | Automated GC creation, mass-invite, recipient manipulation, and GC spam protection (`.gc`). |
| **Fun & Images** | 🎨 | Meme generation, avatar styling, image filters, and text ascii effects. |
| **Giveaways** | 🎉 | Autonomous giveaway host (`.gstart`) with timer parsing (`10m`, `2h`, `1d`), reaction listening, and winner drawing. |

---

## 📂 Project Directory Structure

```text
├── additional/
│   ├── extra.py             # User profile, AFK, reaction & status cycler commands
│   └── extra2.py            # TLS browser fingerprints (Chrome/Firefox) for joiners
├── alt_tokens_data/
│   ├── alt_tokens.txt       # Storage for alternate user tokens
│   └── invalid_tokens.txt   # Auto-routed invalid tokens
├── boost_tokens_data/
│   ├── 1m_tokens.txt        # 1-Month Nitro boost tokens
│   ├── 1m_used.txt          # Used 1-Month tokens
│   ├── 3m_tokens.txt        # 3-Month Nitro boost tokens
│   ├── 3m_used.txt          # Used 3-Month tokens
│   └── invalid_tokens.txt   # Invalidated boost tokens
├── database/
│   ├── ads.json             # Auto-ad configurations
│   ├── aliases.json         # Custom command aliases
│   ├── antinuke.json        # Anti-nuke security state
│   ├── automessages.json    # Periodic automated messages
│   ├── autoreactions.json   # Auto-react triggers
│   ├── autoroles.json       # Auto-role assignment rules
│   ├── greets.json          # Welcome/Greet messages
│   ├── triggers.json        # Custom auto-responses
│   ├── upi.json             # UPI payment QR data
│   ├── wallets.json         # Saved crypto addresses & keys
│   └── whitelist.json       # Whitelisted user IDs
├── bot_config.json          # OAuth2 Bot credentials for .aboost
├── config.json              # Main configuration file (token, webhooks, prefix)
├── main.py                  # Primary application entrypoint
├── nuker.json               # Wizz / Nuker parameters
└── requirements.txt         # Pinned Python package dependencies
```

---

## 🚀 Installation & Getting Started

### 1. Prerequisites
- **Python:** Python 3.10 to 3.14 installed. Ensure **Add Python to PATH** is checked during installation.
- **Git:** Git command line tool installed (needed for `discord.py-self` git dependency).

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/SelfBot.git
cd SelfBot
```

### 3. Install Dependencies
Run the following command to install the required libraries:
```bash
pip install -r requirements.txt
```

> [!NOTE]
> If you encounter dependency issues on Windows, upgrade pip first:
> ```powershell
> python -m pip install --upgrade pip setuptools wheel
> ```

---

## ⚙️ Configuration Guide

Before starting the bot, edit [`config.json`] with your credentials:

```json
{
    "selfbot_name": "Hammer",
    "token": "YOUR_DISCORD_USER_TOKEN",
    "tatum_api_key": "YOUR_TATUM_API_KEY",
    "time_zone": "Asia/Kolkata",
    "vouch_server": "discord.gg/yourlink",
    "ping_scan": false,
    "status_rotator_interval_in_seconds": 15,
    "mode": 2,
    "embed_colour": "#00ffee",
    "prefix": ".",
    "IP": "localhost",
    "PORT": 5000,
    "SECRET_PIN": "12345",
    "boosting_logs_webhook_url": "YOUR_WEBHOOK_URL",
    "ping_scan_webhook_url": "YOUR_WEBHOOK_URL",
    "embed_mode_webhook_url": "YOUR_WEBHOOK_URL",
    "wallets_webhook_url": "YOUR_WEBHOOK_URL",
    "oauth_boosting_logs_webhook_url": "YOUR_WEBHOOK_URL",
    "commands_logs_webhook_url": "YOUR_WEBHOOK_URL"
}
```

### Key Configuration Fields:
- **`token`**: Your personal Discord account user token.
- **`prefix`**: Command prefix (default is `.`).
- **`mode`**: Message delivery styling mode (e.g., plain, webhooks, or embed forwarding).
- **`embed_mode_webhook_url`**: Discord Webhook URL used to display stylized rich embeds from a self-bot account.
- **`tatum_api_key`**: API key from [Tatum.io](https://tatum.io/) required for generating wallets (`.genltc`) and sending crypto (`.sendltc`).
- **`bot_config.json`**: (Optional) Only required if using the OAuth `.aboost` command.

---

## 💳 Crypto Wallet Setup & Tatum API Guide (`database/wallets.json`)

The bot includes built-in automated Litecoin wallet generation and direct payment processing.

### 1. What is in `database/wallets.json`?
Each wallet entry in [`database/wallets.json`](file:///d:/my%20downloads/SelfBot/database/wallets.json) has the following format:
```json
{
    "1": {
        "id": 1,
        "wallet_name": "main",
        "mnemonic": "word1 word2 word3 ... word24",
        "xpub": "Ltub...",
        "address": "LTC_DEPOSIT_ADDRESS",
        "private_key": "YOUR_PRIVATE_KEY"
    }
}
```

- **`address`**: Used by `.addy <id>`, `.bal <id>`, and `.ltcqr <id>` to check balances and display your receiving address/QR code.
- **`private_key`**: Required by `.sendltc <id> <amount_usd> <to_address>` to sign and broadcast transactions to the Litecoin blockchain.
- **`xpub`** (Extended Public Key): Master public key used by hierarchical deterministic (HD) wallets to generate receiving addresses without revealing private keys.
- **`mnemonic`**: 12 or 24-word recovery seed phrase used to derive keys.

---

### 2. How to Get Your Tatum API Key
The bot uses **Tatum.io** as its blockchain gateway for creating wallets and broadcasting transactions:
1. Go to [https://tatum.io/](https://tatum.io/) and create a free account.
2. Navigate to your **Tatum Dashboard** -> **API Keys**.
3. Create a new API key (select **Mainnet** for real transactions or **Testnet** for testing).
4. Copy the API key and paste it into [`config.json`](file:///d:/my%20downloads/SelfBot/config.json):
   ```json
   "tatum_api_key": "YOUR_TATUM_API_KEY_HERE"
   ```

---

### 3. How to Obtain Wallet Credentials (`xpub`, `private_key`, `address`)

#### Option A: Let the Bot Generate It Automatically (Easiest & Recommended)
Once you have your `tatum_api_key` set in `config.json`:
1. In Discord, run:
   ```text
   .genltc <wallet_name>
   ```
   *(Example: `.genltc main`)*
2. The bot will automatically:
   - Call Tatum API to generate a fresh 24-word **mnemonic** and **xpub**.
   - Derive the initial receiving **address** (`index: 0`).
   - Derive the matching **private_key**.
   - Automatically save everything into [`database/wallets.json`](file:///d:/my%20downloads/SelfBot/database/wallets.json) with a new ID!

#### Option B: Export from Existing Wallets (Electrum-LTC, Trust Wallet, Exodus)
If you want to use an existing Litecoin wallet:
- **From Electrum-LTC (Desktop)**:
  - **Address**: Go to the **Receive** tab.
  - **xpub**: Go to **Wallet** -> **Information** -> Copy **Master Public Key** (`xpub` / `Ltub`).
  - **Private Key**: Go to **Wallet** -> **Private keys** -> **Export** -> Find the private key corresponding to your receiving address.
- **From Trust Wallet / Exodus / Coinomi**:
  - Export your **12/24-word recovery phrase (mnemonic)** or your **Private Key (WIF format)** from settings/security.
  - You can derive your master `xpub` and address keys using the offline [BIP39 Mnemonic Code Converter](https://iancoleman.io/bip39/) (Select coin: **LTC - Litecoin**).

> [!CAUTION]
> Never share your `private_key` or `mnemonic` with anyone! Anyone with access to these credentials has full control over your funds.

---

## 📖 First Run & Usage

1. **Launch the Self-Bot:**
   ```bash
   python main.py
   ```
2. **Server Setup:**
   - Create a private server for your self-bot controls.
   - Run the setup command in your server:
     ```text
     .setup
     ```
   - The bot will generate necessary channels (`ping-scan`, logs) and webhooks.
3. **Explore Commands:**
   - Type `.help` to view the interactive category menu.
   - Type `.help <module>` (e.g. `.help alts`, `.help crypto`, `.help btool`) to see specific commands.
   - Type `.allcmd` to see a full list of all available commands.

---

## 🛠️ Credits & Recognition

- **Original Creator**: Full credits for original code, design, and features belong to the **original author**.
- **Bug Fixes, Patches & Maintenance**: **wisep**
  - Continuous compatibility updates for newer Python versions (including 3.12–3.14).
  - Modernization of Discord API endpoints and security patching.
  - Architecture optimization and removal of broken third-party packages.

---

<div align="center">
  <sub>Maintained for educational purposes. Built with Python & discord.py-self.</sub>
</div>