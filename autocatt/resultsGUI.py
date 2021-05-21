import pandas as pd
import plotly.express as px
import numpy as np
import io
import base64
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

import ImpResSiF.signals
import ImpResSiF.filtering
from scipy.io import wavfile
import pathlib

def loadIR(row):
	filename = pathlib.Path(row["folder"]) / row["filename"]
	fs, data = wavfile.read(filename)
	ir = ImpResSiF.signals.ImpulseResponse(data, fs = fs)
	return ir



app = dash.Dash(__name__, external_stylesheets = external_stylesheets)


#df = pd.read_csv("/Users/zagala/Documents/Doctorat_IRCAM_UPMC/misc/amphi55a/measures/dataframe2.csv")
df = pd.DataFrame()


app.layout = html.Div([
	dcc.Upload(
		id="datatable-upload",
		children = html.Div([
			"Drag and Drop IR database or ", html.A("Select Files")
		]),
		style = {"width": "100%", "height": "60px", "lineHeight": "60px",
			"borderWidth": "1px", "borderStyle": "dashed",
            "borderRadius": "5px", "textAlign": "center", "margin": "15px"
		},
	),
    dash_table.DataTable(
        id='datatable-interactivity',
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current= 0,
        page_size= 10,
		hidden_columns = ["frequency band", "T30", "C80"],
		style_cell = {"overflow": "hidden",
			"textOverflow": "ellipsis",
			"maxWidth": 0,
		},
		style_table={'height': '350px'},
		css = [{"selector": ".show-hide", "rule": "display: none"}] # hide "toggle columns" button
    ),
    html.Div(id='datatable-interactivity-container'),
	html.Div([
    	dcc.Tabs(id="tabs", value='tab-IR', children=[
        	dcc.Tab(id="tab-IR", label='IR', value='tab-IR'),
        	dcc.Tab(id="tab-EDC", label='EDC', value='tab-EDC'),
        	dcc.Tab(id="tab-T30", label='T30', value='tab-T30'),
        	dcc.Tab(id="tab-C80", label='C80', value='tab-C80'),
    	]),
    	html.Div(id='tabs-content')
	]),
],
)


def parse_contents(contents, filename):
	content_type, content_string = contents.split(',')
	decoded = base64.b64decode(content_string)
	if '.csv' in filename:
		# Assume that the user uploaded a CSV file
		return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
	else: 
		raise ValueError("file must be csv")

@app.callback(Output("datatable-interactivity", "data"),
		Output("datatable-interactivity", "columns"),
		Output("datatable-interactivity", "row_selectable"),
		Input("datatable-interactivity", "data"),## test
		Input("datatable-upload", "contents"),
		State("datatable-upload", "filename"))
def update_output(prevContents, contents, filename):
	if contents is None:
		return [{}], [], None
	df = parse_contents(contents, filename)
	for col in ["frequency band", "T30", "C80"]:
		df[col] = df[col].apply(lambda x : np.fromstring(x.strip('()[]'), sep=', '))
	print("\n\n")
	print(f"{prevContents=}")
	print(f"{df.to_dict('records')=}")
	if prevContents[0]:
		print("extending previous dataframe") 
		prevContents.extend(df.to_dict("records"))
		return prevContents, [{"name": col, "id": col, "deletable": False, "selectable": False} for col in df.columns], "multi"
	print("brand new dataframe")
	return df.to_dict("records"), [{"name": col, "id": col, "deletable": False, "selectable": False} for col in df.columns], "multi"


@app.callback(
		Output("tab-IR", "children"),
		Output("tab-EDC", "children"),
		Output("tab-T30", "children"),
		Output("tab-C80", "children"),
		Input("datatable-interactivity", "data"),
		Input("datatable-interactivity", "selected_rows"))
