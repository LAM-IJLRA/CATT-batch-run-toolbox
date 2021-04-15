from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ObjectProperty, BoundedNumericProperty, BooleanProperty, StringProperty, OptionProperty, ColorProperty, ObjectProperty
from kivy.animation import Animation
import random
import autocatt.materials
import autocatt.projects
import pathlib

moduleFolder = pathlib.Path(autocatt.__file__)
filename = moduleFolder.parent / "materialsGUI.kv"
Builder.load_file(filename.as_posix())

class AllMatPropTabbedPanel(TabbedPanel):
	def __init__(self, prjMaterials, *args, **kwargs):
		print(f"creating materials sliders...")
		super(AllMatPropTabbedPanel, self).__init__(*args, **kwargs)
		self._prjMaterials = prjMaterials
		for mat in prjMaterials.materials:
			tmp = TabbedPanelItem()
			tmp2 = MatPropPanel(mat)
			self.add_widget(tmp)
			tmp.text = mat.name
			tmp.add_widget(tmp2)

	def switch_to(self, header):
		# fade-out - fade-in animation to highlight tab switch
		anim = Animation(opacity=0.3, d=0.05, t='in_out_quad')

		def animateOut(_anim, child, in_complete, *lt):
			_anim.start(child)

		def animateIn(*lt):
			if header.content:
				header.content.opacity = 0.3
				anim = Animation(opacity=1, d=0.4, t='in_out_quad')
				animateOut(anim, header.content, True)
			super(AllMatPropTabbedPanel, self).switch_to(header)

		anim.bind(on_complete = animateIn)
		if self.current_tab.content:
			animateOut(anim, self.current_tab.content, False)
		else:
			animateIn()
			

class ColorPickerPopup(Popup):
	colorPicker = ObjectProperty()
	color = ColorProperty((0.3, 0.4, 0.6, 1))
	ownerMat = ObjectProperty()
	def __init__(self, *args, **kwargs):
		super(ColorPickerPopup, self).__init__(*args, **kwargs)
		if self.ownerMat._material.color:
			self.color = [xx / 255 for xx in self.ownerMat._material.color]
		self.colorPicker.color = self.color 
	def matColorChanged(self):
		self.color = self.colorPicker.color
		self.ownerMat.changeMatColor()


class MatPropPanel(BoxLayout):
	materialName = StringProperty("default")
	colorPickerPopup = ObjectProperty()
	def __init__(self, material, *args, **kwargs):
		super(MatPropPanel, self).__init__(*args, **kwargs)
		self._material = material
		self.materialName = self._material.name

		if self._material.color:
			self.colorPickerPopup = ColorPickerPopup(ownerMat = self)
			self.changeMatColor()
		else:
			self.ids.but_col.text = "no color"
			self.ids.but_col.disabled = True

		absSec = FreqSections(propType = "absorption")
		self.add_widget(absSec)
		scattSec = FreqSections(propType = "scattering")
		self.add_widget(scattSec)
	
		frequencies = [125, 250, 500, 1000, 2000, 4000, 8000, 16000]	

		for idx, ff in enumerate(frequencies):
			disabled = bool(ff not in self._material.absCoeff.frequencies)
			value = 0.0 if disabled else self._material.absCoeff[ff]
			absSec.add_widget(FreqSection(frequency = ff, gray = bool(idx % 2), disabled = disabled, value = value))
			disabled = bool(ff not in self._material.scattCoeff.frequencies)
			value = 0.0 if disabled else self._material.scattCoeff[ff]
			scattSec.add_widget(FreqSection(frequency = ff, gray = bool(idx % 2), disabled = disabled, value = value))
	
	def openColorPicker(self):
		self.colorPickerPopup.open()

	def changeMatColor(self):
		color = self.colorPickerPopup.color
		self.ids.but_col.background_color = color
		rgb255 = [str(int(xx*255)) for xx in color[0:3]]
		self.ids.but_col.text = ", ".join(rgb255)
		self._material.color = rgb255

		
	def on_value_change(self, propType, frequency, value):
		if propType == "absorption":
			self._material.absCoeff[frequency] = value
		elif propType == "scattering":
			self._material.scattCoeff[frequency] = value



class FreqSections(BoxLayout):
	propType = OptionProperty("absorption", options = ["absorption", "scattering"])
	def on_value_change(self, frequency, value):
		self.parent.on_value_change(self.propType, frequency, value)



class FreqSection(BoxLayout):
	frequency = BoundedNumericProperty(1, min=0)
	value = NumericProperty()
	gray = BooleanProperty(defaultValue = False)
	def on_value_change(self, value):
		self.parent.on_value_change(frequency = self.frequency, value = value)



class MaterialsModifierApp(App):
	def build_config(self, config):
		config.setdefaults("input", {"geofilename": "/Users/zagala/Documents/Doctorat_IRCAM_UPMC/misc/CATT-batch-run-toolbox/MASTER_32.GEO"})

	def build(self):
		config = self.config
		filename = config.get("input", "geofilename")
		
#filename = "/Users/zagala/Documents/Doctorat_IRCAM_UPMC/misc/CATT-batch-run-toolbox/MASTER_32.GEO"
		filenames = autocatt.projects.getAllNestedGeoFiles(filename, keepOnlyMaterialRelevant = True)

		allMat = autocatt.materials.ProjectMaterials(filenames)

		A = AllMatPropTabbedPanel(allMat)

		return A

if __name__ == "__main__":
	MaterialsModifierApp().run()
