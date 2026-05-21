# APK WebView Checker - Complete Toolkit

A comprehensive command-line toolkit for detecting, analyzing, and testing WebView vulnerabilities in Android APK files. Fully integrated with your Frida automation framework.

## 📦 What's Included

### Tools

| Tool | Purpose | Command |
|------|---------|---------|
| **check_webview.py** | Basic WebView detection | `python check_webview.py app.apk` |
| **check_webview_advanced.py** | Advanced analysis with decompilation | `python check_webview_advanced.py app.apk --apktool` |
| **example_workflow.py** | Frida integration and hook generation | `python example_workflow.py app.apk --generate-hooks` |

### Wrappers

| Wrapper | OS | Command |
|---------|----|---------| 
| **webview_check.ps1** | Windows PowerShell | `.\webview_check.ps1 app.apk` |
| **webview_check.bat** | Windows CMD | `webview_check.bat app.apk` |

### Documentation

| Document | Purpose |
|----------|---------|
| **WEBVIEW_QUICKSTART.md** | Quick start guide and examples |
| **CHECK_WEBVIEW_README.md** | Detailed documentation for basic tool |
| **WEBVIEW_INTEGRATION.md** | Integration with Frida and CI/CD |
| **README.md** | This file |

## 🚀 Quick Start

### Basic Analysis (30 seconds)

```powershell
# Using PowerShell wrapper (easiest)
.\webview_check.ps1 myapp.apk
```

Output:
```
[*] WebView analysis started...

======================================================================
APK WebView Analysis Report
======================================================================

Component: WebView Usage
WebView Found: ✓ YES
JavaScript Enabled: ✓ YES (SECURITY RISK)
File Access: ✓ YES (SECURITY RISK)

Security Recommendations:
1. Disable JavaScript if not required
2. Disable file access
...
```

### Advanced Analysis with Hooks

```powershell
# Generate Frida hooks
python example_workflow.py myapp.apk --generate-hooks hooks.js

# Use with Frida
frida -U -f com.example.app -l hooks.js
```

### Complete Testing Workflow

```powershell
# 1. Analyze WebView vulnerabilities
.\webview_check.ps1 app.apk -output analysis.txt

# 2. Review findings
Get-Content analysis.txt

# 3. Generate hooks for testing
python example_workflow.py app.apk --generate-hooks test_hooks.js

# 4. Deploy and test with Frida
python Frida_script.py --package com.example.app --script test_hooks.js
```

## 📋 Features

### Detection Capabilities

✅ **WebView Components**
- WebView class usage
- Custom WebView clients (WebViewClient, WebChromeClient)
- JavaScript bridge implementations

