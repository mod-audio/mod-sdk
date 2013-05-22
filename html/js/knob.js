JqueryClass('knob', {
    init: function(options) {
	var self = $(this)
	self.data('container', options.container)
	self.knob('getSize', function() { self.knob('config', options.port) })
	self.data('rotation', 0)

	self.on('dragstart', function(event) { event.preventDefault() })

	var moveHandler = function(e) {
	    self.knob('mouseMove', e)
	}
	
	var upHandler = function(e) {
	    self.knob('mouseUp', e)
	    $(document).unbind('mouseup', upHandler)
	    $(document).unbind('mousemove', moveHandler)
	    //self.trigger('knobstop')
	}
	
	self.mousedown(function(e) {
	    if (e.which == 1) { // left button
		self.knob('mouseDown', e)
		$(document).bind('mouseup', upHandler)
		$(document).bind('mousemove', moveHandler)
		self.trigger('knobstart')
	    }
	})
    },

    config: function(port) {
	var self = $(this)

	var portSteps
	if (port.toggle) {
	    port.minimum = port.minimum || 0
	    port.maximum = port.maximum || 1
	    portSteps = 2
	} else if (port.enumeration) {
	    portSteps = port.scalePoints.length
	} else {
	    portSteps = self.data('knobSteps')
	}

	if (port.rangeSteps)
	    portSteps = Math.min(port.rangeSteps, portSteps)

	// This is a bit verbose and could be optmized, but it's better that
	// each port property used is documented here
	self.data('symbol', port.symbol)
	self.data('default', port.default)
	self.data('enumeration', port.enumeration)
	self.data('integer', port.integer)
	self.data('maximum', port.maximum)
	self.data('minimum', port.minimum)
	self.data('logarithm', port.logarithm)
	self.data('scalePoints', port.scalePoints)
	self.data('toggle', port.toggle)

	if (port.logarithm) {
	    self.data('scaleMinimum', Math.log(port.minimum) / Math.log(2))
	    self.data('scaleMaximum', Math.log(port.maximum) / Math.log(2))
	} else {
	    self.data('scaleMinimum', port.minimum)
	    self.data('scaleMaximum', port.maximum)
	}

	var format
	if (port.unit)
	    format = port.unit.render.replace('%f', '%.2f')
	else
	    format = '%.2f'
	if (port.integer)
	    format = format.replace(/%\.\d+f/, '%d')
	self.data('format', format)

	self.data('portSteps', portSteps)
	self.data('dragPrecision', Math.ceil(50/portSteps))
    },

    getSize: function(callback) {
	var self = $(this)
	setTimeout(function() {
	    var url = self.css('background-image').replace('url(', '').replace(')', '').replace("'", '').replace('"', '');
	    var height = self.css('background-size').split(/ /)[1]
	    if (height)
		height = parseInt(height.replace(/\D+$/, ''))
	    var bgImg = $('<img />');
	    bgImg.css('max-width', '999999999px')
	    bgImg.hide();
	    bgImg.bind('load', function() {
		if (!height)
		    height = bgImg.height()
		self.data('knobSteps', height * bgImg.width() / (self.width() * bgImg.height()))
		self.data('size', self.width())
		bgImg.remove()
		callback()
	    });
	    self.append(bgImg);
	    bgImg.attr('src', url);    
	}, 1)
    },

    mouseDown: function(e) {
	var self = $(this)
	self.data('lastY', e.pageY)
    },

    mouseUp: function(e) {
	var self = $(this)
    },

    mouseMove: function(e) {
	var self = $(this)
	var diff = self.data('lastY') - e.pageY
	diff = parseInt(diff / self.data('dragPrecision'))
	var rotation = self.data('rotation')

	rotation += diff
	self.data('rotation', rotation)
	if (Math.abs(diff) > 0)
	    self.data('lastY', e.pageY)
	self.knob('setRotation', rotation)
    },

    setRotation: function(rotation) {
	var self = $(this)

	var knobSteps = self.data('knobSteps')
	var portSteps = self.data('portSteps')
	if (portSteps == 1)
	    rotation = Math.round(knobSteps/2)
	else if (portSteps != null)
	    rotation *= Math.round(knobSteps / (portSteps-1))

	rotation = Math.min(rotation, knobSteps-1)
	rotation = Math.max(rotation, 0)

	var bgShift = rotation * -self.data('size')
	bgShift += 'px 0px'
	self.css('background-position', bgShift)

	self.knob('valueFromRotation', rotation)
    },

    valueFromRotation: function(rotation) {
	var self = $(this)
	var container = self.data('container')
	var format = self.data('format')
	var symbol = self.data('symbol')
	var min = self.data('scaleMinimum')
	var max = self.data('scaleMaximum')

	var portSteps = self.data('portSteps')

	var value = min + rotation * (max - min) / (portSteps - 1)
	if (self.data('logarithm'))
	    value *= value

	if (self.data('integer'))
	    value = Math.round(value)

	container.find('[mod-role=input-control-value][mod-port-symbol='+symbol+']').text(sprintf(format, value))
    }
})
