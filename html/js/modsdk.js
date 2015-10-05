var bundles, effects, content, iconCanvas, settingsCanvas, deployWindow, renderedIcon, version, section
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
    deployWindow = $('#content-deploy')

    $.ajax({
        url: '/config/get',
        success: function(config) {
            for (var key in config) {
                deployWindow.find('#'+key).val(config[key])
            }
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
        var options = effects.find('option:selected').data()
        if (options.gui.iconTemplate == null) {
            alert("Cannot generate screenshot without an Icon!")
            return
        }

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

    $('#deploy').click(function() {
        saveDeployConfiguration(function() {
            $.ajax({
                url: '/post/' + bundles.val(),
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

    deployWindow.find('.controls span').click(function() {
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
    if (bundle) {
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
    } else {
        window.location.hash = ''
        effects.hide()
        content.hide()
    }
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

    $('#info-uri').html(options.uri)
    $('#info-name').html(options.name)
    $('#info-label').html(options.label)
    $('#info-author').html(options.author.name)
    $('#info-brand').html(options.brand)
    $('#info-version').html(options.version)

    $('#info-license').html(options.license || "missing license")
    $('#info-comment').html(options.comment || "missing comment")

    var errors, warnings

    if (options.errors.length || options.warnings.length)
    {
        if (options.errors.length) {
            errors = '<p><b>Errors:</b></p><ol>'
            for (var i in options.errors)
                errors += '<li>' + options.errors[i] + '</li>'
            errors += '</ol>'
        } else {
            errors = ''
        }

        if (options.warnings.length) {
            warnings = '<p><b>Warnings:</b></p><ol>'
            for (var i in options.warnings)
                warnings += '<li>' + options.warnings[i] + '</li>'
            warnings += '</ol>'
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

    window.location.hash = bundle + ',' + options.uri + ',' + section

    var gui = new GUI(options, {
        defaultIconTemplate: defaultIconTemplate,
        defaultSettingsTemplate: defaultSettingsTemplate,
        bypassed: false,
    })

    gui.render(null, function(icon, settings) {
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

function saveDeployConfiguration(callback) {
    var config = {}
    deployWindow.find('input').each(function() {
        config[this.id] = $(this).val()
    });
    $.ajax({
        url: '/config/set',
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
