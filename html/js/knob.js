JqueryClass('knob', {
    init: function() {
	var self = $(this)

	self.knob('getSize')
	self.data('rotation', 0)

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
	    console.log(self.find('.image').attr('id'))
	    self.knob('mouseDown', e)
	    $(document).bind('mouseup', upHandler)
	    $(document).bind('mousemove', moveHandler)
	    self.trigger('knobstart')
	})
    },

    getSize: function() {
	var self = $(this)
	setTimeout(function() {
	    var img = self.find('.image')
	    var url = img.css('background-image').replace('url(', '').replace(')', '').replace("'", '').replace('"', '');
	    var height = img.css('background-size').split(/ /)[1]
	    if (height)
		height = parseInt(height.replace(/\D/, ''))
	    var bgImg = $('<img />');
	    bgImg.css('max-width', '999999999px')
	    bgImg.hide();
	    bgImg.bind('load', function() {
		self.data('steps', bgImg.width() / bgImg.height())
		self.data('size', height || bgImg.height())
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
	var rotation = self.data('rotation')
	var steps = self.data('steps')
	rotation = (rotation + diff - steps) % steps
	self.data('rotation', rotation)
	self.data('lastY', e.pageY)
	self.knob('setRotation', rotation)
    },

    setRotation: function(rotation) {
	var self = $(this)
	console.log(rotation)
	rotation *=  self.data('size')
	rotation += 'px 0px'
	self.find('.image').css('background-position', rotation)
    }
})
