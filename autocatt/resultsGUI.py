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
			"Drag and Drop or ", html.A("Select Files")
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
		Input("datatable-upload", "contents"),
		State("datatable-upload", "filename"))
def update_output(contents, filename):
	if contents is None:
		return [{}], [], None
	df = parse_contents(contents, filename)
	for col in ["frequency band", "T30", "C80"]:
		df[col] = df[col].apply(lambda x : np.fromstring(x.strip('()[]'), sep=', '))
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
	for idx, row in dff.iterrows():
		currIr = loadIR(row)
		allIRs.append( {"x": currIr.sampleTimes[:4800*2], "y": currIr[:4800*2], "name" : row["filename"], "type" : "line"} )
		allEDCs.append( {"x": currIr.sampleTimes[::100], "y": currIr.energyDecayCurve[::100], "name" : row["filename"], "type" : "line"} )


	
	return ([
        dcc.Graph(
            id="graph-IR",
            figure={
                "data": allIRs,
                "layout": {
                    "xaxis": {"automargin": True},
                    "yaxis": {
                        "automargin": True,
                        "title": {"text": "Impulse response (first reflexions)"}
                    },
                    "height": 250,
                    "margin": {"t": 10, "l": 10, "r": 10},
					"height": 600
                },
            },
        )], 
	[ dcc.Graph(
		id="graph-EDC",
            figure={
                "data": allEDCs,
                "layout": {
                    "xaxis": {"automargin": True},
                    "yaxis": {
                        "automargin": True,
                        "title": {"text": "EDC, in dB"}
                    },
                    "height": 250,
                    "margin": {"t": 10, "l": 10, "r": 10},
					"height": 600
                },
            },
        )],
	[
        dcc.Graph(
            id="graph-T30",
            figure={
                "data": [ {"x": row["frequency band"], "y": row["T30"], "name": row["filename"]} for _, row in dff.iterrows()],
                "layout": {
                    "xaxis": {"automargin": True, "type": "log"},
                    "yaxis": {
                        "automargin": True,
                        "title": {"text": "T30, in s"},
						"min": 0.0
                    },
                    "height": 250,
                    "margin": {"t": 10, "l": 10, "r": 10},
					"height": 600
                },
            },
        )
    ],
	[
        dcc.Graph(
            id="graphC80",
            figure={
                "data": [ {"x": row["frequency band"], "y": row["C80"], "name": row["filename"]} for _, row in dff.iterrows()],
                "layout": {
                    "xaxis": {"automargin": True, "type": "log"},
                    "yaxis": {
                        "automargin": True,
                        "title": {"text": "C80, in dB"},
						"min": 0.0
                    },
                    "height": 250,
                    "margin": {"t": 10, "l": 10, "r": 10},
					"height": 600
                },
            },
        )
    ])





if __name__ == '__main__':
    app.run_server(debug=True)
