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
	    self.knob('mouseDown', e)
	    $(document).bind('mouseup', upHandler)
	    $(document).bind('mousemove', moveHandler)
	    self.trigger('knobstart')
	})
    },

    getSize: function() {
	var self = $(this)
	setTimeout(function() {
	    var url = self.find('.image').css('background-image').replace('url(', '').replace(')', '').replace("'", '').replace('"', '');
	    var bgImg = $('<img />');
	    bgImg.css('max-width', '999999999px')
	    bgImg.hide();
	    bgImg.bind('load', function() {
		self.data('steps', bgImg.width() / bgImg.height())
		self.data('size', bgImg.height())
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
	rotation += self.data('size') * diff
	self.data('rotation', rotation)
	self.data('lastY', e.pageY)
	self.knob('setRotation', rotation)
    },

    setRotation: function(rotation) {
	var self = $(this)
	rotation += 'px 0px'
	self.find('.image').css('background-position', rotation)
	console.log(rotation)
    }
})
