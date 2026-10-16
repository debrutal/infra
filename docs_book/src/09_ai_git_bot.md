# AI-Git-Bot Integration in Gitea

This chapter covers the architecture, configuration, and operational workflows for **AI-Git-Bot** (`tmseidel/ai-git-bot`) integrated with **Gitea**, featuring dual LLM inference modes:

- **Mode 1 (Local Device)**: LLM inference on the Minisforum host itself via local Ollama (small model, e.g., `qwen2.5-coder:1.5b`).
- **Mode 2 (Remote Device)**: LLM inference on a remote Mac via Ollama/llama.cpp (larger model, e.g., `qwen2.5-coder:14b`) over LAN or NetBird VPN.

---

## 1. Architecture Overview

```
                      +-----------------------------+
                      |         Developer           |
                      +--------------+--------------+
                                     |
                                     | 1. Opens / Updates PR
                                     v
                      +-----------------------------+
                      |         Gitea Server        |
                      |  https://gitea.mini...      |
                      +--------------+--------------+
                                     |
                                     | 2. Webhook Event
                                     |    (pull_request, review_requested)
                                     v
                      +-----------------------------+
                      |          AI-Git-Bot         |
                      |  https://ai-git-bot.mini... |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               | [Mode 1: Active]                          | [Mode 2: Prepared]
               v                                           v
+-------------------------------+             +-------------------------------+
|    Minisforum Local Ollama    |             |      Remote Mac Ollama        |
|    http://ollama:11434        |             |    http://<mac-ip>:11434      |
|    Model: qwen2.5-coder:1.5b  |             |    Model: qwen2.5-coder:14b   |
+-------------------------------+             +-------------------------------+
               |                                           |
               +---------------------+---------------------+
                                     |
                                     | 3. Generated Code Review & Suggestions
                                     v
                      +-----------------------------+
                      |         Gitea Server        |
                      |  PR Inline Diff Comments &  |
                      |  Review Approvals / Notes   |
                      +-----------------------------+
```

---

## 2. Dual Inference Modes

### Mode 1: Device-Local Inference (Minisforum)
- **Engine**: Ollama running directly in the local Docker network (`http://ollama:11434`).
- **Model**: `qwen2.5-coder:1.5b` (lightweight, rapid inference on CPU with zero external network dependencies).
- **Keep-Alive**: Set to `24h` so the model stays memory-resident for instant review turnaround.
- **Privacy & Security**: 100% on-premises. Code diffs and prompts never leave the Minisforum server.

### Mode 2: Remote Device Inference (Mac - Prepared)
- **Engine**: Ollama running on a macOS workstation with Apple Silicon GPU acceleration.
- **Model**: `qwen2.5-coder:14b` (or `deepseek-coder-v2:16b` / `qwen2.5-coder:7b`) for deeper reasoning, complex architectural analysis, and higher-context PR reviews.
- **Connectivity**: Reached over local LAN (e.g., `http://192.168.1.10:11434`) or via NetBird mesh VPN.
- **How to switch**: In the AI-Git-Bot web dashboard, edit the Bot profile and switch its AI integration to `Mac Remote Ollama`, or maintain two separate review bots.

---

## 3. Step-by-Step Configuration Guide

### Step 3.1: Verify Deployment Services
Ensure both containers are active:
- **Ollama**: `https://ollama.mini.debrutal.dev` (or internal container `http://ollama:11434`)
- **AI-Git-Bot**: `https://ai-git-bot.mini.debrutal.dev`

### Step 3.2: Setting up AI Integrations in AI-Git-Bot
1. Open `https://ai-git-bot.mini.debrutal.dev` and log in.
2. Navigate to **AI Integrations → New Integration**:
   - **Mode 1 Integration**:
     - Name: `Minisforum Local Ollama`
     - Provider: `Ollama`
     - API URL: `http://ollama:11434`
     - Model: `qwen2.5-coder:1.5b`
     - Max Tokens: `4096`
   - **Mode 2 Integration (Remote Mac)**:
     - Name: `Mac Remote Ollama`
     - Provider: `Ollama`
     - API URL: `http://<YOUR_MAC_IP_OR_NETBIRD_IP>:11434`
     - Model: `qwen2.5-coder:14b`
     - Max Tokens: `8192`

### Step 3.3: Configuring Ollama on your Mac (for Mode 2)
On your Mac:
1. Ensure Ollama is installed:
   ```bash
   brew install ollama
   ```
2. Pull the larger review model:
   ```bash
   ollama pull qwen2.5-coder:14b
   ```
3. Expose Ollama to the local network or NetBird IP:
   ```bash
   OLLAMA_HOST=0.0.0.0:11434 ollama serve
   ```
   *(If using the Ollama macOS GUI app, set `launchctl setenv OLLAMA_HOST "0.0.0.0:11434"` and restart the app).*

### Step 3.4: Gitea Git Integration in AI-Git-Bot
1. In AI-Git-Bot, navigate to **Git Integrations → New Integration**:
   - Provider: `Gitea`
   - Name: `Local Gitea`
   - URL: `https://gitea.mini.debrutal.dev` (or `http://gitea:3000`)
   - API Token: Paste the access token generated for `ai_bot` (stored at `/opt/ai-git-bot/gitea_token.txt`).

### Step 3.5: Create the Review Bot
1. Navigate to **Bots → New Bot**:
   - Bot Name: `AI PR Reviewer`
   - Username: `ai_bot` (must match the Gitea bot account)
   - Git Integration: `Local Gitea`
   - AI Integration: Select `Minisforum Local Ollama` (Mode 1) or `Mac Remote Ollama` (Mode 2)
   - Enable PR Review triggers:
     - Review on PR open: Enabled
     - Review when reviewer requested: Enabled
2. Copy the generated **Webhook URL** (e.g. `https://ai-git-bot.mini.debrutal.dev/api/webhook/<token>`).

### Step 3.6: Configure the Webhook in Gitea
In Gitea:
1. Go to repository **Settings → Webhooks → Add Webhook → Gitea** (or Site Administration → Default Webhooks for all repositories).
2. Set:
   - **Target URL**: Paste the bot's Webhook URL
   - **HTTP Method**: `POST`
   - **POST Content Type**: `application/json`
   - **Secret**: Optional signing secret (matches bot settings if configured)
3. Select **Custom Events**:
   - Check **Pull Request**
   - Check **Pull Request Review Requested**
   - Check **Pull Request Comment**
   - Check **Issue Comment**
4. Click **Add Webhook**.

---

## 4. Review Workflow on Pull Requests

1. **Initial Review**: When a developer opens a Pull Request in Gitea, or explicitly requests `@ai_bot` as a reviewer:
   - Gitea triggers the webhook.
   - AI-Git-Bot retrieves the diff and sends it to the selected LLM (Mode 1 local or Mode 2 Mac).
   - AI-Git-Bot leaves detailed code feedback and inline comments on changed lines.
2. **Interactive Comments**: Developers can reply to any inline comment or general PR conversation:
   ```text
   @ai_bot can you suggest a cleaner refactor for this function?
   ```
   The bot detects the mention, analyzes the surrounding context, and responds in the thread.
3. **Re-Reviews**: When new commits are pushed, simply re-request `@ai_bot` in Gitea to initiate a fresh review pass.
