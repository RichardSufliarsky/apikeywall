## 🌉 What is APIKeyWall?

**APIKeyWall** is a security tool that acts as a protective gateway for your API keys. Think of it as a "firewall for API keys" that sits between your applications and external services.

**Why use it?** Instead of configuring real API keys in your applications (AI Agents, ...), you use placeholder keys. APIKeyWall automatically swaps these placeholders for real keys when requests pass through it. This keeps your sensitive keys safe and manageable in one place. It is a critical safety layer against prompt injection, buggy plugins, or misconfigurations that could exfiltrate your credentials.

---

## Works on: Linux, macOS, Windows

**Remember**: In Windows, replace `~/.mitmproxy/` with `%USERPROFILE%\.mitmproxy\`.

---

## 📦 Prerequisites

*   [**mitmproxy**](https://www.mitmproxy.org/): The core proxy engine.

---

## 🚀 Quick Start Guide

### 1. **Install the Required Software - mitmproxy**
Follow the official [mitmproxy installation guide](https://docs.mitmproxy.org/stable/overview-installation/) for your operating system.

### 2. Generate the mitmproxy Configuration Directory
Run mitmproxy once with any command (e.g., `mimdump --help`) to create its configuration directory:
- **Linux/macOS:** `~/.mitmproxy/`
- **Windows:** `%USERPROFILE%\.mitmproxy\`

### 3. Trust the mitmproxy CA Certificate
For this to work, you need to trust the mitmproxy Certificate Authority (CA).
- Run `mitmproxy --help` once. It will generate a CA certificate in its directory (Linux/macOS `~/.mitmproxy/`, Windows` %USERPROFILE%\.mitmproxy\`).
- **Install this CA certificate as trusted** on your system and in individual applications (like Firefox). Open [https://mitm.it/](https://mitm.it/) where you can download certificate and follow instructions.

<details>

<summary>Steps for Linux Debian/Ubuntu, Windows</summary>

**Linux Debian/Ubuntu:**

```bash
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.cer /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

**Windows:**

