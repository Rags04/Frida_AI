
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
