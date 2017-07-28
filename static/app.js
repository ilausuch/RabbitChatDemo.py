function parse_query_string(query) {
    var vars = query.split("&");
    var query_string = {};

    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        // If first entry with this name
        if (typeof query_string[pair[0]] === "undefined") {
            query_string[pair[0]] = decodeURIComponent(pair[1]);
        // If second entry with this name
        } else if (typeof query_string[pair[0]] === "string") {
            var arr = [query_string[pair[0]], decodeURIComponent(pair[1])];
            query_string[pair[0]] = arr;
        // If third or later entry with this name
        } else {
            query_string[pair[0]].push(decodeURIComponent(pair[1]));
        }
    }
    return query_string;
}

var app = angular.module('app', []);
var mc;


app.controller("MainController", function($rootScope,$scope,$timeout,$http,$q){
    mc=this;

    var query = window.location.search.substring(1);
    var qs = parse_query_string(query);
    var user= qs.u
    mc.user=user;
    mc.password="";

    mc.textToSend="test";
    $scope.connect=function(){


        console.log("Connecting User",user);

        mc.loading=true;
        mc.loged=false;

        mc.chat=new Chat($timeout);
        mc.chat.connect('http://' + document.domain + ':' + location.port,function(){
            mc.chat.login(mc.user,mc.password,function(msg){
                $timeout(function(){
                    mc.loading=false;
                    mc.loged=true;
                })
            })
        });
    }

    $scope.send=function(){
        mc.chat.sendMsg(mc.comunicateWith,mc.textToSend);

        $timeout(function(){
            $("#chatContent").scrollTo("max",100);
            mc.textToSend="";
        })

    }
});
