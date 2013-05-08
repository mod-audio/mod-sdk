var dashboard, bundles, effects, reload, menu, icon, settings, settingsWindow
var default_template // loaded in index.html
$(document).ready(function() {
    dashboard = $('#pedalboard-dashboard')
    bundles = $('#bundle-select')
    effects = $('#effect-select')
    reload = $('#reload')
    menu = $('#effect-menu')
    settings = $('#settings')
    settingsWindow = $('#settings-window')

    effects.hide()

    bundles.change(function() { getEffects() })
    effects.change(function() { showEffect() })
    $('#screenshot').click(function() {
	var iconImg = $('<img>')
	var param = { bundle: bundles.val(),
		      effect: effects.val(),
		      width: icon.width(),
		      height: icon.height()
		    }
	dashboard.find('img').remove()
	$.ajax({ url: '/screenshot',
		 data: param,
		 success: function(result) {
		     if (result.ok) {
			 $('<img class="thumb">').appendTo(dashboard).attr('src', 'data:image/png;base64,'+result.thumbnail)
			 $('<img class="screenshot">').appendTo(dashboard).attr('src', 'data:image/png;base64,'+result.screenshot)
		     } else {
			 alert('Could not generate thumbnail')
		     }
		 },
		 error: function(resp) {
		     alert("Error: Can't generate thumbnail. Is your server running? Check the logs.")
		 }
	       })
    })

    $('#install').click(function() {
	$.ajax({ url: '/post/device/' + bundles.val(),
		 success: function(result) {
		     if (result.ok)
			 alert("Effect installed")
		     else
			 alert("Host said: " + result.error)
		 },
		 error: function(resp) {
		     alert("Error: Can't install bundle. Is your server running? Check the logs.")
		 }
	       })
    })

    $('#publish').click(function() {
	$.ajax({ url: '/post/cloud/' + bundles.val(),
		 success: function(result) {
		     if (result.ok)
			 alert("Effect published")
		     else
			 alert("Cloud said: " + result.error)
		 },
		 error: function(resp) {
		     alert("Error: Can't publish bundle. Is your server running? Check the logs.")
		 }
	       })
    })

    $('#settings').click(function() {
	$.ajax({ url: '/config/get',
		 success: function(config) {
		     var key
		     for (key in config)
			 settingsWindow.find('#'+key).val(config[key])
		     settingsWindow.show()
		 },
		 error: function() {
		     alert("Error: Can't get current configuration. Is your server running? Check the logs.")
		 }
	       })
    })
    $('#settings-cancel').click(function() {
	settingsWindow.hide()
	return false
    })
    $('#settings-save').click(function() {
	var config = {}
	settingsWindow.find('input').each(function() {
	    config[this.id] = $(this).val()
	});
	$.ajax({ url: '/config/set',
		 type: 'POST',
		 data: JSON.stringify(config),
		 success: function() {
		     settingsWindow.hide()
		 },
		 error: function() {
		     alert("Error: Can't set configuration. Is your server running? Check the logs.")
		 }
	       })
	return false
    })
    settingsWindow.find('.controls span').click(function() {
	var self = $(this)
	self.parent().find('input').val(self.attr('data'))
    })

    var hash = window.location.hash.replace(/^#/, '')
    getBundles(function() {
	if (hash) {
	    var bundle = hash.split(/,/)[0]
	    var effect = hash.split(/,/)[1]
	    bundles.val(bundle)
	    getEffects(function() {
		if (effect) {
		    effects.val(effect)
		    showEffect()
		}
	    })
	}
    })
})

function getBundles(callback) {
    $.ajax({ url: '/bundles',
	     success: function(data) {
		 dashboard.html('')
		 menu.hide()
		 if (data.length == 0) {
		     bundles.hide()
		     $('#no-bundles').show()
		     return
		 }
		 $('#no-bundles').hide()
		 bundles.show()
		 bundles.find('option').remove()
		 $('<option>').val('').html('-- Select Bundle --').appendTo(bundles)
		 for (var i in data) {
		     $('<option>').val(data[i]).html(data[i]).appendTo(bundles)
		 }
		 if (callback != null)
		     callback()
	     },
	     error: function(resp) {
		 alert("Error: Can't get list of bundles. Is your server running? Check the logs.")
	     }
	   })
}

function getEffects(callback) {
    var bundle = bundles.val()
    window.location.hash = bundle
    if (!bundle) {
	effects.hide()
	return
    }
    $.ajax({ url: '/effects/' + bundle,
	     success: function(data) {
		 effects.find('option').remove()
		 $('<option>').html('-- Select Effect --').appendTo(effects)
		 plugins = data.plugins
		 for (var url in plugins) {
		     var effect = plugins[url]
		     $('<option>').val(effect.url).html(effect.name).data(effect).appendTo(effects)
		 }
		 effects.show()
		 if (callback != null)
		     callback()
	     },
	     error: function(resp) {
		 alert("Error: Can't get list of effects. Is your server running? Check the logs.")
	     }
	   })
}

function showEffect() {
    dashboard.html('')
    menu.hide()
    var bundle = bundles.val()
    if (!bundle) {
	window.location.hash = ''
	return
    }
    var options = effects.find('option:selected').data()
    if (!options.url) {
	window.location.hash = bundle
	return
    }
    if (!options.icon)
	options.icon = {}
    if (!options.icon.template)
	options.icon.template = default_template
    window.location.hash = bundle + ',' + options.url
    var element = $(Mustache.render(options.icon.template, getTemplateData(options)))
    element.find('[mod-role=input-control-port]').each(function() {
	$(this).knob()
    })

    var handle = element.find('[mod-role=drag-handle]')
    if (handle.length > 0)
	element.draggable({ handle: handle })
    element.find('[mod-role=bypass]').click(function() {
	var light = element.find('[mod-role=bypass-light]')
	if (light.hasClass('on')) {
	    light.addClass('off')
	    light.removeClass('on')
	} else {
	    light.addClass('on')
	    light.removeClass('off')
	}
    })

    dashboard.append(element)
    menu.show()
    icon = element
}



function getTemplateData(options) {
    var i, port, control, symbol
    var data = $.extend({}, options.icon.templateData)
    data.effect = options
    data.ns = '?bundle=' + options.package + '&url=' + escape(options.url)
    if (!data.controls)
	return data
    var controlIndex = {}
    for (i in options.ports.control.input) {
	port = options.ports.control.input[i]
	controlIndex[port.symbol] = port
    }
    for (var i in data.controls) {
	control = data.controls[i]
	if (typeof control == "string") {
	    control = controlIndex[control]
	} else {
	    control = $.extend({}, controlIndex[control.symbol], control)
	}
	data.controls[i] = control
    }
    return data
}

