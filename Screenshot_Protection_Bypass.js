
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
