var DRAG_PRECISION = 1

JqueryClass('knob', {
    init: function() {
	var self = $(this)

	self.knob('getSize')
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
	    self.knob('mouseDown', e)
	    $(document).bind('mouseup', upHandler)
	    $(document).bind('mousemove', moveHandler)
	    self.trigger('knobstart')
	})
    },

    getSize: function() {
	var self = $(this)
	setTimeout(function() {
	    var url = self.css('background-image').replace('url(', '').replace(')', '').replace("'", '').replace('"', '');
	    var height = self.css('background-size').split(/ /)[1]
	    if (height)
		height = parseInt(height.replace(/\D/, ''))
	    var bgImg = $('<img />');
	    bgImg.css('max-width', '999999999px')
	    bgImg.hide();
	    console.log(height)
	    bgImg.bind('load', function() {
		if (!height)
		    height = bgImg.height()
		self.data('steps', height * bgImg.width() / (self.width() * bgImg.height()))
		self.data('size', self.width())
		console.log(self.width())
		console.log(bgImg.height())
		bgImg.remove()
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
	diff = parseInt(diff / DRAG_PRECISION)
	var rotation = self.data('rotation')
	var steps = self.data('steps')
	rotation = (rotation + diff - steps) % steps
	self.data('rotation', rotation)
	self.data('lastY', e.pageY)
	self.knob('setRotation', rotation)
    },

    setRotation: function(rotation) {
	var self = $(this)
	rotation *= self.data('size')
	rotation += 'px 0px'
	self.css('background-position', rotation)
    }
})
