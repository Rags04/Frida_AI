
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
