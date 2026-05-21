
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
