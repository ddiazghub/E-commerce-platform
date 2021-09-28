function getCookie(name) {
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    if (match) return match[2];
  }
/*
document.querySelectorAll("form").forEach((form) => {
    form.onsubmit() {
        const url = "/" + form.id;
        let request = new XMLHttpRequest();
        request.open("POST", url, true);
        request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
        request.setRequestHeader("Authorization", "Bearer " + getCookie("token"));
        //request.setRequestHeader('Accept', 'application/json');
        request.send(formData)
    }
})
*/