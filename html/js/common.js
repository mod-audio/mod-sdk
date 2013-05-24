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
    return assignFunctionality(element, data)
}

function renderSettings(template, data) {
    var element = $('<div>')
    element.html(Mustache.render(template, getTemplateData(data)))
    return assignFunctionality(element, data)
}

function assignFunctionality(element, effect) {
    var controls = makePortIndex(effect.ports.control.input)

    element.find('[mod-role=input-control-port]').each(function() {
	var symbol = $(this).attr('mod-port-symbol')
	$(this).widget({ port: controls[symbol],
		       container: element
		     })
    });

    element.find('[mod-role=input-control-minimum]').each(function() {
	var symbol = $(this).attr('mod-port-symbol')
	if (!symbol) {
	    $(this).html('missing mod-port-symbol attribute')
	    return
	}
	var content = controls[symbol].minimum
	var format = controls[symbol].unit ? controls[symbol].unit.render : '%.2f'
	$(this).html(sprintf(format, controls[symbol].minimum))
    });
    element.find('[mod-role=input-control-maximum]').each(function() {
	var symbol = $(this).attr('mod-port-symbol')
	if (!symbol) {
	    $(this).html('missing mod-port-symbol attribute')
	    return
	}
	var content = controls[symbol].maximum
	var format = controls[symbol].unit ? controls[symbol].unit.render : '%.2f'
	$(this).html(sprintf(format, controls[symbol].maximum))
    });

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

function makePortIndex(ports) {
    var index = {}
    for (var i in ports) {
	var port = ports[i]
	index[port.symbol] = port
    }
    return index
}


function getTemplateData(options) {
    var i, port, control, symbol
    var data = $.extend({}, options.gui.templateData)
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


function JqueryClass() {
    var name = arguments[0]
    var methods = {}
    for (var i=1; i<arguments.length; i++) {
	$.extend(methods, arguments[i])
    }
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
