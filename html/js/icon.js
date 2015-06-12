$(document).ready(function() {
    var uri = window.location.hash.replace(/^#/, '')

    if (uri) {
        $.ajax({
            url: '/effect/get/',
            data: { url: uri },
            success: function(effect) {
                new GUI(effect).render(function(icon) {
                    $('#pedalboard-dashboard').append(icon)
                })
            },
            error: function(resp) {
                alert("Error: Can't get requested plugin via URI.")
            },
            dataType: 'json'
        })
    }
})
