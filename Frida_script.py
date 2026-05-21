"""Collection of common Frida bypass scripts for Android security testing.
For legitimate penetration testing and security research only.
"""

BYPASS_SCRIPTS: dict[str, dict] = {
    "SSL Pinning Bypass (Universal)": {
        "description": "Bypasses SSL/TLS certificate pinning using multiple hook strategies (OkHttp, TrustManager, etc.)",
        "script": r"""
/* Universal SSL Pinning Bypass */
setTimeout(function () {
    Java.perform(function () {

        /* TrustManager - trust all certs */
        var TrustManager = Java.registerClass({
            name: 'com.custom.TrustManager',
            implements: [Java.use('javax.net.ssl.X509TrustManager')],
            methods: {
                checkClientTrusted: function (chain, authType) {},
                checkServerTrusted: function (chain, authType) {},
                getAcceptedIssuers: function () { return []; }
            }
        });

        var SSLContext = Java.use('javax.net.ssl.SSLContext');
        SSLContext.init.overload('[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom').implementation = function (km, tm, sr) {
            this.init(km, [TrustManager.$new()], sr);
        };

        /* OkHttp3 CertificatePinner */
        try {
            var CertificatePinner = Java.use('okhttp3.CertificatePinner');
            CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function (str, list) {
                console.log('[+] OkHttp3 CertificatePinner.check bypassed');
            };
            CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function (str, cert) {
                console.log('[+] OkHttp3 CertificatePinner.check (cert) bypassed');
            };
        } catch (e) { console.log('[-] OkHttp3 not present'); }

        /* Hostname verifier */
        var HostnameVerifier = Java.registerClass({
            name: 'com.custom.HostnameVerifier',
            implements: [Java.use('javax.net.ssl.HostnameVerifier')],
            methods: { verify: function (hostname, session) { return true; } }
        });
        var HttpsURLConnection = Java.use('javax.net.ssl.HttpsURLConnection');
        HttpsURLConnection.setDefaultHostnameVerifier(HostnameVerifier.$new());

        console.log('[+] SSL Pinning Bypass active');
    });
}, 0);
"""
    },

    "Root Detection Bypass": {
        "description": "Bypasses common root detection libraries: RootBeer, RootTools, and file-based checks.",
        "script": r"""
/* Root Detection Bypass */
setTimeout(function () {
    Java.perform(function () {

        /* RootBeer */
        try {
            var RootBeer = Java.use('com.scottyab.rootbeer.RootBeer');
            RootBeer.isRooted.implementation = function () { return false; };
            RootBeer.isRootedWithoutBusyBoxCheck.implementation = function () { return false; };
            console.log('[+] RootBeer bypassed');
        } catch (e) { console.log('[-] RootBeer not found'); }

        /* Generic isRooted / isDeviceRooted patterns */
        Java.enumerateLoadedClasses({
            onMatch: function (cls) {
                try {
                    var klass = Java.use(cls);
                    ['isRooted', 'isRootedDevice', 'isDeviceRooted', 'checkRoot', 'detectRoot'].forEach(function (m) {
                        try {
                            klass[m].overload().implementation = function () {
                                console.log('[+] Hooked ' + cls + '.' + m);
                                return false;
                            };
                        } catch (_) {}
                    });
                } catch (_) {}
            },
            onComplete: function () {}
        });

        /* File.exists for su / superuser */
        var File = Java.use('java.io.File');
        File.exists.implementation = function () {
            var path = this.getAbsolutePath();
            var suspects = ['/su', '/system/xbin/su', '/system/bin/su', '/sbin/su', 'Superuser.apk', 'supersu', '.magisk', 'busybox'];
            for (var i = 0; i < suspects.length; i++) {
                if (path.toLowerCase().indexOf(suspects[i].toLowerCase()) !== -1) {
                    console.log('[+] Faking missing: ' + path);
                    return false;
                }
            }
            return this.exists();
        };

        console.log('[+] Root Detection Bypass active');
    });
}, 0);
"""
    },

    "Emulator Detection Bypass": {
        "description": "Spoofs device properties (Build, TelephonyManager) to bypass emulator/VM detection.",
        "script": r"""
/* Emulator Detection Bypass */
setTimeout(function () {
    Java.perform(function () {
        var Build = Java.use('android.os.Build');
        Build.FINGERPRINT.value = 'google/walleye/walleye:9/PQ3A.190801.002/5670554:user/release-keys';
        Build.MODEL.value       = 'Pixel 2';
        Build.MANUFACTURER.value = 'Google';
        Build.BRAND.value       = 'google';
        Build.DEVICE.value      = 'walleye';
        Build.PRODUCT.value     = 'walleye';
        Build.HARDWARE.value    = 'walleye';
        Build.TAGS.value        = 'release-keys';

        /* TelephonyManager */
        try {
            var TM = Java.use('android.telephony.TelephonyManager');
            TM.getDeviceId.overload().implementation          = function () { return '352000000000000'; };
            TM.getNetworkOperatorName.implementation         = function () { return 'T-Mobile'; };
            TM.getSimOperatorName.implementation            = function () { return 'T-Mobile'; };
            TM.getPhoneType.implementation                  = function () { return 1; };
            TM.getNetworkType.implementation                = function () { return 13; };
        } catch (e) {}

        console.log('[+] Emulator Detection Bypass active');
    });
}, 0);
"""
    },

    "Biometric Bypass": {
        "description": "Bypasses fingerprint/biometric authentication by forcing the onAuthenticationSucceeded callback.",
        "script": r"""
/* Biometric Bypass */
setTimeout(function () {
    Java.perform(function () {

        /* BiometricPrompt (API 28+) */
        try {
            var BiometricPrompt = Java.use('android.hardware.biometrics.BiometricPrompt');
            BiometricPrompt.authenticate.overload(
                'android.os.CancellationSignal',
                'java.util.concurrent.Executor',
                'android.hardware.biometrics.BiometricPrompt$AuthenticationCallback'
            ).implementation = function (cancel, executor, callback) {
                console.log('[+] BiometricPrompt.authenticate hooked - triggering success');
                var result = Java.use('android.hardware.biometrics.BiometricPrompt$AuthenticationResult').$new(null);
                callback.onAuthenticationSucceeded(result);
            };
        } catch (e) { console.log('[-] BiometricPrompt not found'); }

        /* FingerprintManager (legacy) */
        try {
            var FPM = Java.use('android.hardware.fingerprint.FingerprintManager');
            FPM.authenticate.overload(
                'android.hardware.fingerprint.FingerprintManager$CryptoObject',
                'android.os.CancellationSignal',
                'int',
                'android.hardware.fingerprint.FingerprintManager$AuthenticationCallback',
                'android.os.Handler'
            ).implementation = function (crypto, cancel, flags, callback, handler) {
                console.log('[+] FingerprintManager.authenticate hooked - triggering success');
                var res = Java.use('android.hardware.fingerprint.FingerprintManager$AuthenticationResult').$new(crypto);
                callback.onAuthenticationSucceeded(res);
            };
        } catch (e) { console.log('[-] FingerprintManager not found'); }

        console.log('[+] Biometric Bypass active');
    });
}, 0);
"""
    },

    "Signature / Anti-Tamper Bypass": {
        "description": "Bypasses APK signature and package integrity checks by spoofing PackageManager signature results.",
        "script": r"""
/* Signature / Anti-Tamper Bypass */
setTimeout(function () {
    Java.perform(function () {
        var PackageManager = Java.use('android.app.ApplicationPackageManager');

        PackageManager.getPackageInfo.overload('java.lang.String', 'int').implementation = function (pkg, flags) {
            var info = this.getPackageInfo(pkg, flags);
            if ((flags & 0x00000040) !== 0) { /* GET_SIGNATURES */
                console.log('[+] Spoofing signatures for: ' + pkg);
                /* Return original info - hooks downstream comparisons instead */
            }
            return info;
        };

        /* Spoof Signature.toByteArray / hashCode for comparison hooks */
        var Signature = Java.use('android.content.pm.Signature');
        Signature.hashCode.implementation = function () {
            console.log('[+] Signature.hashCode spoofed');
            return 0;
        };

        console.log('[+] Signature/Anti-Tamper Bypass active');
    });
}, 0);
"""
    },

    "Debugger Detection Bypass": {
        "description": "Bypasses anti-debugging checks: Debug.isDebuggerConnected, ApplicationInfo flags, and TimingAttack guards.",
        "script": r"""
/* Debugger Detection Bypass */
setTimeout(function () {
    Java.perform(function () {

        /* android.os.Debug */
        var Debug = Java.use('android.os.Debug');
        Debug.isDebuggerConnected.implementation = function () { return false; };
        Debug.waitingForDebugger.implementation = function () { return false; };

        /* ApplicationInfo.FLAG_DEBUGGABLE */
        var ApplicationInfo = Java.use('android.content.pm.ApplicationInfo');
        ApplicationInfo.flags.value = ApplicationInfo.flags.value & ~(1 << 1);

        /* System.exit - prevent kill on detection */
        var System = Java.use('java.lang.System');
        System.exit.implementation = function (code) {
            console.log('[+] System.exit(' + code + ') blocked');
        };

        /* Timing attack guard - Thread.sleep */
        var Thread = Java.use('java.lang.Thread');
        Thread.sleep.overload('long').implementation = function (ms) {
            if (ms > 500) {
                console.log('[+] Long sleep (' + ms + 'ms) skipped (timing guard)');
                return;
            }
            this.sleep(ms);
        };

        console.log('[+] Debugger Detection Bypass active');
    });
}, 0);
"""
    },

    "SafetyNet / Play Integrity Bypass": {
        "description": "Hooks SafetyNet Attestation API and Play Integrity API to return a passing result.",
        "script": r"""
/* SafetyNet / Play Integrity Bypass */
setTimeout(function () {
    Java.perform(function () {

        /* SafetyNet API */
        try {
            var SafetyNetClient = Java.use('com.google.android.gms.safetynet.SafetyNetClient');
            SafetyNetClient.attest.implementation = function (nonce, apiKey) {
                console.log('[+] SafetyNet.attest called - hooking response');
                return this.attest(nonce, apiKey);
            };
        } catch (e) { console.log('[-] SafetyNetClient not found'); }

        /* AttestationResult */
        try {
            var AttestationResult = Java.use('com.google.android.gms.safetynet.SafetyNetApi$AttestationResponse');
            AttestationResult.getJwsResult.implementation = function () {
                /* Return a placeholder - replace with a valid JWS for full bypass */
                console.log('[+] SafetyNet JWS result intercepted');
                return this.getJwsResult();
            };
        } catch (e) {}

        console.log('[+] SafetyNet/Play Integrity Bypass active (partial - valid JWS needed for full bypass)');
    });
}, 0);
"""
    },

    "Android DeepLink Observer": {
        "description": "Observes and logs deep link/URL scheme data when Android apps receive intents. Hooks Intent.getData() to intercept and display URI components.",
        "script": r"""
/*
    Description: Android DeepLink Observer
    Usage: frida -U -f XXX -l android-deeplink-observer.js
    Credit: leolashkevych

    Link:
    https://developer.android.com/reference/android/content/Intent#getData()
*/

Java.perform(function()
{
    var Intent = Java.use("android.content.Intent");


Intent.getData.implementation = function()
    {
        var action = this.getAction() !== null ? this.getAction().toString() : false;

        if (action)
        {
            console.log("[*] Intent.getData() was called");
            console.log("[*] Activity: " + this.getComponent().getClassName());
            console.log("[*] Action: " + action);

            var uri = this.getData();

            if (uri !== null)
            {
                console.log("\n[*] Data");
                uri.getScheme() && console.log("- Scheme:\t" + uri.getScheme() + "://");
                uri.getHost() && console.log("- Host:\t\t" + uri.getHost());
                uri.getPath() && console.log("- Path:\t\t" + uri.getPath());
                uri.getQuery() && console.log("- Params:\t" + uri.getQuery());
                uri.getFragment() && console.log("- Fragment:\t" + uri.getFragment());
                console.log("\n\n");
            }
            else
            {
                console.log("[-] No data supplied.");
            }
        }

        return this.getData();
    }
});
"""
    },

    "Firebase DataSnapshot Logger": {
        "description": "Logs Firebase Realtime Database use of DatabaseReference.get(), child(), and ValueEventListener.onDataChange().",
        "script": r"""
Java.perform(function() {
    console.log("[*] Starting Firebase hooks...");

    // Hooking into Firebase Database Reference get() method
    var DatabaseReference = Java.use("com.google.firebase.database.DatabaseReference");
    DatabaseReference.get.overload().implementation = function() {
        console.log("[*] Firebase DatabaseReference.get() called!");
        var result = this.get();
        console.log("[*] Data fetched: " + result);
        return result;
    };

    // Hooking the addValueEventListener to capture data as it is received
    var ValueEventListener = Java.use("com.google.firebase.database.ValueEventListener");
    ValueEventListener.onDataChange.implementation = function(dataSnapshot) {
        console.log("[*] ValueEventListener.onDataChange triggered!");

        // Log snapshot details (key and value)
        var key = dataSnapshot.getKey();
        var value = dataSnapshot.getValue();
        console.log("[*] Key: " + key);
        console.log("[*] Value: " + JSON.stringify(value));

        this.onDataChange(dataSnapshot);
    };

    // Hooking the child() method to trace what parts of the database the app is querying
    DatabaseReference.child.implementation = function(pathString) {
        console.log("[*] DatabaseReference.child() accessed. Path: " + pathString);
        return this.child(pathString);
    };
});
"""
    },

    "Screenshot Protection Bypass": {
        "description": "Bypasses screenshot protection (FLAG_SECURE) by hooking SurfaceView.setSecure() and Window.setFlags(). Allows capturing screenshots of protected apps.",
        "script": r"""
/* Screenshot Protection Bypass */
Java.perform(function() {
    var surface_view = Java.use('android.view.SurfaceView');
    var set_secure = surface_view.setSecure.overload('boolean');
    
    set_secure.implementation = function(flag){
        console.log("[*] SurfaceView.setSecure() called with: " + flag);
        set_secure.call(this, false);
    };

    var window = Java.use('android.view.Window');
    var set_flags = window.setFlags.overload('int', 'int');
    var window_manager = Java.use('android.view.WindowManager');
    var layout_params = Java.use('android.view.WindowManager$LayoutParams');

    set_flags.implementation = function(flags, mask){
        console.log("[*] Window.setFlags() called - flags: " + flags);
        console.log("[*] FLAG_SECURE value: " + layout_params.FLAG_SECURE.value);
        
        // Remove FLAG_SECURE from flags
        flags = (flags & ~layout_params.FLAG_SECURE.value);
        
        console.log("[*] Removed FLAG_SECURE - new flags: " + flags);
        set_flags.call(this, flags, mask);
    };

    console.log('[+] Screenshot Protection Bypass active');
});
"""
    },

    "External Storage APIs Tracing with Frida": {
        "description": "Monitors external storage access and ContentResolver.insert calls for Android storage data protection testing.",
        "script": r"""
function printBacktrace(maxLines = 8) {
    Java.perform(() => {
        let Exception = Java.use("java.lang.Exception");
        let stackTrace = Exception.$new().getStackTrace().toString().split(",");
        console.log("\nBacktrace:");
        for (let i = 0; i < Math.min(maxLines, stackTrace.length); i++) {
            console.log(stackTrace[i]);
        }
    });
};

// Intercept libc's open to make sure we cover all Java I/O APIs
Interceptor.attach(
    Process.getModuleByName('libc.so').getExportByName('open'),
    {
        onEnter: function(args) {
            const external_paths = ['/sdcard', '/storage/emulated'];
            const path = args[0].readCString();
            external_paths.forEach(external_path => {
                if (path.indexOf(external_path) === 0) {
                    console.log(`\n[*] open called to open a file from external storage at: ${path}`);
                    printBacktrace(15);
                }
            });
        }
    }
);

// Hook ContentResolver.insert to log ContentValues (including keys like _display_name, mime_type, and relative_path) and returned URI
Java.perform(() => {
    let ContentResolver = Java.use("android.content.ContentResolver");
    ContentResolver.insert.overload('android.net.Uri', 'android.content.ContentValues').implementation = function(uri, values) {
        console.log(`\n[*] ContentResolver.insert called with ContentValues:`);

        console.log(`\t_display_name: ${values.get("_display_name").toString()}`);
        console.log(`\tmime_type: ${values.get("mime_type").toString()}`);
        console.log(`\trelative_path: ${values.get("relative_path").toString()}`);

        let result = this.insert(uri, values);
        console.log(`\n[*] ContentResolver.insert returned URI: ${result.toString()}`);
        printBacktrace();
        return result;
    };
});
"""
    },

    "Hardcoded Credential Scanner": {
        "description": "Scans loaded Java classes for static string fields and field names containing common credential keywords.",
        "script": r"""
Java.perform(function() {
    console.log('[*] Starting hardcoded credential scan...');

    var keywords = [
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
        'auth', 'credential', 'client_secret', 'access_key', 'username'
    ];

    function looksLikeSecret(str) {
        if (!str) return false;
        var lower = str.toString().toLowerCase();
        for (var i = 0; i < keywords.length; i++) {
            if (lower.indexOf(keywords[i]) !== -1) {
                return true;
            }
        }
        return false;
    }

    var foundCredentials = [];

    function tryField(field, className, clazzWrapper) {
        try {
            field.setAccessible(true);
            var fieldName = field.getName();
            var fieldType = field.getType().getName();
            if (fieldType !== 'java.lang.String' && fieldType !== 'java.lang.CharSequence') {
                return;
            }

            var value = null;
            var isStatic = (field.getModifiers() & 0x0008) !== 0;
            if (isStatic) { // static
                try {
                    value = field.get(null);
                } catch (e) {
                    value = null;
                }
            } else {
                // Try to instantiate the class (if it has a default constructor) and read the instance field
                try {
                    var inst = null;
                    try {
                        inst = clazzWrapper.$new();
                    } catch (e) {
                        // fallback: try reflection-based newInstance
                        try {
                            inst = clazzWrapper.class.newInstance();
                        } catch (e2) {
                            inst = null;
                        }
                    }

                    if (inst !== null) {
                        try {
                            value = field.get(inst);
                        } catch (e3) {
                            value = null;
                        }
                    }
                } catch (e) {
                    // ignore instantiation errors
                    value = null;
                }
            }

            if (looksLikeSecret(fieldName) || looksLikeSecret(value)) {
                var result = '[*] Possible hardcoded credential: ' + className + '.' + fieldName + ' = ' + value;
                console.log(result);
                foundCredentials.push(result);
            }
        } catch (e) {
            // ignore field access errors
        }
    }

    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.indexOf('java.') === 0 || className.indexOf('android.') === 0 || className.indexOf('dalvik.') === 0 || className.indexOf('com.android.') === 0) {
                return;
            }

            try {
                var clazz = Java.use(className);
                var fields = clazz.class.getDeclaredFields();
                for (var i = 0; i < fields.length; i++) {
                    tryField(fields[i], className, clazz);
                }
            } catch (e) {
                // ignore classes that cannot be reflected
            }
        },
        onComplete: function() {
            if (foundCredentials.length > 0) {
                console.log('[*] Hardcoded credential scan complete - found ' + foundCredentials.length + ' possible items:');
                for (var i = 0; i < foundCredentials.length; i++) {
                    console.log(foundCredentials[i]);
                }
            } else {
                console.log('[*] Hardcoded credential scan complete - no hardcoded credentials found.');
            }
        }
    });
});
"""
    },

    "Custom Script (Edit Below)": {
        "description": "Write your own Frida script. Edit the script in the text area below before injecting.",
        "script": r"""
/* Custom Frida Script - edit as needed */
setTimeout(function () {
    Java.perform(function () {
        console.log('[*] Custom script running');
        // Add your hooks here
    });
}, 0);
"""
    }
}