def update_graphs(tableContent, rows):
#	if rows is None:
#		return

	dff = pd.DataFrame(tableContent).loc[rows]
	
	colors = ['#7FDBFF' if i in rows else '#0074D9'
              for i in range(len(dff))]

	allIRs = []
	allEDCs = []
	df_IR = []
	df_onset = []
	df_EDC = []
	df_freqParam = []
	for idx, row in dff.iterrows():
		currIr = loadIR(row)
		idxMax = np.argmax(currIr.sampleTimes > 0.1) # 100ms (arbitrary)
		allIRs.append( {"x": currIr.sampleTimes[:idxMax], "y": currIr[:idxMax], "name" : row["filename"], "type" : "line"} )
		allEDCs.append( {"x": currIr.sampleTimes[::100], "y": currIr.energyDecayCurve[::100], "name" : row["filename"], "type" : "line"} )

		df_IR.append(pd.DataFrame({"time": currIr.sampleTimes[:idxMax], 
					"amplitude": currIr[:idxMax] / np.linalg.norm(currIr), 
					"filename": row["filename"], 
					"onsetTime": currIr.onsetTime,
					"source": row["source"],
					"receiver": row["receiver"],
					"origin": row["origin"],
					"processing": row["processing"],
					"src-rec, origin, processing": " - ".join([str(row["source"]), str(row["receiver"])]) + ", " + row["origin"] + ", " + str(row["processing"])}))
		df_onset.append(pd.DataFrame({"onsetTime": currIr.onsetTime, "name": row["filename"], "index": [0]}))
		df_EDC.append(pd.DataFrame({"time": currIr.sampleTimes[::100], 
					"edc": currIr.energyDecayCurve[::100], 
					"filename": row["filename"], 
					"onsetTime": currIr.onsetTime,
					"processing": row["processing"],
					"src-rec, origin, processing": " - ".join([str(row["source"]), str(row["receiver"])]) + ", " + row["origin"] + ", " + str(row["processing"])}))
		
		df_freqParam.append(pd.DataFrame({"frequency band": row["frequency band"], 
					"T30": row["T30"], 
					"C80": row["C80"], 
					"filename": row["filename"], 
					"source": row["source"],
					"receiver": row["receiver"], 
					"processing":row["processing"],
					"src-rec, origin, processing": ' - '.join([str(row["source"]), str(row["receiver"])]) + ", " + row["origin"] + ", " + str(row["processing"])
					}))

	if df_IR:
		df_IR = pd.concat(df_IR)
		df_IR["processing"].fillna(value = "", inplace = True)
		df_onset = pd.concat(df_onset)
		fig_irs = px.line(df_IR, x="time", y="amplitude", 
				line_group = "filename", 
				color = "src-rec, origin, processing",
				hover_name = "filename",
				hover_data = {"filename": False, 
							"src-rec, origin, processing": False, 
							"time": ":.3f",
							"amplitude": ":.3f",
							"source": True,
							"receiver": True,
						   	"origin": True,
							"processing": True	},
				labels = {"time": "time, in s"},
				render_mode = "svg") 
		for _, row2 in df_onset.iterrows():
			fig_irs.add_vline(x=row2["onsetTime"],
					line_dash = "dot",
					line_color = "#AAA",
					annotation_text = "onset " + row2["name"],
					annotation_textangle = -90.0,
					annotation_font = {"color": "#AAA"},
					annotation_position = "top left")
	else:
		fig_irs = px.line(x=None, y=None, labels = dict(x="time, in s", y="amplitude")) 


	if df_EDC:
		df_EDC = pd.concat(df_EDC)
		df_EDC["processing"].fillna(value = "", inplace = True)
		fig_edc = px.line(df_EDC, x="time", y="edc", 
				line_group="filename", 
				color="src-rec, origin, processing", 
				labels = {"time": "time, in s", "edc": "EDC, in dB"},
				render_mode = "svg")
	else:
		fig_edc = px.line(x=None, y=None, 
				labels = dict(x="time, in s", y="EDC, in dB")) 
	

	if df_freqParam:
		df_freqParam = pd.concat(df_freqParam)
		df_freqParam["processing"].fillna(value = "", inplace = True)
		fig_T30 = px.line(df_freqParam, x="frequency band", y="T30", 
				line_group = "filename", 
				log_x = True, 
				range_x=[50.,20000.], 
				color = "src-rec, origin, processing", 
				labels = {"frequency band": "frequency band, in Hz",
					"T30":"T30, in s"},
				render_mode = "svg")
		fig_C80 = px.line(df_freqParam, x="frequency band", y="C80", 
				line_group = "filename", 
				log_x = True, 
				range_x=[50.,20000.], 
				color = "src-rec, origin, processing",
				labels = {"frequency band": "frequency band, in Hz",
					"C80": "C80, in dB"},
				render_mode = "svg")
	else:
		fig_T30 = px.line(x = None, y = None, log_x=True)
		fig_C80 = px.line(x = None, y = None, log_x=True)



	return (dcc.Graph(id = "graph-IR", figure = fig_irs),
			dcc.Graph(id = "graph-EDC", figure = fig_edc),
			dcc.Graph(id = "graph-T30", figure = fig_T30),
			dcc.Graph(id = "graph-C80", figure = fig_C80),)
#	[
#        dcc.Graph(
#            id="graphC80",
#            figure={
#                "data": [ {"x": row["frequency band"], "y": row["C80"], "name": row["filename"]} for _, row in dff.iterrows()],
#                "layout": {
#                    "xaxis": {"automargin": True, "type": "log",
#						"title": "frequency, in Hz"
#					},
#                    "yaxis": {
#                        "automargin": True,
#                        "title": {"text": "C80, in dB"},
#						"min": 0.0
#                    },
#                    "height": 250,
#                    "margin": {"t": 10, "l": 10, "r": 10},
#					"height": 600
#                },
#            },
#        )
#    ])





if __name__ == '__main__':
    app.run_server(debug=True)
