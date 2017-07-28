

class Chat{
    constructor(waitforui){
        this.connected=false;
        this.authorized=false;
        this.callbacks={};
        this.conversation=[];
        this.waitforui=waitforui
    }

    connect(url,callback){
        var $this=this;

        this.channel = io(url);

        this.channel.on('connect', function() {
            $this.connected = true;
            $this.setup()
            callback()
        });
    }

    setup(){
        var $this=this;

        this.channel.on('auth', function(data) {
            console.log("control","IN", "auth",data);
            $this.authData=data;
            $this.callCallback('auth',data);
        });

        this.channel.on('ping', function(data) {
            console.log("control","IN", "ping",data);
            $this.callCallback('ping',data);
        });

        this.channel.on('msg', function(data) {
            console.log("control","IN", "msg",data);
            $this.callCallback('msg',data);
        });
    }

    login(user,password,callback){
        var $this=this;

        this.send({op:"auth",user:user,password:password});

        this.setCallback("auth",function(msg){
            $this.authorized=true;
            $this.namespace=msg.namespace;

            console.log("communication","connecting to namespace",msg.namespace)
            $this.comChannel = io('http://' + document.domain + ':' + location.port+"/"+msg.namespace);

            $this.comChannel.on('connect', function() {
                console.log("communication","connected")
                if (callback!==undefined)
                    callback(msg);
            });

            $this.comChannel.on('ping', function(data) {
                console.log("comunication","IN", "ping",data);
                $this.callCallback('ping',data);
            });

            $this.comChannel.on('msg', function(msg) {
                console.log("communication","IN", "msg",msg);
                $this.waitforui(function(){
                    $this.conversation.push(msg);
                    $this.callCallback('msg',msg);
                })

            });
        })
    }

    sendMsg(to,text){
        var msg = {op:"msg",to:to,text:text};
        this.conversation.push(msg);
        this.send(msg);
    }

    send(msg){
        console.log("control","OUT",msg)
        this.channel.emit('msg', msg);
    }

    getCallback(type){
        var callback=this.callbacks[type];
        this.callbacks[type]=undefined;
        return callback;
    }

    setCallback(type,fnc){
        this.callbacks[type]=fnc;
    }

    callCallback(type,msg){
        var callback=this.getCallback(type);
        if (callback!=undefined)
            callback(msg);
    }
}
