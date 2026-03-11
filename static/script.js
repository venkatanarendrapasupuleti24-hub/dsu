document.querySelector("form").addEventListener("submit", function(){

    let distance = document.querySelector("[name='distance']").value

    if(distance < 0){
        alert("Distance cannot be negative")
        return false
    }

})