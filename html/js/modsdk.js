var dashboard, bundles, effects, reload, menu, icon
$(document).ready(function() {
    dashboard = $('#pedalboard-dashboard')
    bundles = $('#bundle-select')
    effects = $('#effect-select')
    reload = $('#reload')
    menu = $('#effect-menu')

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
	$('<img class="thumb">').attr('src', '/thumb_screenshot?'  + $.param(param)).appendTo(dashboard)
	$('<img class="icon">').attr('src', '/icon_screenshot?' + $.param(param)).appendTo(dashboard)
	
    })

    $('#install').click(function() {
	$.ajax({ url: '/install/' + bundles.val(),
		 success: function(result) {
		     if (result.ok)
			 alert("Effect installed")
		     else
			 alert(result.msg)
		 },
		 error: function(resp) {
		     alert("Error: Can't install bundle. Is your server running? Check the logs.")
		 }
	       })
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
    window.location.hash = bundle + ',' + options.url
    var element = $(Mustache.render(options.icon.template, getTemplateData(options)))

    element.draggable({ handle: element.find('[mod-role=drag-handle]') })
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

    var max_inputs = 4
    var num_inputs = options.ports.audio.input.length
    for (var i=0; i < max_inputs; i++) {
	var cls = '.pedal-input-'+i
	var input = element.find(cls)
	if (i >= num_inputs)
	    input.remove()
    }
    
    var max_outputs = 4
    var num_outputs = options.ports.audio.output.length
    for (var i=0; i < max_outputs; i++) {
	var cls = '.pedal-output-'+i
	var output = element.find(cls)
	if (i >= num_outputs) 
	    output.remove()
    }

    dashboard.append(element)
    menu.show()
    icon = element
}



function getTemplateData(options) {
    var i, port, control, symbol
    var data = $.extend({}, options.icon.template_data)
    data.effect = options
    data.ns = 'url=' + escape(options.url)
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

