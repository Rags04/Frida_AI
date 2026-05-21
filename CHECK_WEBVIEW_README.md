# APK WebView Checker - Usage Guide

A command-line tool to detect and analyze WebView usage in Android APK files with security risk assessment.

## Features

✓ **WebView Detection** - Identifies WebView components and usage patterns
✓ **Security Analysis** - Detects risky configurations like:
  - JavaScript execution enabled
  - File access permissions
  - DOM storage enabled
  - Database access enabled
  - Mixed content mode
  - JavaScript interfaces
✓ **Detailed Reports** - Text and JSON output formats
✓ **Verbose Logging** - Optional detailed output for debugging

## Installation

### Prerequisites
- Python 3.7+
- APK file to analyze

### Dependencies
The tool uses only Python standard library (no external dependencies needed):
- `zipfile` - for APK extraction
- `xml.etree.ElementTree` - for manifest parsing
- `argparse` - for CLI
- `json` - for JSON output

## Usage

### Basic Usage

```bash
python check_webview.py app.apk
```

### Command Options

```
positional arguments:
  apk                   Path to APK file

optional arguments:
  -h, --help            Show help message
  -v, --verbose         Enable verbose output
  -j, --json            Output in JSON format
  -o, --output FILE     Save report to file
```

### Examples

**Basic analysis:**
```bash
python check_webview.py myapp.apk
```

**Verbose output:**
```bash
python check_webview.py myapp.apk -v
```

**JSON output:**
```bash
python check_webview.py myapp.apk --json
```

**Save to file:**
```bash
python check_webview.py myapp.apk -o report.txt
```

**JSON report to file:**
```bash
python check_webview.py myapp.apk --json --output report.json
```

## Output Examples

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
  WebViewClient - found in 1 location(s)
    ℹ️  Custom android.webkit.WebViewClient implementation

======================================================================
Security Recommendations:
======================================================================
1. Disable JavaScript if not required: setJavaScriptEnabled(false)
2. Disable file access: setAllowFileAccess(false)
3. Be cautious with addJavascriptInterface() - potential XSS vector
4. Validate and sanitize all URLs loaded in WebView
5. Use HTTPS only for remote content
6. Implement proper certificate pinning
======================================================================
```

### JSON Report
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
      "mixed_content_mode": "DETECTED",
      "custom_client": true,
      "details": [
        "android/webkit/WebView - found in 2 location(s)",
        "setJavaScriptEnabled - found in 1 location(s)",
        "  ⚠️  JavaScript is enabled in WebView",
        ...
      ]
    }
  ]
}
```

## What It Detects

### WebView Components
- `android/webkit/WebView` - WebView class usage
- `WebViewClient` - Custom WebView client implementations
- `WebChromeClient` - Custom Chrome client implementations

### Security-Relevant Settings
- `setJavaScriptEnabled` - JavaScript execution capability
- `setAllowFileAccess` - File:// protocol access
- `addJavascriptInterface` - JavaScript-to-Java bridge
- `setDomStorageEnabled` - DOM storage capability
- `setDatabaseEnabled` - Database access
- `setMixedContentMode` - Mixed HTTP/HTTPS content handling

### JavaScript Operations
- `loadUrl` - URL loading
- `evaluateJavascript` - JavaScript evaluation

## Security Recommendations

### High Risk
1. **JavaScript Enabled** - Only enable if absolutely necessary
   ```java
   webView.getSettings().setJavaScriptEnabled(false); // Recommended
   ```

2. **File Access** - Disable unless required
   ```java
   webView.getSettings().setAllowFileAccess(false); // Recommended
   ```

3. **JavaScript Interface** - Never expose sensitive APIs
   ```java
   // Avoid or use with extreme caution
   webView.addJavascriptInterface(bridgeObject, "Bridge");
   ```

### Medium Risk
4. **DOM Storage** - Limit sensitive data storage
   ```java
   webView.getSettings().setDomStorageEnabled(false);
   ```

5. **Database** - Be cautious with data stored
   ```java
   webView.getSettings().setDatabaseEnabled(false);
   ```

### General Best Practices
6. **HTTPS Only** - Load content only from HTTPS sources
7. **Input Validation** - Sanitize all user input
8. **Certificate Pinning** - Implement public key pinning
9. **Content Security Policy** - Use CSP headers
10. **WebView Updates** - Keep WebView component updated

## Limitations

- Detects WebView usage by searching for known patterns in DEX bytecode
- Binary manifest parsing is pattern-based (not full XML parsing)
- Some obfuscated code may not be detected
- Custom WebView implementations may bypass detection
- Does not perform dynamic analysis

## Advanced Usage with Other Tools

### Combine with Frida
```bash
python check_webview.py app.apk --json > webview_analysis.json
# Use findings with Frida hooks to bypass security measures during testing
```

### Integration with CI/CD
```bash
python check_webview.py app.apk --json --output reports/webview_$(date +%s).json
```

## Troubleshooting

### "APK file not found"
- Verify the path to your APK file is correct
- Use absolute paths if having issues

### "AndroidManifest.xml not found"
- File may be corrupted or in unusual format
- Try unpacking with `unzip -l app.apk`

### No WebView found when you expect it
- Code may be obfuscated
- WebView may be loaded dynamically
- Use verbose mode (`-v`) to debug

## License

MIT License

## Notes

- This tool is for security testing and educational purposes
- Always obtain proper authorization before analyzing apps
- Results are based on static analysis; dynamic analysis may reveal additional findings