# Preserve key script aliases in the selection list, then keep only the requested scripts
BYPASS_SCRIPTS["SSL Pinning Bypass"] = BYPASS_SCRIPTS["SSL Pinning Bypass (Universal)"]
BYPASS_SCRIPTS["Root Detection"] = BYPASS_SCRIPTS["Root Detection Bypass"]
BYPASS_SCRIPTS["Deep Link Observer"] = BYPASS_SCRIPTS["Android DeepLink Observer"]
BYPASS_SCRIPTS["DeepLink Script"] = BYPASS_SCRIPTS["Android DeepLink Observer"]

KEEP_ONLY = [
    "SSL Pinning Bypass (Universal)",
    "SSL Pinning Bypass",
    "Root Detection Bypass",
    "Root Detection",
    "Android DeepLink Observer",
    "Deep Link Observer",
    "DeepLink Script",
    "Firebase DataSnapshot Logger",
    "Hardcoded Credential Scanner",
    "Screenshot Protection Bypass",
    "External Storage APIs Tracing with Frida",
]
BYPASS_SCRIPTS = {k: BYPASS_SCRIPTS[k] for k in KEEP_ONLY if k in BYPASS_SCRIPTS}

# ============= DYNAMIC LOADER FOR EXTERNAL SCRIPTS =============
def load_external_frida_scripts():
    """
    Dynamically load all Frida scripts from a default external scripts folder.
    Adds them to the BYPASS_SCRIPTS dictionary.
    """
    import os
    import re
    from pathlib import Path

    home = Path.home()
    candidates = [
        home / "Downloads" / "Frida-Mobile-Scripts-master" / "Android",
        home / "Downloads" / "Frida-Mobile-Scripts" / "Android",
        Path.cwd() / "external_frida_scripts",
        Path.cwd() / "Frida-Mobile-Scripts" / "Android",
        Path.cwd() / "Frida-Mobile-Scripts-master" / "Android",
    ]

    external_path = next((p for p in candidates if p.exists()), None)
    if external_path is None:
        print("[!] External scripts folder not found in default search paths.")
        print(f"    Search locations: {', '.join(str(p) for p in candidates)}")
        return

    try:
        # Get all .js files
        js_files = sorted([f for f in os.listdir(external_path) if f.endswith('.js')])
        
        print(f"\n[*] Loading {len(js_files)} external Frida scripts from {external_path}...")
        
        for filename in js_files:
            filepath = os.path.join(external_path, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                # Extract description from header
                description = "External Frida script"
                lines = script_content.split('\n')
                
                for line in lines[:20]:
                    if 'Name:' in line or 'Description:' in line:
                        parts = re.split(r'Name:|Description:', line)
                        if len(parts) > 1:
                            description = parts[1].strip().rstrip('*/').strip()
                            break
                
                # Create script name from filename (convert_this_to_This)
                script_name = filename.replace('.js', '')
                script_name = ' '.join(word.capitalize() for word in script_name.split('_'))
                
                # Add to BYPASS_SCRIPTS if not already present
                if script_name not in BYPASS_SCRIPTS:
                    BYPASS_SCRIPTS[script_name] = {
                        "description": description,
                        "script": script_content
                    }
                    print(f"  [+] Loaded: {script_name}")
            
            except Exception as e:
                print(f"  [-] Error loading {filename}: {str(e)}")
        
        print(f"[+] Total scripts now available: {len(BYPASS_SCRIPTS)}\n")
    
    except Exception as e:
        print(f"[!] Error loading external scripts: {str(e)}")

# Load external scripts on module import
# External scripts are disabled because the active script list is limited
# to SSL pinning, root detection bypass, and deep link observer only.
# try:
#     load_external_frida_scripts()
# except Exception as e:
#     print(f"[!] Failed to load external scripts: {str(e)}")
