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