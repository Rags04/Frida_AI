# WebView Checker - Integration Guide

Complete integration of WebView analysis tools with your existing Frida automation framework.

## Project Structure

```
FridaAutomation/
├── check_webview.py                 # Basic WebView detector
├── check_webview_advanced.py        # Advanced analysis tool
├── example_workflow.py              # Frida integration example
├── webview_check.ps1               # PowerShell wrapper (Windows)
├── webview_check.bat               # Batch wrapper (Windows)
│
├── WEBVIEW_QUICKSTART.md           # Quick start guide
├── CHECK_WEBVIEW_README.md         # Basic tool documentation
├── WEBVIEW_INTEGRATION.md          # This file
│
├── Frida_script.py                 # Existing Frida automation
├── AndroidConnect.py               # Existing ADB automation
├── adb.py                          # ADB utilities
│
└── Biometric_Bypass.js             # Existing Frida modules
├── Debugger_Detection_Bypass.js
├── SSL_Pinning_Bypass_(Universal).js
└── ... (other existing scripts)
```

## Using with PowerShell (Recommended for Windows)

### Basic Usage

```powershell
# Check webview in APK
.\webview_check.ps1 myapp.apk

# Advanced analysis
.\webview_check.ps1 myapp.apk -advanced

# JSON output
.\webview_check.ps1 myapp.apk -json

# Save to file
.\webview_check.ps1 myapp.apk -output report.txt
```

### Using in Your Frida Automation Workflow

```powershell
# 1. Analyze WebView
.\webview_check.ps1 app.apk -advanced -json | Tee-Object analysis.json

# 2. Review findings
$report = Get-Content analysis.json | ConvertFrom-Json
$report.findings | ForEach-Object { $_.details }

# 3. Generate Frida hooks
python example_workflow.py app.apk --generate-hooks webview_hooks.js

# 4. Use with existing Frida automation
python Frida_script.py --package com.example.app --script webview_hooks.js
```

## Integration with Existing Tools

### 1. With AndroidConnect.py

```python
# Enhanced AndroidConnect.py with WebView checking
import subprocess
import json

def check_webview_before_testing(apk_path, package_name):
    """Check WebView vulnerabilities before Frida testing"""
    
    # Run WebView analysis
    result = subprocess.run(
        ['python', 'check_webview.py', apk_path, '--json'],
        capture_output=True,
        text=True
    )
    
    analysis = json.loads(result.stdout)
    
    # Check for critical issues
    if analysis['findings'][0]['javascript_enabled']:
        print(f"[!] Critical: JavaScript enabled in WebView")
    
    if analysis['findings'][0]['file_access']:
        print(f"[!] Critical: File access allowed in WebView")
    
    return analysis
```

### 2. With Frida_script.py

Create a enhanced Frida script that combines WebView analysis with exploitation:

```python
# Add to your Frida_script.py
import subprocess
import json

class FridaAutomation:
    def analyze_webview_and_hook(self, apk_path, package):
        # First, analyze WebView
        workflow = FridaWebViewWorkflow(apk_path)
        workflow.run_webview_check()
        
        # Generate hooks based on findings
        workflow.create_frida_script("auto_hooks.js")
        
        # Load hooks with Frida
        self.load_frida_script("auto_hooks.js")
        self.run_app(package)
```

### 3. With Existing Bypass Scripts

Integrate WebView findings with your existing bypass scripts:

```javascript
// Add to your bypass scripts (e.g., Debugger_Detection_Bypass.js)

// WebView JavaScript Bridge Interception
Java.perform(function() {
    var WebView = Java.use("android.webkit.WebView");
    
    // Before applying debugger bypass, check WebView
    var webSettings = WebView.getSettings();
    if (webSettings != null) {
        var jsEnabled = webSettings.getJavaScriptEnabled();
        console.log("[*] WebView JavaScript enabled: " + jsEnabled);
        
        // Apply additional security bypasses if needed
        if (jsEnabled) {
            console.log("[!] Applying WebView bypasses...");
            apply_webview_bypasses();
        }
    }
});

function apply_webview_bypasses() {
    // Add WebView-specific bypass logic
}
```

## Complete Testing Workflow

### Scenario 1: Security Assessment

```powershell
# Step 1: Install app to device
python AndroidConnect.py --install app.apk

# Step 2: Analyze WebView
.\webview_check.ps1 app.apk -advanced -output webview_report.txt

# Step 3: Review security issues
Get-Content webview_report.txt

# Step 4: Generate testing hooks
python example_workflow.py app.apk --generate-hooks testing_hooks.js

# Step 5: Test with Frida
python Frida_script.py --package com.example.app --hook-file testing_hooks.js
```

### Scenario 2: Automated Testing Pipeline

```powershell
# Create batch analysis script
$apks = Get-ChildItem -Filter "*.apk"

foreach ($apk in $apks) {
    Write-Host "[*] Analyzing $($apk.Name)..."
    
    # Analysis
    .\webview_check.ps1 $apk.FullName -json -output "$($apk.BaseName)_report.json"
    
    # Extract findings
    $report = Get-Content "$($apk.BaseName)_report.json" | ConvertFrom-Json
    
    # Log critical issues
    if ($report.findings[0].webview_found) {
        Write-Host "[!] WebView found - creating hooks..."
        python example_workflow.py $apk.FullName --generate-hooks "$($apk.BaseName)_hooks.js"
    }
}
```