Open Windows Eplorer and insert this `%USERPROFILE%\.mitmproxy\` to the location bar, press enter and it will get you to the directory containing the certificate to import. Double click on `mitmproxy-ca-cert.cer`, click on `Install Certificate...`, in Store Location choose `Local Machine`, click `Next` and confirm [UAC](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/) popup (click `Yes`). Select `Place all certificates in the following store`, then click `Browse`, and select `Trusted Root Certification Authorities`. Click `OK` and `Next`. Click `Finish`. Click `Yes` to confirm the warning dialog.

</details>

For more details see the [mitmproxy docs on certificates](https://docs.mitmproxy.org/stable/concepts-certificates/).

### 4. **Get APIKeyWall**
Download the addon file:

- **Linux/macOS:**

```bash
cd ~/.mitmproxy/
wget https://raw.githubusercontent.com/RichardSufliarsky/apikeywall/main/apikeywall.py
```

- **Windows:**

```bash
cd %USERPROFILE%\.mitmproxy\
curl -o apikeywall.py https://raw.githubusercontent.com/RichardSufliarsky/apikeywall/main/apikeywall.py
```

### 5. **Create Your Configuration**
Create a file at `~/.mitmproxy/apikeywall.json` (this location is important) with content like this:
```json
[
    {
        "tokenin": "placeholder_key_for_openai",
        "tokenout": "sk-real-openai-key-abc123",
        "endpoints": ["api.openai.com"]
    },
    {
        "tokenin": "placeholder_for_anthropic", 
        "tokenout": "sk-ant-real-key-def456",
        "endpoints": ["api.anthropic.com"]
    }
]
```
Replace the `tokenout` values with your actual API keys.

**Remember**: 
  
Create the `apikeywall.json` file directly on a removable drive or in a temporary, encrypted location, then copy the entire file to `~/.mitmproxy/`, for security reasons, **it will be deleted** immediately after loading from there!  
**Your `apikeywall.json` contains real API keys. Keep it secure and never commit it unencrypted to version control!**

### 6. **Run APIKeyWall**
Linux (see [issue](https://github.com/mitmproxy/mitmproxy/issues/7787#issuecomment-3241257383))
```bash
mitmdump --flow-detail 0 --mode 'local:!tokio-runtime-w' -s ~/.mitmproxy/apikeywall.py
```
macOS
```bash
mitmdump --flow-detail 0 --mode local -s ~/.mitmproxy/apikeywall.py
```
Windows
```bash
mitmdump --flow-detail 0 --mode local -s %USERPROFILE%\.mitmproxy\apikeywall.py
```

#### Now use placeholders in your applications (AI Agents, ...) instead of real keys!

---

## 🛠️ How to Set Up Your Configuration

### **Configuration File Location**
The addon looks for configuration at: `~/.mitmproxy/apikeywall.json`

**Example Configuration:**
```json
[
    {
        "tokenin": "placeholder_key_for_openai",
        "tokenout": "sk-real-openai-key-abc123",
        "endpoints": ["api.openai.com"]
    },
    {
        "tokenin": "placeholder_for_anthropic", 
        "tokenout": "sk-ant-real-key-def456",
        "endpoints": ["api.anthropic.com"]
    }
]
```

### **What Each Field Means:**
- **`tokenin`**: The placeholder key you'll use in your application code
- **`tokenout`**: Your real, sensitive API key (keep this secret!)
- **`endpoints`**: Which websites/services this key should be used for

---

## 🔄 How It Works - Simple Explanation

Imagine you're sending a package (API request) to a specific company (endpoint). Instead of writing your real return address (API key) on the package, you write a code word (placeholder key). However, you have a rule: "Only replace this code word if the package is going to Company A or Company B."

**API Key Wall acts like a smart mailroom attendant who:**
1. **Checks the destination:** Looks at which company (endpoint) the package is addressed to
2. **Looks at your rules:** Checks if this company is on your "allowed companies" list for that code word
3. **Only then replaces the address:** If it's an allowed company, swaps the code word with your real address
4. **Otherwise leaves it alone:** If it's going to a different company, leaves the code word as-is
5. **Sends the package:** Forwards it to the destination company

**The key point:** Replacement happens ONLY when BOTH conditions are met:
1. ✅ The request uses a configured placeholder key
2. ✅ The destination matches one of the endpoints listed for that key

This ensures your API keys are revealed only to the services they're intended for!  
Your applications (AI Agents, ...) only know safe placeholders, so if there is a leak, the real API keys will not be exposed.

---

## 🔍 Checking If It's Working

When you run APIKeyWall (`mitmdump --flow-detail 0 -s ~/.mitmproxy/apikeywall.py`), look for these messages:
```
Loading addon: apikeywall.py
Set tcp_timeout to 7200 seconds
Updated allow_hosts with 2 endpoints
~/.mitmproxy/apikeywall.json: loaded 2 rules
```

If you see these, it's working correctly!

---

## 🤔 Common Questions

**Q: What happens if I need to change my API key?**  
**A:** Just update the `tokenout` value in your `apikeywall.json` file. No code changes needed!

**Q: Can I use multiple placeholder keys?**  
**A:** Yes! Add as many entries as you need to the JSON array.

**Q: What if the configuration file doesn't exist on start?**  
**A:** The addon will output error and stop.

**Q: Why does it delete the config file after reading?**  
**A:** For security - your real API keys are only in memory, not sitting on disk.

---

## ⚙️ For Technical Users / Developers

For detailed technical information about the addon's architecture, configuration options, and advanced usage, please see the [TECHNICAL.md](TECHNICAL.md) document.

---

## 🆘 Need Help?

1. **Make sure mitmproxy is installed**: `mitmdump --version`
2. **Check file location**: Configuration must be at `~/.mitmproxy/apikeywall.json`
3. **Verify JSON format**: Use a JSON validator if unsure
4. **Check logs**: Look for error messages in the mitmdump output

---

## ⚠️ Limitations

*   **Not Battle-Tested:** This is a new tool. Unexpected behavior may occur.
*   **Certificate Trust:** Some applications (notably **Firefox** and certain command-line tools) do not use the system's certificate store by default. You must manually import and trust the mitmproxy CA certificate within those applications.
*   **HTTPS-Only:** The script only inspects HTTP(S) traffic.
*   **Local Mode Requires Admin/Sudo:** On some systems, running in `--mode local` (transparent mode) may require administrator/root privileges (in Linux sudo password prompt, in Windows [UAC](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/) popup). Do not run it directly as root (administrator in Windows).
*   **Not tested on macOS:** Volunteers welcome, please report via issue.
*   **Runs in the console, not as a service:** Future improvement opportunity.

---

## 📄 License

MIT License. See the [LICENSE](LICENSE) file for full text.