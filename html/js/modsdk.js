var bundles, effects, content, iconCanvas, settingsCanvas, publishWindow, renderedIcon, version, section
var defaultIconTemplate, defaultSettingsTemplate // loaded in index.html
var DEBUG // holds template debugging info
$(document).ready(function() {
    var firstSection = $('ul#menu li').first().attr('id').replace(/^tab-/, '')
    section = window.location.hash.split(/,/)[2] || firstSection
    makeTabs()
    bundles = $('#bundle-select')
    effects = $('#effect-select')
    content = $('#content-wrapper')

    iconCanvas = $('#content-icon .canvas')
    screenshotCanvas = $('#content-screenshot .canvas')
    settingsCanvas = $('#content-settings .canvas')
    publishWindow = $('#content-publish')

    $.ajax({
        url: '/config/get',
        success: function(config) {
            var key
            for (key in config)
                publishWindow.find('#'+key).val(config[key])
        },
        error: function() {
            alert("Error: Can't get current configuration. Is your server running? Check the logs.")
        }
    })

    version = $('#version')

    effects.hide()
    version.hide()

    bundles.change(function() { loadEffects() })
    effects.change(function() { showEffect() })
    $('#next-bundle').click(function() {
        bundles.val(bundles.find(':selected').next().val())
        loadEffects()
    })
    $('#screenshot').click(function() {
        var iconImg = $('<img>')
        screenshotCanvas.find('img').remove()
        $.ajax({
            url: '/screenshot',
            data: {
                uri   : effects.val(),
                width : renderedIcon.width(),
                height: renderedIcon.height()
            },
            success: function(result) {
                if (result.ok) {
                    $('<img class="thumb">').appendTo(screenshotCanvas).attr('src', 'data:image/png;base64,'+result.thumbnail)
                    $('<img class="screenshot">').appendTo(screenshotCanvas).attr('src', 'data:image/png;base64,'+result.screenshot)
                } else {
                    alert('Could not generate thumbnail')
                }
            },
            error: function(resp) {
                alert("Error: Can't generate thumbnail. Is your server running? Check the logs.")
            },
            dataType: 'json'
        })
    })

    $('#install').click(function() {
        savePublishConfiguration(function() {
            $.ajax({ url: '/post/device/' + bundles.val(),
                success: function(result) {
                    if (result.ok)
                        alert("Effect installed")
                    else
                        alert("Host said: " + result.error)
                },
                error: function(resp) {
                    alert("Error: Can't install bundle. Is your server running? Check the logs.")
                },
                timeout: 300000,
                dataType: 'json'
              })
        })
    })

    $('#publish').click(function() {
        savePublishConfiguration(function() {
            $.ajax({
                url: '/post/cloud/' + bundles.val(),
                success: function(result) {
                    if (result.ok)
                        alert("Effect published")
                    else
                        alert("Cloud said: " + result.error)
                },
                error: function(resp) {
                    alert("Error: Can't publish bundle. Is your server running? Check the logs.")
                },
                timeout: 300000,
                dataType: 'json'
            })
        })
    })

    publishWindow.find('.controls span').click(function() {
        var self = $(this)
        self.parent().find('input').val(self.attr('data'))
    })

    $('button.debug').click(function() {
        $('#debug-window pre').text(DEBUG)
        $('#debug-window').show()
    })
    $('#debug-cancel').click(function() {
        $('#debug-window').hide()
    })

    loadBundles()
})

