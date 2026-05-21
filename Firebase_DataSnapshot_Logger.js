
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
