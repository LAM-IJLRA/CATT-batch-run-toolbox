from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, ObjectProperty, BoundedNumericProperty, BooleanProperty, StringProperty, OptionProperty, ColorProperty, ObjectProperty, ListProperty
#from kivy.animation import Animation
from kivy.uix.scrollview import ScrollView
import pathlib
import autocatt
import autocatt.projects
import autocatt.materials

#moduleFolder = pathlib.Path(autocatt.__file__)
#filename = moduleFolder.parent / "materialsGUI.kv"
#print(filename)


# load .kv file for GUI
import pkg_resources
if pkg_resources.isdir("autocatt/resources") is False:
    raise FileExistsError()
kivyFile = pkg_resources.resource_filename("autocatt", "resources/materialsGUI.kv")
Builder.load_file(kivyFile)



class GeoInstruction(ScrollView):
    pass

class AllMatPropTabbedPanel(TabbedPanel):
    def __init__(self, prjMaterials, *args, **kwargs):
        super(AllMatPropTabbedPanel, self).__init__(*args, **kwargs)
        self._prjMaterials = prjMaterials
        for mat in prjMaterials.materials.values():
            tmp = TabbedPanelItem()
            print(mat)
            tmp2 = MatPropPanel(material = mat)
            self.add_widget(tmp)
            tmp.text = mat.name
            tmp.add_widget(tmp2)