function loadBundles() {
    $.ajax({
        url: '/bundles',
        success: function(data) {
            content.hide()
            if (data.length == 0) {
                bundles.hide()
                $('#next-bundle').hide()
                $('#no-bundles').show()
                return
            }
            $('#next-bundle').show()
            $('#no-bundles').hide()
            bundles.show()
            bundles.find('option').remove()
            $('<option>').val('').html('-- Select Bundle --').appendTo(bundles)
            data.sort()
            for (var i in data) {
                $('<option>').val(data[i]).html(data[i]).appendTo(bundles)
            }

            var hash = window.location.hash.replace(/^#/, '')
            if (hash) {
                var bundle = hash.split(/,/)[0]
                var uri    = hash.split(/,/)[1]
                bundles.val(bundle)
                loadEffects(function() {
                    if (uri) {
                        effects.val(uri)
                        showEffect()
                    }
                })
            }
        },
        error: function(resp) {
            alert("Error: Can't get list of bundles. Is your server running? Check the logs.")
        },
        dataType: 'json'
    })
}

function getEffects(bundle, callback) {
    window.location.hash = bundle
    if (!bundle) {
        effects.hide()
        return
    }
    $.ajax({
        url: '/effects',
        data: {
            bundle: bundle,
        },
        success: function(result) {
            if (!result.ok) {
                alert(result.error)
                return
            }
            callback(result.data)
        },
        error: function(resp) {
            alert("Error: Can't get list of effects. Is your server running? Check the logs.")
        },
        dataType: 'json'
    })
}

function loadEffects(callback) {
    var bundle = bundles.val()
    version.hide()
    getEffects(bundle, function(plugins) {
        effects.find('option').remove()
        $('<option>').html('-- Select Effect --').appendTo(effects)
        for (var uri in plugins) {
            var plugin = plugins[uri]
            $('<option>').val(plugin.uri).html(plugin.name).data(plugin).appendTo(effects)
        }
        effects.show()
        if (effects.children().length == 2) {
            effects.children().first().remove()
            showEffect()
        }
        if (callback != null)
            callback()
    })
}

function showEffect() {
    content.hide()
    var bundle = bundles.val()
    if (!bundle) {
        window.location.hash = ''
        return
    }
    var options = effects.find('option:selected').data()

    if (options.version) {
        version.html('v' + options.version + ' (' + options.stability + ')')
        version.show()
    } else {
        version.hide()
    }
    if (!options.uri) {
        window.location.hash = bundle
        return
    }

    var errors   = []
    var warnings = []

    errn = function(msg){
        errors.push(msg)
        return '<i>missing</i> ('+errors.length+')'
    }
    warnn = function(repl, msg){
        warnings.push(msg)
        return '<i>'+(repl || 'missing')+'</i> ['+warnings.length+']'
    }

    // name
    if (!options.name)
        $('#info-name-full').html(errn('missing name'))
    else
        $('#info-name-full').html(options.name)

    // author
    if (!options.author)
        $('#info-author-full').html(errn('missing author information'))
    else if (!options.author.name)
        $('#info-author-full').html(errn('missing author name'))
    else
        $('#info-author-full').html(options.author.name)

    // version
    if ((options.minorVersion == 0 && options.microVersion == 0) || options.minorVersion === undefined || options.microVersion === undefined)
        $('#info-version').html(errn('missing version information'))
    else
        $('#info-version').html(''+options.minorVersion+'.'+options.microVersion)

    // license
    if (!options.license)
        $('#info-license').html(errn('missing license'))
    else
        $('#info-license').html(options.license)

    // description
    if (!options.description)
        $('#info-description').html(errn('missing description'))
    else
        $('#info-description').html(options.description)

    // plugin shortname
    if (!options.shortname)
        $('#info-name-short').html(warnn(options.name, 'plugin shortname is not defined, will use full name instead'))
    else
        $('#info-name-short').html(options.shortname)

    // author shortname
    if (!options.author.shortname)
        $('#info-author-short').html(warnn(options.author.name, 'plugin author shortname is not defined, will use full name instead'))
    else
        $('#info-author-short').html(options.author.shortname)

    if (errors.length || warnings.length)
    {
        if (errors.length) {
            errorstr = '<p><b>Errors:</b></p><ol>'
            for (var i in errors)
                errorstr += '<li>' + errors[i] + '</li>'
            errorstr += '</ol>'
            errors = errorstr
            delete errorstr
        } else {
            errors = ''
        }

        if (warnings.length) {
            warningstr = '<p><b>Warnings:</b></p><ol>'
            for (var i in warnings)
                warningstr += '<li>' + warnings[i] + '</li>'
            warningstr += '</ol>'
            warnings = warningstr
            delete warningstr
        } else {
            warnings = ''
        }
    }
    else
    {
        errors = ''
        warnings = '<p>Congratulations, your plugin passes all basic tests without warnings!</p>'
    }

    $('#info-errors').html(errors)
    $('#info-warnings').html(warnings)

//     portsHtml = infoPorts.html('')
//     for (var i in options.ports.control.input) {
//         port = options.ports.control.input[i]
//         portsHtml.append(sprintf('\
//             <div class="controls clearfix"><label>Control Port #%d</label>\
//             <span>Name:   </span><input id="info_port_%s_name"   type="text" value="%s"/><br/>\
//             <span>Symbol: </span><input id="info_port_%s_symbol" type="text" value="%s"/><br/>\
//             <span>Minimum: </span><input id="info_port_%s_min" type="number" value="%f"/><br/>\
//             </div>',
//             port.index,
//             port.symbol, "fake-name-here", //port.name
//             port.symbol, port.symbol,
//             port.symbol, port.ranges.minimum
//         ))
//     }

    //infoPorts.html('<pre>' + JSON.stringify(options.ports.control.input) + '</pre>');

    window.location.hash = bundle + ',' + options.uri + ',' + section

    var gui = new GUI(options, {
        defaultIconTemplate: defaultIconTemplate,
        defaultSettingsTemplate: defaultSettingsTemplate
    })

    gui.render(function(icon, settings) {
        renderedIcon = icon
        var actions = $('<div>').addClass('mod-actions').appendTo(icon)
        $('<div>').addClass('mod-settings').appendTo(actions)
        $('<div>').addClass('mod-remove').appendTo(actions)

        iconCanvas.html('').append(icon)
        settingsCanvas.html('').append(settings)

        content.show()

        screenshotCanvas.html('')
        var param = '?uri=' + escape(options.uri)
        if (options.gui.thumbnail) {
            var thumb = $('<img class="thumb">')
            thumb.attr('src', '/effect/image/thumbnail.png'+param)
            thumb.appendTo(screenshotCanvas)
        }
        if (options.gui.screenshot) {
            var shot = $('<img class="screenshot">')
            shot.attr('src', '/effect/image/screenshot.png'+param)
            shot.appendTo(screenshotCanvas)
        }
    })
}

function makeTabs() {
    $('ul#menu li').each(function() {
        var item = $(this)
        item.click(function() {
            selectTab(item.attr('id').replace(/^tab-/, ''))
        })
    })

    $('.content').hide()

    selectTab(section)
}

function selectTab(newSection) {
    section = newSection
    var tab = $('#tab-'+section)
    var path = window.location.hash.split(/,/)
    if (path[2] != section) {
        path[2] = section
        window.location.hash = path.join(',')
    }
    $('.content').hide()
    $('ul#menu li.selected').removeClass('selected')
    tab.addClass('selected')
    $('#content-'+section).show()
}

function savePublishConfiguration(callback) {
    var config = {}
    publishWindow.find('input').each(function() {
        config[this.id] = $(this).val()
    });
    $.ajax({ url: '/config/set',
             type: 'POST',
             data: JSON.stringify(config),
             success: function() {
                 callback()
             },
             error: function() {
                 alert("Error: Can't set configuration. Is your server running? Check the logs.")
             },
             dataType: 'json'
          })
    return false
}

function slug() {
    var effect = effects.find('option:selected').data()
    return effect['name'].toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '').replace(/-+/g, '-')
}
