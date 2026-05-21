
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
