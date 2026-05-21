# WebView Checker - Quick Start Guide

## Overview

You now have three command-line tools for analyzing WebView usage in APK files:

1. **check_webview.py** - Basic WebView detection tool
2. **check_webview_advanced.py** - Advanced analysis with decompilation support
3. **example_workflow.py** - Integration example with Frida hooks

## Installation

No additional dependencies required for the basic tool. The tools use Python's standard library.

For advanced features (apktool support), install:
```bash
pip install apktool
```

## Quick Start

### 1. Basic WebView Check

```bash
python check_webview.py app.apk
```

Output:
```
Analyzing app.apk...
======================================================================
APK WebView Analysis Report
======================================================================
APK Path: app.apk

Component: WebView Usage
WebView Found: ✓ YES
JavaScript Enabled: ✓ YES (SECURITY RISK)
File Access: ✓ YES (SECURITY RISK)
...
```

### 2. Save Report to File

```bash
python check_webview.py app.apk -o report.txt
```

### 3. JSON Output

```bash
python check_webview.py app.apk --json
```

```json
{
  "apk_path": "app.apk",
  "findings": [
    {
      "activity": "WebView Usage",
      "webview_found": true,
      "javascript_enabled": true,
      ...
    }
  ]
}
```

### 4. Advanced Analysis

```bash
python check_webview_advanced.py app.apk -v
```

Features:
- Decompiled source code analysis
- DEX bytecode inspection
- Component extraction
- Detailed security assessment

### 5. Workflow with Frida Integration

```bash
python example_workflow.py app.apk
```

This will:
- Analyze WebView usage
- Print vulnerability summary
- Suggest Frida hooks
- Show Frida code examples

### 6. Generate Frida Hooks Script

```bash
python example_workflow.py app.apk --generate-hooks webview_hooks.js
```

Creates `webview_hooks.js` that can be used with Frida:

```bash
frida -U -f com.example.app -l webview_hooks.js
```

## Command Reference

### check_webview.py

```
Usage: python check_webview.py APK_FILE [OPTIONS]

Options:
  -h, --help           Show help message
  -v, --verbose        Enable verbose output
  -j, --json           Output in JSON format
  -o FILE, --output    Save report to file
```

### check_webview_advanced.py

```
Usage: python check_webview_advanced.py APK_FILE [OPTIONS]

Options:
  -h, --help           Show help message
  -v, --verbose        Enable verbose output
  -j, --json           Output in JSON format
  -o FILE, --output    Save report to file
  --apktool            Use apktool for decompilation
```

### example_workflow.py

```
Usage: python example_workflow.py APK_FILE [OPTIONS]

Options:
  -h, --help              Show help message
  -p PKG, --package       Package name
  -a, --advanced          Use advanced analysis
  -g FILE, --generate-hooks FILE    Generate Frida hooks
```

## Common Workflows

### 1. Security Assessment

```bash
# Analyze app
python check_webview.py myapp.apk -o assessment.txt

# Review report
cat assessment.txt
```

### 2. Frida Testing

```bash
# Generate hooks
python example_workflow.py myapp.apk --generate-hooks hooks.js

# Test with Frida
frida -U -f com.example.app -l hooks.js
```

### 3. CI/CD Integration

```bash
# Run check and fail if critical issues found
python check_webview.py app.apk --json > report.json

# Parse JSON and check for critical issues
python -c "
import json
with open('report.json') as f:
    report = json.load(f)
    issues = report['findings'][0]['details']
    critical = [i for i in issues if 'SECURITY RISK' in i]
    if critical:
        print(f'Critical issues found: {len(critical)}')
        exit(1)
"
```

### 4. Batch Analysis

```bash
# Analyze multiple APKs
for apk in *.apk; do
    echo "Analyzing $apk..."
    python check_webview.py "$apk" -o "${apk%.apk}_report.txt"
done
```

## What Each Tool Detects

### Basic Tool (check_webview.py)
- ✓ WebView class usage
- ✓ WebView configuration methods
- ✓ JavaScript/File access settings
- ✓ Custom client implementations
- ✗ Decompiled source code

### Advanced Tool (check_webview_advanced.py)
- ✓ Everything from basic tool
- ✓ Decompiled Java source code
- ✓ Detailed component analysis
- ✓ Security risk categorization
- ✓ Code location in source files

### Workflow Tool (example_workflow.py)
- ✓ Complete WebView analysis
- ✓ Vulnerability summary
- ✓ Frida hook suggestions
- ✓ Auto-generated Frida scripts
- ✓ Integration with Android testing

## Security Issues Detected

### High Priority (Critical)
- JavaScript enabled in WebView
- File access (file:// protocol) allowed
- JavaScript bridge exposed to web
- Dynamic code execution potential

### Medium Priority
- DOM storage enabled
- Database access enabled
- Mixed HTTP/HTTPS content allowed

### Low Priority
- Custom WebView client implementation
- Dynamic URL loading

## Security Recommendations

1. **Disable JavaScript** if not needed
   ```java
   webView.getSettings().setJavaScriptEnabled(false);
   ```

2. **Disable file access** to prevent data theft
   ```java
   webView.getSettings().setAllowFileAccess(false);
   ```

3. **Minimize JavaScript interfaces** - only expose necessary APIs
   ```java
   webView.addJavascriptInterface(new MyBridge(), "bridge");
   ```

4. **Use HTTPS only** for remote content loading

5. **Implement input validation** for all web content

6. **Use certificate pinning** for critical communications

7. **Keep WebView updated** - use latest Android security patches

## Troubleshooting

### "APK file not found"
```bash
# Use absolute path
python check_webview.py "/full/path/to/app.apk"
```

### "No WebView found" when expected
- App may use reflection to load WebView
- Try advanced mode: `python check_webview_advanced.py app.apk --apktool`
- Check with verbose logging: `python check_webview.py app.apk -v`

### "apktool not found" when using advanced mode
- Install: `pip install apktool`
- Or use without apktool (will use zipfile fallback)

### JSON parsing error
```bash
# Validate JSON output
python check_webview.py app.apk --json | python -m json.tool
```

## Integration with Your Frida Framework

The tools integrate seamlessly with your existing Frida automation:

```python
# In your Python script
from example_workflow import FridaWebViewWorkflow

workflow = FridaWebViewWorkflow("app.apk")
workflow.run_webview_check()
hooks = workflow.suggest_frida_hooks()
workflow.create_frida_script("custom_hooks.js")
```

Then use with Frida:
```bash
python Frida_script.py --hook-file custom_hooks.js
```

## Performance Notes

- **Basic tool**: Fast, completes in seconds
- **Advanced tool**: Slower due to decompilation, 10-30 seconds
- **Workflow tool**: Medium speed, includes analysis + suggestions

## Limitations

- Cannot detect obfuscated code patterns
- Pattern-based detection (not semantic analysis)
- Binary manifest parsing may miss some components
- Requires executable APK file (not corrupted)

## Support & Examples

See individual README files:
- `CHECK_WEBVIEW_README.md` - Basic tool documentation
- Source code comments in each Python file

## Next Steps

1. Analyze your target APK
2. Review the security findings
3. Generate Frida hooks if needed
4. Test with Frida on running app
5. Implement security fixes based on recommendations
