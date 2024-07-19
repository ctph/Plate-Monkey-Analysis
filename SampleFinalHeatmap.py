import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output


# Define the paths to the files
sampledis_path = '/Users/curwenpeihongtan/Desktop/pcrJob2/Final Result/Sample_dispensing.xlsx'
ctdis_path = '/Users/curwenpeihongtan/Desktop/pcrJob2/Final Result/Cts Dispensing pattern.xlsx'
'''
sampledis_path = '/home/ec2-user/Plate-Monkey-Analysis/Sample_dispensing.xlsx'
ctdis_path = '/home/ec2-user/Plate-Monkey-Analysis/Cts Dispensing pattern.xlsx'
'''
# Read the Excel files into pandas DataFrames
ctdis_data = pd.read_excel(ctdis_path)
sample_data = pd.read_excel(sampledis_path)

# Create the Dash app
app = Dash(__name__)
server = app.server

# Define color options
color_ranges = {
    "black": [0, 1],
    "blue": [2, 10],
    "cyan": [11, 15],
    "green": [16, 20],
    "red": [21, 30],
    "yellow": [31, 35],
    "pink": [36, 40]
}

app.layout = html.Div([
    html.H1("Sample Dispensing Heatmap Visualization"),
    dcc.Checklist(
        id='color-checklist',
        options=[{'label': color, 'value': color} for color in color_ranges.keys()],
        value=['black', 'blue', 'cyan', 'green', 'red', 'yellow', 'pink'],  # Default values
        inline=True
    ),
    dcc.Input(id='range-min', type='number', placeholder='Enter min value', value=0),
    dcc.Input(id='range-max', type='number', placeholder='Enter max value', value=40),
    html.Div(id='color-range-display'),
    dcc.Graph(id='heatmap-sample', style={"height": "90vh", "width": "90%"})
])

def create_custom_colorscale(color_ranges, min_val, max_val):
    colorscale = []
    for color, (start, end) in color_ranges.items():
        norm_start = (start - min_val) / (max_val - min_val)
        norm_end = (end - min_val) / (max_val - min_val)
        colorscale.append([norm_start, color])
        colorscale.append([norm_end, color])
    return colorscale

@app.callback(
    [Output('heatmap-sample', 'figure'),
     Output('color-range-display', 'children')],
    [Input('color-checklist', 'value'), Input('range-min', 'value'), Input('range-max', 'value')]
)
def update_heatmap(selected_colors, range_min, range_max):
    selected_color_ranges = {color: color_ranges[color] for color in selected_colors}
    custom_colorscale = create_custom_colorscale(selected_color_ranges, range_min, range_max)
    ctdis_data_numeric = ctdis_data.apply(pd.to_numeric, errors='coerce').fillna(-1)
    
    # Prepare hover text
    hover_text = sample_data.applymap(str)

    fig_sample = go.Figure(data=go.Heatmap(
        z=ctdis_data_numeric.values,
        x=[str(i) for i in ctdis_data.columns],
        y=[str(i) for i in ctdis_data.index],
        colorscale=custom_colorscale,
        zmin=range_min,
        zmax=range_max,
        hoverinfo='text',
        text=hover_text.values
    ))

    fig_sample.update_layout(
        title='CT Dispensing and Sample Dispensing Heatmap with Annotations',
        xaxis_title='Column Number',
        yaxis_title='Row Number'
    )

    color_range_text = html.Div([
        html.P(f"{color} range: {selected_color_ranges[color]}") for color in selected_colors
    ])

    return fig_sample, color_range_text

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True, port=2100)
