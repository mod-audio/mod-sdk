$(document).ready(function() {
    var uri = window.location.hash.replace(/^#/, '')

    if (uri) {
        $.ajax({
            url: '/effect/get/',
            data: { uri: uri },
            success: function(resp) {
                var options = {
                    defaultIconTemplate: defaultIconTemplate,
                    bypassed: false,
                }
                new GUI(resp.data, options).render(null, function(icon) {
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
