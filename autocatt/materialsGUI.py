import autocatt.materials
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle


class FreqBandSlider(GridLayout):
	def __init__(self, freq, parent = None):
		super().__init__()

		self.rows = 3
		self._freq = freq
		self._parent = parent
		
		self.slider = Slider(orientation="vertical",
				min=0, max=100, step=1,
				value_track_color = [1, 0, 1, 0.5])
		self.add_widget(self.slider)
		self.slider.bind(value = self.on_value_change)

		self.valLabel = Label(size_hint_y=0.1);
		self.add_widget(self.valLabel)

		self.label = Label(text=str(freq) + " Hz",
				size_hint_y = 0.1)
		self.add_widget(self.label)

		# update
		self.valLabel.text = str(self.slider.value)

	def on_value_change(self, instance, value):
		self.valLabel.text = str(value)
		if self._parent is not None:
			self.parent.on_value_change(self, (self._freq, self.slider.value))


class CoeffSliders(GridLayout):
	def __init__(self, freqs, material = None, type = "abs"):
		super().__init__()
		self.cols = len(freqs)
		self._material = material
		self._type = type

		if type == "abs":
			freqs = self._material.absCoeff.frequencies()
		elif type == "scatt":
			freqs = self._material.scattCoeff.frequencies()
		
		self._allSliders = {freq: FreqBandSlider(freq, parent=self) for freq in freqs}
		for ss in self._allSliders.values():
			self.add_widget(ss)

		self.updateSliderValues()

	def on_value_change(self, instance, value):
		if self._type == "abs":
			self._material.absCoeff[value[0]] = value[1]
		elif self._type == "scatt":
			self._material.scattCoeff[value[0]] = value[1]
		else:
			raise ValueError(f"Invalid type '{self._type}' of coefficient to modify")

	def updateSliderValues(self):
		if self._type == "abs":
			vals = self._material._absCoeff.values()
		elif self._type == "scatt":
			vals = self._material._scattCoeff.values()
		else:
			raise ValueError(f"Invalid type '{self._type}' of coefficient to modify")
		for ss, val in zip(self._allSliders.values(), vals):
			ss.slider.value = val


class MyScreenManager(ScreenManager):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		from kivy.core.window import Window
		Window.bind(on_key_down=self._keydown)
	def _keydown(self, *args):
		tmp = self.current.split(' ')
		currentMatName = tmp[0]
		if len(tmp) > 1:
			currentType = tmp[1]
		else:
			currentType = ""

		if args[2] in (79, 80, 81, 82):
			if args[2] == 79: 
				# right
				self.transition.direction = "left"
				nextMatName = self.current_screen.next	
				nextTypeName = currentType
			elif args[2] == 80:
				# left
				self.transition.direction = "right"
				nextMatName = self.current_screen.prev#"settings"
				nextTypeName = currentType
			elif args[2] == 81:
				# down
				self.transition.direction = "up"
				nextMatName = currentMatName
				nextTypeName = "scatt"
			elif args[2] == 82:
				# up
				self.transition.direction = "down"
				nextMatName = currentMatName
				nextTypeName = "abs"

			try:
				# is lateral move, and neighbour material does not have scatt coefficients, then move to same neighbour material but for abs coeffs
				self.current = nextMatName + " " + nextTypeName
			except:
				self.current = nextMatName + " abs"



class CoeffScreen(Screen):
	def __init__(self, material, prev = None, next = None, type = "abs", color = (0, 0, 0, 1), **kwargs):
		super().__init__(**kwargs)
		self._material = material
		self._type = type
		self.prev = prev
		self.next = next
		self._layout = GridLayout(rows = 2)
		title = ' - '.join(self.name.split(' '))
		self._layout.add_widget(Label(text=title, size_hint_y = 0.1, font_size='30sp', bold=True))
		self._layout.add_widget(
				CoeffSliders((125, 250, 500, 1000, 2000, 4000, 8000, 16000), 
					material = self._material,
					type = self._type))
		
		self._layout.bind(size=self._updateBackgroundPosition, pos=self._updateBackgroundPosition)
		with self._layout.canvas.before:
			Color(*color)
			self.rectangle = Rectangle(pos=self._layout.pos, size=self._layout.size)

		self.add_widget(self._layout)

	def _updateBackgroundPosition(self, instance, value):
		self.rectangle.pos = instance.pos
		self.rectangle.size = instance.size


def reset():
	# reset kiwy to be able to re-launch App after closing it while stating in the same session
	import kivy.core.window as window
	from kivy.base import EventLoop
	if not EventLoop.event_listeners:
		from kivy.cache import Cache
		window.Window = window.core_select_lib('window', window.window_impl, True)
		Cache.print_usage()
		for cat in Cache._categories:
			Cache._objects[cat] = {}



class MaterialsApp(App):
	def build_config(self, config):
		config.setdefaults("input", {"geofilenames": "autocatt/testMat2.txt, testMATERIAUX.geo"})

	def build(self):
		config = self.config
		reset()
		self._frequencies = (125, 250, 500, 1000, 2000, 4000, 8000, 16000)
		
		filenames = config.get("input", "geofilenames").split(',')
		filenames = [x.strip() for x in filenames]

		self._materialNames, scattCoeffsDefined = autocatt.materials.getAllMaterialsFromFiles(filenames)
		print(self._materialNames)

		self._screenManager = MyScreenManager()

		self._allMaterials = []

		for idx, (mat, scattDef) in enumerate(zip(self._materialNames, scattCoeffsDefined)):

			currMaterial = autocatt.materials.Material(mat, filenames = filenames)
			self._allMaterials.append(currMaterial)
			
			if idx == 0:
				prev = mat
			else:
				prev = self._materialNames[idx - 1]

			if idx == len(self._materialNames) - 1:
				next = mat
			else:
			 	next = self._materialNames[idx + 1]

			name = mat + " abs"
			self._screenManager.add_widget(CoeffScreen(currMaterial, name=name, type="abs", prev=prev, next=next))

			tmpStrInfo = "abs"

			if scattDef == True:
				name = mat + " scatt"
				color = (0.2, 0.0, 0.3, 1)
				self._screenManager.add_widget(CoeffScreen(currMaterial, name=name, type="scatt", prev=prev, next=next, color=color))		
				tmpStrInfo += " + scatt"

			print(f"constructing screen for material {mat : >20}       [{tmpStrInfo : <12}]")
		return self._screenManager

	def stop(self, *largs):
		self.root_window.close()
		return super(MaterialsApp, self).stop(*largs)