✅ **Security Settings**
- JavaScript enabled/disabled status
- File access permissions (file:// protocol)
- DOM storage configuration
- Database access settings
- Mixed content handling
- Mixed HTTP/HTTPS content

✅ **Advanced Analysis**
- Decompiled source code scanning
- DEX bytecode inspection
- Component extraction from manifest
- Security risk categorization
- Detailed location mapping

### Output Formats

- **Text Reports** - Human-readable analysis with recommendations
- **JSON Output** - Machine-parseable results for automation
- **File Export** - Save reports for documentation
- **Frida Scripts** - Auto-generated hook templates

## 🛠️ Command Cheat Sheet

```powershell
# Basic usage
.\webview_check.ps1 app.apk                    # Standard analysis
.\webview_check.ps1 app.apk -advanced          # Advanced analysis
.\webview_check.ps1 app.apk -verbose           # Detailed output
.\webview_check.ps1 app.apk -json              # JSON format

# Save outputs
.\webview_check.ps1 app.apk -output report.txt # Save text report
.\webview_check.ps1 app.apk -json -output r.json # Save JSON

# Frida integration
python example_workflow.py app.apk --generate-hooks hooks.js # Generate hooks
python example_workflow.py app.apk -a          # Advanced + suggestions

# Direct Python usage
python check_webview.py app.apk -v             # Verbose output
python check_webview_advanced.py app.apk --apktool # With apktool
```

## 🔍 What Gets Detected

### Critical Issues (High Risk)
🔴 **JavaScript Enabled**
- Potential for web-based attacks
- Exposure to XSS vulnerabilities

🔴 **File Access Enabled**
- Ability to read local files (file:// protocol)
- Risk of data theft from device

🔴 **JavaScript Bridge Exposed**
- Direct app function access from web content
- Potential for privilege escalation

### Medium Issues
🟠 **DOM Storage Enabled**
- Persistent data storage in web view
- May contain sensitive information

🟠 **Database Access**
- Direct database access from web content
- Information disclosure risk

🟠 **Mixed Content**
- HTTP/HTTPS content mixing
- Man-in-the-middle vulnerability

### Low Issues
🟡 **Custom Client Implementation**
- Custom WebViewClient or WebChromeClient
- May have security implications

🟡 **Dynamic URL Loading**
- Runtime URL loading detected
- Ensure proper validation

## 📊 Sample Output

### Text Report
```
======================================================================
APK WebView Analysis Report
======================================================================
APK Path: /path/to/app.apk

Component: WebView Usage
WebView Found: ✓ YES
JavaScript Enabled: ✓ YES (SECURITY RISK)
File Access: ✓ YES (SECURITY RISK)
DOM Storage: ✓ YES
Database Enabled: ✓ YES
Mixed Content Mode: DETECTED
Custom WebView Client: ✓ YES

Detailed Findings:
  android/webkit/WebView - found in 2 location(s)
  setJavaScriptEnabled - found in 1 location(s)
    ⚠️  JavaScript is enabled in WebView
  setAllowFileAccess - found in 1 location(s)
    ⚠️  File access is allowed in WebView
  
======================================================================
Security Recommendations:
======================================================================
1. Disable JavaScript if not required
2. Disable file access
3. Minimize JavaScript interfaces
...
```

### JSON Output
```json
{
  "apk_path": "/path/to/app.apk",
  "findings": [
    {
      "activity": "WebView Usage",
      "webview_found": true,
      "javascript_enabled": true,
      "file_access": true,
      "dom_storage": true,
      "database_enabled": true,
      "details": [
        "android/webkit/WebView - found in 2 location(s)",
        "setJavaScriptEnabled - found in 1 location(s)",
        ...
      ]
    }
  ]
}
```

### Frida Hooks (Auto-Generated)
```javascript
// Auto-generated Frida hooks for WebView analysis
console.log("[*] WebView Frida hooks loaded");

Java.perform(function() {
    var WebView = Java.use("android.webkit.WebView");
    var WebSettings = Java.use("android.webkit.WebSettings");
    
    WebSettings.setJavaScriptEnabled.overload('boolean').implementation = 
        function(enabled) {
        console.log("[*] setJavaScriptEnabled: " + enabled);
        return this.setJavaScriptEnabled(enabled);
    };
    
    // ... more hooks ...
});
```

## 🔐 Security Recommendations

### Disable JavaScript
```java
webView.getSettings().setJavaScriptEnabled(false);
```

### Disable File Access
```java
webView.getSettings().setAllowFileAccess(false);
webView.getSettings().setAllowContentAccess(false);
```

### Minimize Exposed Interfaces
```java
// Only expose necessary functions
webView.addJavascriptInterface(new SafeJavaScriptBridge(), "bridge");
```

### Use HTTPS Only
```java
webView.loadUrl("https://secure.example.com");
```

### Implement Input Validation
```java
String url = validateUrl(userInput);
webView.loadUrl(url);
```

### Enable Security Headers
```
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
```

## 📚 Documentation

### For Quick Start
→ See **WEBVIEW_QUICKSTART.md**

### For Basic Tool Details
→ See **CHECK_WEBVIEW_README.md**

### For Frida Integration
→ See **WEBVIEW_INTEGRATION.md**

### For Source Code Details
→ Check comments in Python files

## 🔧 Installation & Setup

### No Special Installation Required!

The basic tool uses only Python standard library:
```bash
python check_webview.py app.apk
```

### Optional: Advanced Features

For apktool support (better decompilation):
```bash
pip install apktool
python check_webview_advanced.py app.apk --apktool
```

### Activate Virtual Environment (First Time)

```powershell
.\venv\Scripts\Activate.ps1
```

## 💡 Use Cases

### Security Assessment
```powershell
# Assess security posture of an app
.\webview_check.ps1 app.apk -advanced -output "security_report_$(Get-Date -f 'yyyy-MM-dd').txt"
```

### Vulnerability Testing with Frida
```powershell
# Analyze then test vulnerabilities
python example_workflow.py app.apk --generate-hooks exploit.js
frida -U -f com.example.app -l exploit.js
```

### Compliance & Audit
```powershell
# Generate reports for security audit
Get-ChildItem *.apk | ForEach-Object {
    .\webview_check.ps1 $_ -output "$($_.BaseName)_audit.json" -json
}
```

### CI/CD Pipeline
```powershell
# Automated security checks
python check_webview.py app.apk --json | Tee-Object report.json
$report = ConvertFrom-Json (Get-Content report.json)
if ($report.findings[0].webview_found) { exit 1 }
```

## 🐛 Troubleshooting

### "Python not found"
```powershell
# Check Python installation
python --version

# Or use full path
C:\Python311\python.exe check_webview.py app.apk
```

### "Permission denied on .ps1 script"
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### "APK file not found"
```powershell
# Use absolute path
.\webview_check.ps1 "C:\Path\To\app.apk"
```

### "No WebView found" (but expected)
```powershell
# Try advanced mode with verbose
python check_webview_advanced.py app.apk -v --apktool
```

## 📈 Performance

| Tool | Speed | Features |
|------|-------|----------|
| check_webview.py | ⚡ Fast (~5s) | Basic detection, bytecode analysis |
| check_webview_advanced.py | 🐢 Slow (~20s) | Full decompilation, source analysis |
| example_workflow.py | ⏱️ Medium (~10s) | Analysis + Frida suggestions |

## 🔗 Integration with Your Tools

### With Frida_script.py
```python
# Add to your Frida automation
workflow = FridaWebViewWorkflow("app.apk")
workflow.run_webview_check()
hooks = workflow.suggest_frida_hooks()
```

### With AndroidConnect.py
```python
# Check WebView before testing
analysis = check_webview_before_testing("app.apk", "com.example.app")
if analysis['findings'][0]['javascript_enabled']:
    print("[!] JavaScript enabled - potential vulnerability")
```

### With Existing Bypass Scripts
- Use generated hooks with SSL_Pinning_Bypass.js
- Combine with Debugger_Detection_Bypass.js
- Layer with Biometric_Bypass.js

## 📄 File Manifest

```
check_webview.py               - Basic WebView detector (270 lines)
check_webview_advanced.py      - Advanced analyzer (450 lines)
example_workflow.py            - Frida integration (290 lines)
webview_check.ps1            - PowerShell wrapper
webview_check.bat            - Batch wrapper
README.md                     - This file
WEBVIEW_QUICKSTART.md         - Quick start guide
CHECK_WEBVIEW_README.md       - Basic tool docs
WEBVIEW_INTEGRATION.md        - Integration guide
```

## 📞 Support & Issues

1. **Tool not running?**
   - Check Python installation
   - Verify APK file exists
   - Try with absolute paths

2. **No findings detected?**
   - Use `-advanced` flag
   - Try with `-v` (verbose)
   - Check APK integrity

3. **Want more details?**
   - Read tool-specific documentation
   - Check source code comments
   - Review example_workflow.py

## 📝 License

For security testing and educational purposes. Follow responsible disclosure practices.

## 🎯 Next Steps

1. **Start here:** Review WEBVIEW_QUICKSTART.md
2. **Try basic tool:** `.\webview_check.ps1 app.apk`
3. **Explore advanced:** `python check_webview_advanced.py app.apk -v`
4. **Generate hooks:** `python example_workflow.py app.apk --generate-hooks`
5. **Test with Frida:** Use generated hooks with your Frida framework

---

**Created for Frida-based Android security testing framework**

Last Updated: 2026-05-11
