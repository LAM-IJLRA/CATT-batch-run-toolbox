import pandas as pd
import plotly.express as px
import numpy as np

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

import ImpResSiF.signals
import ImpResSiF.filtering
from scipy.io import wavfile
import pathlib


def loadIR(row):
	filename = pathlib.Path(row["folder"]) / row["filename"]
	fs, data = wavfile.read(filename)
	ir = ImpResSiF.signals.ImpulseResponse(data, fs = fs)
	return ir



app = dash.Dash(__name__)


df = pd.read_csv("/Users/zagala/Documents/Doctorat_IRCAM_UPMC/misc/amphi55a/measures/dataframe2.csv")
print(df)

# make sure the column "frequency band", "T30", and "C80" are imported as numpy arrays (stored in csv a string with sep=',' and framed by '(', and ')')
for col in ["frequency band", "T30", "C80"]:
	df[col] = df[col].apply(lambda x : np.fromstring(x.strip('()[]'), sep=', '))



app.layout = html.Div([
    dash_table.DataTable(
        id='datatable-interactivity',
        columns=[
            {"name": i, "id": i, "deletable": False, "selectable": False} for i in df.columns
        ],
        data=df.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable="multi",
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
		}
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
	])

])


@app.callback(
		Output("tab-IR", "children"),
		Output("tab-EDC", "children"),
		Output("tab-T30", "children"),
		Output("tab-C80", "children"),
		Input("datatable-interactivity", "selected_rows"))
def update_graphs(rows):
#	if rows is None:
#		return
	print('---')
	print(rows)

	dff = df if rows is None else df.loc[rows]
	print(dff)
	
	colors = ['#7FDBFF' if i in rows else '#0074D9'
              for i in range(len(dff))]

	allIRs = []
	allEDCs = []
	for idx, row in dff.iterrows():
		currIr = loadIR(row)
		allIRs.append( {"x": currIr.sampleTimes[:4800], "y": currIr[:4800], "name" : row["filename"], "type" : "line"} )
		allEDCs.append( {"x": currIr.sampleTimes[::100], "y": currIr.energyDecayCurve[::100], "name" : row["filename"], "type" : "line"} )
#print(type(allEDCs))


	
	return ([
        dcc.Graph(
            id="receiver",
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
		id="receiver",
            figure={
                "data": allEDCs,
                "layout": {
                    "xaxis": {"automargin": True},
                    "yaxis": {
                        "automargin": True,
                        "title": {"text": "receiver"}
                    },
                    "height": 250,
                    "margin": {"t": 10, "l": 10, "r": 10},
					"height": 600
                },
            },
        )],
	[
        dcc.Graph(
            id="receiver",
            figure={
                "data": [ {"x": row["frequency band"], "y": row["T30"], "name": row["filename"]} for _, row in dff.iterrows()],
                "layout": {
                    "xaxis": {"automargin": True, "type": "log"},
                    "yaxis": {
                        "automargin": True,
                        "title": {"text": "receiver"},
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
            id="receiver",
            figure={
                "data": [ {"x": row["frequency band"], "y": row["C80"], "name": row["filename"]} for _, row in dff.iterrows()],
                "layout": {
                    "xaxis": {"automargin": True, "type": "log"},
                    "yaxis": {
                        "automargin": True,
                        "title": {"text": "receiver"},
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
