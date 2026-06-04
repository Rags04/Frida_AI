Java.perform(()=>{
        Java.enumerateLoadedClasses({
            onMatch : function(name, handle){
                if(name.includes("com.scb.breezebanking.hk")){
                    console.log(name);
            }
        },
        onComplete : function(){
            console.log("------Done----");
        }
    });

});
               