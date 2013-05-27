var defaultIconTemplate
$(document).ready(function() {
    var hash = window.location.hash.replace(/^#/, '')
    var bundle = hash.split(/,/)[0]
    var effect = hash.split(/,/)[1]
    if (bundle && effect) {
	getEffects(bundle, function(plugins) {
	    effect = plugins[effect]
	    var element = new GUI(effect).renderIcon(effect.gui.iconTemplate || defaultIconTemplate)
	    $('#pedalboard-dashboard').append(element)
	})
    }
    
})