### Scenario 3: Continuous Integration

```powershell
# CI/CD Pipeline Script
$apk = $args[0]
$failures = 0

# Run WebView check
Write-Host "Running WebView analysis..."
python check_webview.py $apk --json | Tee-Object report.json

# Parse results
$report = Get-Content report.json | ConvertFrom-Json
$issues = $report.findings[0]

# Define failure criteria
if ($issues.javascript_enabled) { $failures++ }
if ($issues.file_access) { $failures++ }
if ($issues.javascript_interface) { $failures++ }

if ($failures -gt 0) {
    Write-Error "WebView security check failed: $failures critical issues"
    exit 1
}

Write-Host "WebView security check passed"
exit 0
```

## Advanced Integration Examples

### 1. Real-Time Monitoring

```python
#!/usr/bin/env python3
# Monitor WebView at runtime with Frida

import subprocess
import time
from pathlib import Path

def monitor_webview_runtime(package_name):
    """Monitor WebView activity in real-time"""
    
    script = """
    Java.perform(function() {
        var WebView = Java.use("android.webkit.WebView");
        var WebSettings = Java.use("android.webkit.WebSettings");
        
        // Log all WebView operations
        WebView.loadUrl.overload('java.lang.String').implementation = function(url) {
            console.log("[LOAD] URL: " + url);
            send({"type": "load_url", "url": url});
            return this.loadUrl(url);
        };
        
        WebSettings.setJavaScriptEnabled.overload('boolean').implementation = 
            function(enabled) {
            console.log("[JS] JavaScript: " + enabled);
            send({"type": "javascript", "enabled": enabled});
            return this.setJavaScriptEnabled(enabled);
        };
    });
    """
    
    # Save script
    with open('monitor.js', 'w') as f:
        f.write(script)
    
    # Run with Frida
    cmd = f'frida -U -f {package_name} -l monitor.js --no-pause'
    subprocess.run(cmd, shell=True)

# Usage
monitor_webview_runtime("com.example.app")
```

### 2. Automated Exploit Generation

```python
#!/usr/bin/env python3
# Auto-generate exploits based on WebView findings

from example_workflow import FridaWebViewWorkflow

def generate_exploit(apk_path):
    """Generate exploit script based on WebView vulnerabilities"""
    
    workflow = FridaWebViewWorkflow(apk_path)
    workflow.run_webview_check()
    
    vulns = workflow.check_webview_vulnerabilities()
    
    exploit = "// Auto-generated exploit\n"
    
    if vulns['javascript_interface']:
        exploit += """
// Exploit JavaScript Bridge
var bridge = Java.use("com.example.app.JavaScriptBridge");
// ... bridge exploitation code ...
"""
    
    if vulns['file_access']:
        exploit += """
// Exploit file:// access
// ... file access exploitation ...
"""
    
    with open('exploit.js', 'w') as f:
        f.write(exploit)
    
    return 'exploit.js'
```

## Command Reference

### All-in-One Analysis and Hook Generation

```powershell
# Complete workflow in one command
python example_workflow.py app.apk -a -g hooks.js ; python Frida_script.py --script hooks.js
```

### Batch Processing

```powershell
# Analyze all APKs and generate reports
Get-ChildItem *.apk | ForEach-Object {
    Write-Host "Analyzing $_"
    .\webview_check.ps1 $_ -advanced -output "$($_.BaseName)_report.txt"
}
```

### Extract Specific Findings

```powershell
# Get only critical issues
$report = python check_webview.py app.apk --json | ConvertFrom-Json
$report.findings[0].details | Where-Object { $_ -match "SECURITY RISK" }
```

## Troubleshooting Integration

### Issue: Scripts not found in PATH

**Solution:**
```powershell
# Use full path
python C:\Users\LENOVO\OneDrive\Desktop\FridaAutomation\check_webview.py app.apk
```

### Issue: Permission denied on PS1

**Solution:**
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\webview_check.ps1 app.apk
```

### Issue: Python not found

**Solution:**
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1
.\webview_check.ps1 app.apk
```

## Tips & Best Practices

1. **Always use `-advanced` flag for detailed analysis**
   ```powershell
   .\webview_check.ps1 app.apk -advanced
   ```

2. **Save reports for documentation**
   ```powershell
   .\webview_check.ps1 app.apk -output "reports\$(Get-Date -f 'yyyy-MM-dd_HHmmss').txt"
   ```

3. **Combine with version control**
   ```powershell
   .\webview_check.ps1 app.apk --json | Out-File "reports\v$version.json"
   ```

4. **Use JSON for parsing in scripts**
   ```powershell
   $analysis = python check_webview.py app.apk --json | ConvertFrom-Json
   if ($analysis.findings[0].webview_found) { ... }
   ```

5. **Document all findings**
   ```powershell
   .\webview_check.ps1 app.apk -verbose -output log.txt 2>&1
   ```

## Next Steps

- Review `WEBVIEW_QUICKSTART.md` for tool usage
- Check `CHECK_WEBVIEW_README.md` for detailed documentation
- Study `example_workflow.py` for integration patterns
- Adapt scripts to your testing methodology
- Integrate with your CI/CD pipeline

## Support

For issues or questions:
1. Check the individual tool README files
2. Review the source code comments
3. Test with the example workflow first
4. Verify APK file integrity

---

Created for Frida-based Android security testing
