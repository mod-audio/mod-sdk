function getEffects(bundle, callback) {
    window.location.hash = bundle
    if (!bundle) {
	effects.hide()
	return
    }
    $.ajax({ url: '/effects/' + bundle,
	     success: function(result) {
		 if (!result.ok) {
		     alert(result.error)
		     return
		 }
		 callback(result.data.plugins)
	     },
	     error: function(resp) {
		 alert("Error: Can't get list of effects. Is your server running? Check the logs.")
	     }
	   })
}

function renderIcon(template, data) {
    var element = $('<strong>') // TODO this container must be <div class="pedal">
    element.html(Mustache.render(template, getTemplateData(data)))
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

    return element
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
    DEBUG = JSON.stringify(data, undefined, 4)
    return data
}


function JqueryClass(name, methods) {
    (function($) {
	$.fn[name] = function(method) {
	    if (methods[method]) {
		return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
	    } else if (typeof method === 'object' || !method) {
		return methods.init.apply(this, arguments);
	    } else {
		$.error( 'Method ' +  method + ' does not exist on jQuery.' + name );
	    }
	}
    })(jQuery);
}
