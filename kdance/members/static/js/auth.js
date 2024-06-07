$(document).ready(() => {
    $('#nav-logout').click(() => {
        $.ajax({
            url: logoutUrl,
            type: 'POST',
            success: () => {
                window.location.replace("/");
            },
            eroor: () => {
                console.log("oups");
            }
        });
    });
});
