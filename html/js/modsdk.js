var dashboard, bundles, effects, reload
$(document).ready(function() {
    dashboard = $('#pedalboard-dashboard')
    bundles = $('#bundle-select')
    effects = $('#effect-select')
    reload = $('#reload')

    effects.hide()

    bundles.change(function() { getEffects() })
    effects.change(function() { showEffect() })

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
}

function getTemplateData(options) {
    var template_data = $.extend({}, options.icon.template_data)
    template_data.effect = options
    template_data.ns = 'url=' + escape(options.url)
    return template_data
}

