var wizard_db // populated in index.html
$(document).ready(function() {
    $('#wizard-window').wizard(wizard_db)
    $('#wizard').click(function() { $('#wizard-window').wizard('open') })
    $('#wizard-cancel').click(function() { $('#wizard-window').wizard('close') })
})

JqueryClass('wizard', {
    init: function(models) {
	var self = $(this)
	var model_list = Object.keys(models).sort()
	self.data('model_index', models)
	self.data('model_list', model_list)
	self.find('.previous').click(function() { self.wizard('shiftModel', -1) })
	self.find('.next').click(function() { self.wizard('shiftModel', 1) })
    },

    open: function() {
	var self = $(this)
	self.show()
	self.wizard('chooseModel', 0)
    },
    
    close: function() {
	$(this).hide()
    },

    shiftModel: function(diff) {
	var self = $(this)
	var model = self.data('model')
	var models = self.data('model_list')
	var i = models.indexOf(model)
	self.wizard('chooseModel', i+diff)
    },

    chooseModel: function(i) {
	var self = $(this)
	var list = self.data('model_list')
	var len = list.length;
	i = (i + len) % len
	var model = list[i]

	self.data('model', model)
	self.data('color', null)
	self.data('panel', null)

	var canvas, factory

	var data = self.data('model_index')[model]
	canvas = self.find('#color-options')
	canvas.html('')
	var colors = data.colors.sort()
	factory = function(color) { return function() { self.wizard('chooseColor', color) } }
	for (var j in colors)
	    $('<img>').attr('src', '/resources/pedals/'+model+'/'+colors[j]+'.png').height(64).click(factory(colors[j])).appendTo(canvas)

	canvas = self.find('#panel-options')
	canvas.html('')
	var panels = Object.keys(data.panels).sort()
	factory = function(panel) { return function() { self.wizard('choosePanel', panel) } }
	for (var j in panels)
	    $('<li>').html(panels[j].replace(/-/, ' ')).click(factory(panels[j])).appendTo(canvas)

	self.wizard('render')
    },

    chooseColor: function(color) {
	var self = $(this)
	self.data('color', color)
	self.wizard('render')
    },

    choosePanel: function(panel) {
	var self = $(this)
	self.data('panel', panel)
	self.wizard('render')
    },

    render: function() {
	var self = $(this)
	var model = self.data('model')
	var color = self.data('color')
	var panel = self.data('panel')

	var db = self.data('model_index')
	
	self.find('#model-choice h2').html(model)

	var icon = self.find('#wizard-icon')
	var width = icon.width()
	var height = icon.height()

	icon.html('')

	if (!color)
	    color = 'none'

	var element
	if (!panel) { // no template yet
	    element = $('<img>').attr('src', '/resources/pedals/'+model+'/'+color+'.png')
	} else {
	    var template = TEMPLATES['pedal-' + model + '-' + panel]
	    var effect = effects.find('option:selected').data()
	    effect.icon = {
		template: template,
		template_data: {
		    color: color,
		    controls: effect.ports.control.input.slice(0, db[model].panels[panel])
		}
	    }
	    element = $(Mustache.render(template, getTemplateData(effect)))
	}

	element.appendTo(icon)
	element.load(function() {
	    icon.width(element.width())
	    icon.height(element.height())
	})
    },

	
})
