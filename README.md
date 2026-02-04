# APIKeyWall

A lightweight Python script for [mitmproxy](https://www.mitmproxy.org/) that acts as a firewall for your API keys. It securely replaces placeholder tokens with real API keys only when requests are sent to authorized endpoints, preventing accidental key leakage through AI agents, plugins, or misconfigured tools.

**⚠️ Important Security Disclaimer**
This script was published quickly to help the community contain the immediate risk of API key leaks from AI agents. It is a practical, incremental security measure. **It is not yet extensively battle-tested.** Use with caution and always monitor your API usage.

## 🛡️ How It Works

APIKeyWall runs as a script for mitmproxy on your local machine:
1.  You configure your AI tools (CLI agents, IDE plugins, etc.) to use a **placeholder API key**.
2.  mitmproxy intercepts all outgoing HTTPS traffic, and the APIKeyWall script processes it.
3.  If a request contains a configured placeholder (`tokenin`) and is destined for an allowed endpoint (e.g., `api.openai.com`), it **transparently swaps** the placeholder for the real key (`tokenout`).
4.  If the request goes to any other server, the real key is never exposed.

This provides a critical safety layer against prompt injection, buggy plugins, or misconfigurations that could exfiltrate your credentials.

## 📦 Prerequisites

*   [**mitmproxy**](https://www.mitmproxy.org/): The core proxy engine.

## ⚙️ Installation & Setup

### 1. Install mitmproxy
Follow the official [mitmproxy installation guide](https://docs.mitmproxy.org/stable/overview-installation/) for your operating system.

### 2. Generate the mitmproxy Configuration Directory
Run mitmproxy once with any command (e.g., `mitmproxy --help`) to create its configuration directory:
- **Linux/macOS:** `~/.mitmproxy/`
- **Windows:** `%USERPROFILE%\.mitmproxy\`

### 3. Install the APIKeyWall Script
Copy the `apikeywall.py` and `apikeywall.json` files into the mitmproxy directory created in the previous step.

**🔐 CRITICAL SECURITY STEP: Loading Your Real API Keys**

The `apikeywall.json` file is **loaded and immediately deleted** from disk by the script. This ensures your real API keys (`tokenout`) are never stored persistently.

**To load new keys safely:**
1.  **DO NOT** copy the JSON content via your system clipboard, as clipboard history may expose it.
2.  **Recommended Method:** Create the `apikeywall.json` file directly on a removable drive or in a temporary, encrypted location, then copy the entire file to `~/.mitmproxy/`. The script will consume and delete it on the next check.

**Configuration File Format (`apikeywall.json`):**
```json
[
    {
        "tokenin": "openai_placeholder_key",
        "tokenout": "sk-real-openai-key-abc123...",
        "endpoints": ["api.openai.com", "api.openai.us"]
    },
    {
        "tokenin": "anthropic_placeholder",
        "tokenout": "sk-ant-real-key-def456...",
        "endpoints": ["api.anthropic.com"]
    }
]
```

### 4. Trust the mitmproxy CA Certificate
For the script to intercept HTTPS traffic, you must trust mitmproxy's Certificate Authority (CA).
- Run `mitmproxy --help` once. It will generate a CA certificate in its directory (Linux/macOS ~/.mitmproxy/, Windows %USERPROFILE%\.mitmproxy).
- **Install this CA certificate as trusted** on your system and in individual applications (like Firefox). See the [mitmproxy docs on certificates](https://docs.mitmproxy.org/stable/concepts-certificates/).

Linux Debian/Ubuntu:
```bash
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.cer /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

Windows:

Open Windows Eplorer and insert this `%USERPROFILE%\.mitmproxy\` to the location bar, press enter and it will get you to the directory containing the certificate to import. Double click on `mitmproxy-ca-cert.cer`, click on `Install Certificate...`, in Store Location choose `Local Machine`, click `Next` and confirm [UAC](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/) popup (click `Yes`). Select `Place all certificates in the following store`, then click `Browse`, and select `Trusted Root Certification Authorities`. Click `OK` and `Next`. Click `Finish`. Click `Yes` to confirm the warning dialog.

## 🚀 Usage

Start mitmproxy in **local (transparent) mode** with the APIKeyWall script. This mode intercepts traffic automatically without configuring system proxy settings.

Linux (see [issue](https://github.com/mitmproxy/mitmproxy/issues/7787#issuecomment-3241257383))
```bash
mitmproxy --mode 'local:!tokio-runtime-w' -s ~/.mitmproxy/apikeywall.py
```
macOS
```bash
mitmproxy --mode local -s ~/.mitmproxy/apikeywall.py
```
Windows
```bash
mitmproxy --mode local -s %USERPROFILE%\.mitmproxy\apikeywall.py
```

Once running, configure your AI tools to use the **placeholder keys** (`tokenin`) defined in your config. Traffic will be intercepted, and keys will be swapped automatically for authorized endpoints.

## 🔧 Features

*   **Secure Secret Handling:** The configuration file with real keys is atomically loaded and deleted from disk immediately.
*   **Dynamic Reloading:** To update rules, place a **new** `apikeywall.json` file in the `~/.mitmproxy/` (`%USERPROFILE%\.mitmproxy` in Windows) directory. The script checks for the file's existence every 10 seconds during a request and will load the new configuration, deleting the file afterwards.
*   **Minimal Overhead:** Runs as a script within the mitmproxy process.
*   **Multi-Platform:** Works anywhere mitmproxy runs (Linux, macOS, Windows).

## ⚠️ Limitations & Troubleshooting

*   **Not Battle-Tested:** This is a new tool. Unexpected behavior may occur.
*   **Certificate Trust:** Some applications (notably **Firefox** and certain command-line tools) do not use the system's certificate store by default. You must manually import and trust the mitmproxy CA certificate within those applications.
*   **HTTPS-Only:** The script only inspects HTTP(S) traffic.
*   **Local Mode Requires Admin/Sudo:** On some systems, running in `--mode local` (transparent mode) may require administrator/root privileges (in Linux sudo password prompt, in Windows [UAC](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/) popup). Do not run it directly as root (administrator in Windows).
*   **Not tested on macOS:** Volunteers welcome, please report via issue.
*   **Runs in the console, not as a service:** Future improvement opportunity.

### Discovering API Endpoints (Optional)
For a comprehensive list of AI API endpoints, you can consult community resources like the [`models.dev` API database](https://models.dev/api.json).

## 🧠 Advanced Configuration

### Running as a Transparent Bridge (Advanced) ###
For the highest security, you can run APIKeyWall on a dedicated gateway machine or virtual machine configured as a transparent bridge. This isolates the proxy from your workstation. Please refer to the mitmproxy [transparent mode](https://docs.mitmproxy.org/stable/concepts/modes/#transparent-proxy) documentation if you wish to explore this setup.

## 📄 License

MIT License. See the [LICENSE](LICENSE) file for full text.