class LabeledWidget(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(LabeledWidget, self).__init__(*args, **kwargs)
    def set_disabled(self, obj, val):
        self.disabled = val

class LabeledCheckBox(LabeledWidget):
    label = StringProperty("default label")
    active = BooleanProperty(False)
    value = NumericProperty(6)
    def __init__(self, *args, active = False, value = 6, **kwargs):
        if "group" in kwargs:
            self._cb = CheckBox(group = kwargs["group"], allow_no_selection = False)
            kwargs.pop("group")
        else:
            self._cb = CheckBox()   
        super(LabeledCheckBox, self).__init__(*args, value = value, **kwargs)
        self.add_widget(self._cb, index = 1)
        self._cb.bind(active = self.set_active)
        self.set_active(None, active)
    def set_active(self, obj, val):
        self.active = val
        if obj is not self._cb:
            # value is set by something else than internal checkbox, update state of internal checkbox for appearance
            self._cb.active = val
    def on_active(self, obj, val):
        if obj is not self._cb:
            self._cb.active = val


class NbrCoeffSelector(BoxLayout):
    value = NumericProperty(6)
    title = StringProperty("default title")
    groupName = StringProperty("defaultGroupName")
    def __init__(self, *args, values = [6, 7, 8], **kwargs):
        super(NbrCoeffSelector, self).__init__(*args, **kwargs)
        self._lblcb = dict()
        for ii, nn in enumerate(values):
            tmp = LabeledCheckBox(value = nn, label = str(nn), group = self.groupName, active = ii == 0)
            tmp.bind(active = self.set_value)
            self.bind(disabled = tmp.set_disabled)
            self.add_widget(tmp)
            self._lblcb[nn] = tmp

    def set_disabled(self, obj, val):
        self.disabled = val
        for cc in self.children:
            cc.disabled = val
    def set_value(self, obj, val):
        if val:
            self.value = obj.value
    def on_value(self, obj, val):
        self._lblcb[val].set_active(self, True)
    def setValue(self, val):
        self.value = val

        




class PropScattRoughness(LabeledWidget):
    value = BoundedNumericProperty(0.5, min = 0.0)
    def __init__(self, *args, **kwargs):
        super(PropScattRoughness, self).__init__(*args, **kwargs)
    def set_value(self, obj, val):
        self.value = float(val)
        if obj is not self.ids.textInput:
            self.ids.textInput.text = str(val)
        
class PropNbrAbsTransp(NbrCoeffSelector):
    def __init__(self, *args, title = "nbr transp./abs.", **kwargs):
        super(PropNbrAbsTransp, self).__init__(*args, title = title, **kwargs)

class PropNbrScatt(NbrCoeffSelector):
    def __init__(self, *args, title = "nbr scatt.", **kwargs):
        super(PropNbrScatt, self).__init__(*args, title = title, **kwargs)
    def set_disabled(self, obj, val):
        self.disabled = val


class PropColor(LabeledWidget):
    colorPickerPopup = ObjectProperty()
    color = ColorProperty()
    colorDefined = BooleanProperty()
    def __init__(self, *args, **kwargs):
        super(PropColor, self).__init__(*args, **kwargs)
        self.colorPickerPopup = ColorPickerPopup()
        self.colorPickerPopup.bind(color = self.set_color)
    def on_press(self, obj, val):
        self.colorPickerPopup.open()
    def set_color(self, obj, val):
        self.color = val
    def on_color(self, obj, val):
        self.colorPickerPopup.color = val
        self.ids.button.background_color = val
        self.ids.button.color = [1.0 - vv for vv in val[:3]] + [1.0]
    def set_colorDefined(self, obj, val):
        self.colorDefined = val
    def on_colorDefined(self, obj, val):
        if obj is not self.ids.checkbox:
            self.ids.checkbox.active = val


class ColorPickerPopup(Popup):
    colorPicker = ObjectProperty()
    color = ColorProperty((0.3, 0.4, 0.6, 1))
    def __init__(self, *args, **kwargs):
        super(ColorPickerPopup, self).__init__(*args, **kwargs)
        self.colorPicker.color = self.color 
    def matColorChanged(self):
        self.color = self.colorPicker.color
    def on_color(self, obj, val):
        if obj is not self.colorPicker:
            self.colorPicker.color = val


class FreqSlider(BoxLayout):
    # values are stores between 0 and 1
    floatFormat = BooleanProperty(False)
    frequency = BoundedNumericProperty(125, min = 0)
    value = BoundedNumericProperty(0.0, min = 0, max = 1.0)
    index = BoundedNumericProperty(0, min = 0)
    def __init__(self, *args, **kwargs):
        super(FreqSlider, self).__init__(*args, **kwargs)
    def set_value(self, obj, val):
        self.value = val
        if obj is not self.ids.slider:
            self.ids.slider.value = val
    def set_disabled(self, obj, val):
        # here, val is a threshold to be compared with index
        self.disabled = self.index >= val
    def set_floatFormat(self, obj, val):
        self.floatFormat = val
    def on_value(self, obj, val):
        if obj is not self.ids.slider:
            self.ids.slider.value = val


class FreqSliderSection(BoxLayout):
    floatFormat = BooleanProperty(False)
    coeffType = StringProperty("absorption")
    nbrCoeff = BoundedNumericProperty(6, min = 0)
    normedValues = ListProperty()
    frequencies = [125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    def __init__(self, *args, **kwargs):
        super(FreqSliderSection, self).__init__(*args, **kwargs)
        tmp = BoxLayout(size_hint_y = 0.9, orientation = "horizontal")
        self.add_widget(tmp)
        self._sliders = dict()
        for ii, ff in enumerate(FreqSliderSection.frequencies):
            tmp_freqSlid = FreqSlider(frequency = ff, index = ii)
            tmp.add_widget(tmp_freqSlid)
            self.bind(nbrCoeff = tmp_freqSlid.set_disabled)
            tmp_freqSlid.set_disabled(self, self.nbrCoeff)
            self.bind(disabled = lambda obj, val : tmp_freqSlid.set_disabled(obj, 0 if val or self.disabled else self.nbrCoeff))
            self.bind(floatFormat = tmp_freqSlid.set_floatFormat)
            self._sliders[ff] = tmp_freqSlid
            self._sliders[ff].bind(value = lambda obj, val : self.update_values())
        self.update_values()
    def set_nbrCoeff(self, obj, val):
        self.nbrCoeff = val
    def set_disabled(self, obj, val):
        self.disabled = val
    def set_floatFormat(self, obj, val):
        self.floatFormat = val
    def set_values(self, obj, val):
        # this accepts array-like val
        if obj not in self._sliders.values():
            for ff, nn in zip(FreqSliderSection.frequencies, val):
                self._sliders[ff].value = nn
        self.update_values()
    def update_values(self):
        self.normedValues = [self._sliders[ff].value for ff in FreqSliderSection.frequencies]
        
            
        



class MatMetaParameters(BoxLayout):
    materialName = StringProperty("default")

    floatFormat = BooleanProperty(False)
    transpDefined = BooleanProperty(False)
    scattDefined = BooleanProperty(False)
    estimateScatt = BooleanProperty(False)
    nbrAbsTransp = NumericProperty(6)
    nbrScatt = NumericProperty(6)
    roughness = NumericProperty(0.0)

    colorDefined = BooleanProperty(False)
    color = ColorProperty()

    def __init__(self, *args, **kwargs):
        super(MatMetaParameters, self).__init__(*args, **kwargs)

        self._cb_floatFormat = LabeledCheckBox(label = "use float format")
        self.add_widget(self._cb_floatFormat)
        self._cb_floatFormat.bind(active = self.set_floatFormat)

        self._rb_nbrAbsTransp = PropNbrAbsTransp(groupName = self.materialName + "_grpAbsTransp")
        self.add_widget(self._rb_nbrAbsTransp)
        self._rb_nbrAbsTransp.bind(value = self.set_nbrAbsTransp)

        self._cb_defineTransp = LabeledCheckBox(label = "define transp.")
        self.add_widget(self._cb_defineTransp)
        self._cb_defineTransp.bind(active = self.set_transpDefined)
        
        self._cb_defineScatt = LabeledCheckBox(label = "define scatt.")
        self.add_widget(self._cb_defineScatt)
        self._cb_defineScatt.bind(active = self.set_scattDefined)

        self._cb_estimateScatt = LabeledCheckBox(label = "estimate scatt.")
        self.add_widget(self._cb_estimateScatt)
        self._cb_estimateScatt.bind(active = self.set_estimateScatt)

        self._ti_roughness = PropScattRoughness()
        self.add_widget(self._ti_roughness)
        self._ti_roughness.bind(value = self.set_roughness)
        
        self._rb_nbrScatt = PropNbrScatt(groupName = self.materialName + "_grpScatt")
        self.add_widget(self._rb_nbrScatt)
        self._rb_nbrScatt.bind(value = self.set_nbrScatt)


        self._pu_color = PropColor()
        self.add_widget(self._pu_color)
        self._pu_color.bind(color = self.set_color)
        self._pu_color.bind(colorDefined = self.set_colorDefined)


        # rules for disabling "estimateScatt"
        self._cb_defineScatt.bind(active = lambda obj, val : self._cb_estimateScatt.set_disabled(obj, not val))
        self._cb_estimateScatt.set_disabled(None, not self._cb_defineScatt.active)
        
        # rules for disabling "nbrScatt"
        rule_disabilityNbrScatt = lambda : self._cb_estimateScatt.disabled or self._cb_estimateScatt.active
        self._cb_estimateScatt.bind(disabled = lambda obj, val : self._rb_nbrScatt.set_disabled(obj, rule_disabilityNbrScatt()))
        self._cb_estimateScatt.bind(active = lambda obj, val : self._rb_nbrScatt.set_disabled(obj, rule_disabilityNbrScatt()))
        self._rb_nbrScatt.set_disabled(None, rule_disabilityNbrScatt())

        # rules for disabling "roughness"
        rule_disabilityRoughness = lambda : not(not self._cb_estimateScatt.disabled and self._cb_estimateScatt.active)
        self._cb_estimateScatt.bind(disabled = lambda obj, val : self._ti_roughness.set_disabled(obj, rule_disabilityRoughness()))
        self._cb_estimateScatt.bind(active = lambda obj, val : self._ti_roughness.set_disabled(obj, rule_disabilityRoughness()))
        self._ti_roughness.set_disabled(None, rule_disabilityRoughness())


    def set_floatFormat(self, obj, val):
        self.floatFormat = val
    def set_transpDefined(self, obj, val):
        self.transpDefined = val
    def set_scattDefined(self, obj, val):
        self.scattDefined = val
    def set_estimateScatt(self, obj, val):
        self.estimateScatt = val
    def set_roughness(self, obj, val):
        self.roughness = val
    def set_nbrAbsTransp(self, obj, val):
        self.nbrAbsTransp = val
    def set_nbrScatt(self, obj, val):
        self.nbrScatt = val
    def set_color(self, obj, val):
        self.color = val
    def set_colorDefined(self, obj, val):
        self.colorDefined = val

    def on_floatFormat(self, obj, val):
        if obj is not self._cb_floatFormat: 
            self._cb_floatFormat.active = val
        
    def on_transpDefined(self, obj, val):
        if obj is not self._cb_defineTransp:    
            self._cb_defineTransp.active = val

    def on_scattDefined(self, obj, val):
        if obj is not self._cb_defineScatt: 
            self._cb_defineScatt.active = val

    def on_estimateScatt(self, obj, val):
        if obj is not self._cb_estimateScatt:   
            self._cb_estimateScatt.active = val

    def on_roughness(self, obj, val):
        if obj is not self._ti_roughness:   
            self._ti_roughness.set_value(obj, val)

    def on_nbrAbsTransp(self, obj, val):
        if obj is not self._rb_nbrAbsTransp:
            self._rb_nbrAbsTransp.value = val

    def on_nbrScatt(self, obj, val):
        if obj is not self._rb_nbrScatt:
            self._rb_nbrScatt.value = val

    def on_color(self, obj, val):
        if obj is not self._pu_color:
            self._pu_color.color = val

    def on_colorDefined(self, obj, val):
        self._pu_color.colorDefined = val




class MatPropPanel(BoxLayout):
    material = ObjectProperty()
    materialName = StringProperty("default")
    colorPickerPopup = ObjectProperty()
    def __init__(self, *args, **kwargs):
        super(MatPropPanel, self).__init__(*args, **kwargs)

        self.materialName = self.material.name

        A = MatMetaParameters(size_hint_x = 0.3, materialName = self.materialName)
        self._matParamBanner = A
        self.add_widget(self._matParamBanner)

        tmp = BoxLayout(orientation = "vertical")

        self.add_widget(tmp)

        tmp_freqSliderSection = FreqSliderSection(nbrCoeff = A.nbrAbsTransp)
        A.bind(nbrAbsTransp = tmp_freqSliderSection.set_nbrCoeff)
        A.bind(floatFormat = lambda obj, val : tmp_freqSliderSection.set_floatFormat(obj, val))
        tmp.add_widget(tmp_freqSliderSection)
        tmp_freqSliderSection.bind(normedValues = self.set_absCoeffs)

        tmp_freqSliderSection2 = FreqSliderSection(coeffType = "transparency", nbrCoeff = A.nbrAbsTransp)
        A.bind(nbrAbsTransp = tmp_freqSliderSection2.set_nbrCoeff)
        A.bind(transpDefined = lambda obj, val : tmp_freqSliderSection2.set_disabled(obj, not val))
        A.bind(floatFormat = lambda obj, val : tmp_freqSliderSection2.set_floatFormat(obj, val))
        tmp.add_widget(tmp_freqSliderSection2)
        tmp_freqSliderSection2.bind(normedValues = self.set_transpCoeffs)


        tmp_freqSliderSection3 = FreqSliderSection(coeffType = "scattering", nbrCoeff = A.nbrScatt)
        funDisabilityScattSliders = lambda obj, val : tmp_freqSliderSection3.set_disabled(obj, not (A.scattDefined and not A.estimateScatt))
        A.bind(nbrScatt = tmp_freqSliderSection3.set_nbrCoeff)
        A.bind(scattDefined = funDisabilityScattSliders)
        A.bind(estimateScatt = funDisabilityScattSliders)
        A.bind(floatFormat = lambda obj, val : tmp_freqSliderSection3.set_floatFormat(obj, val))
        tmp.add_widget(tmp_freqSliderSection3)
        tmp_freqSliderSection3.bind(normedValues = self.set_scattCoeffs)

        self._geoInstruction = GeoInstruction(scroll_x = 0.5)
        tmp.add_widget(self._geoInstruction)


        
        tmp_freqSliderSection.set_floatFormat(self, A.floatFormat)
        tmp_freqSliderSection2.set_floatFormat(self, A.floatFormat)
        tmp_freqSliderSection2.set_nbrCoeff(self, A.nbrAbsTransp)
        tmp_freqSliderSection2.set_disabled(self, not A.transpDefined)
        funDisabilityScattSliders(self, None)
        tmp_freqSliderSection3.set_floatFormat(self, A.floatFormat)


        # initialize GUI based on materials current parameters
        A.floatFormat = self.material.floatFormat
        A.transpDefined = self.material.transpDefined
        A.scattDefined = self.material.scattDefined
        A.nbrAbsTransp = self.material.nbrAbsTranspCoeffs
        A.nbrScatt = self.material.nbrScattCoeffs
        A.estimateScatt = self.material.estimateScatt
        A.roughness = self.material.scattRoughness
        A.color = [cc / 255 for cc in self.material.color]
        A.colorDefined = self.material.colorDefined

        absCoeff = self.material.absCoeff.getArray()
        transpCoeff = self.material.transpCoeff.getArray()
        scattCoeff = self.material.scattCoeff.getArray()
        tmp_freqSliderSection.set_values(self, absCoeff)
        tmp_freqSliderSection2.set_values(self, transpCoeff)
        tmp_freqSliderSection3.set_values(self, scattCoeff)

        self.update_instructionLine()

        A.bind(floatFormat = self.set_floatFormat)
        A.bind(transpDefined = self.set_transpDefined)
        A.bind(scattDefined = self.set_scattDefined)
        A.bind(nbrAbsTransp = self.set_nbrAbsTransp)
        A.bind(nbrScatt = self.set_nbrScatt)
        A.bind(estimateScatt = self.set_estimateScatt)
        A.bind(roughness = self.set_roughness)
        A.bind(color = self.set_color)
        A.bind(colorDefined = self.set_colorDefined)

    def set_floatFormat(self, obj, val):
        self.material.floatFormat = val
        self.update_instructionLine()
    def set_transpDefined(self, obj, val):
        self.material.transpDefined = val
        self.update_instructionLine()
    def set_scattDefined(self, obj, val):
        self.material.scattDefined = val
        self.update_instructionLine()
    def set_nbrAbsTransp(self, obj, val):
        self.material.nbrAbsTranspCoeffs = val
        self.update_instructionLine()
    def set_nbrScatt(self, obj, val):
        self.material.nbrScattCoeffs = val
        self.update_instructionLine()
    def set_estimateScatt(self, obj, val):
        self.material.estimateScatt = val
        self.update_instructionLine()
    def set_roughness(self, obj, val):
        self.material.scattRoughness = val
        self.update_instructionLine()
    def set_color(self, obj, val):
        self.material.color = [vv * 255 for vv in val[:3]]
        self.update_instructionLine()
    def set_colorDefined(self, obj, val):
        self.material.colorDefined = val
        self.update_instructionLine()

    def set_absCoeffs(self, obj, val):
        self.material.absCoeff.setFromArray(val)
    def set_transpCoeffs(self, obj, val):
        self.material.transpCoeff.setFromArray(val)
    def set_scattCoeffs(self, obj, val):
        self.material.scattCoeff.setFromArray(val)

    def update_instructionLine(self):
        self._geoInstruction.ids.label.text = self.material.createLine()





class MaterialModifierApp(App):
    def build_config(self, config):
        config.setdefaults("input", {"geofilename": "/Users/zagala/Documents/Doctorat_IRCAM_UPMC/misc/CATT-batch-run-toolbox/autocatt/testFileInput/text1.GEO"})

    def build(self):
#filename = "/Users/zagala/Documents/Doctorat_IRCAM_UPMC/misc/CATT-batch-run-toolbox/autocatt/testFileInput/text1.GEO" 
#       filenames = autocatt.projects.getAllNestedGeoFiles(filename)

        print("testA")
        config = self.config
        filename = config.get("input", "geofilename")
        print("testB")

        allMats = autocatt.materials.ProjectMaterialsWrapper(filename)
        B = AllMatPropTabbedPanel(allMats)

        return B
#return MatPropPanel(materialName = "testMaterial")


#if __name__ == "__main__":
#   A = MaterialModifierApp().run() 
