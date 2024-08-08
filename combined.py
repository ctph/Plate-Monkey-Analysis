import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Define the paths to the files
assaydis_path = 'Assay_dispensing.xlsx'
sampledis_path = 'Sample_dispensing.xlsx'
ctdis_path = 'Cts Dispensing pattern.xlsx'

# Read the Excel files into pandas DataFrames
ctdis_data = pd.read_excel(ctdis_path)
assay_data = pd.read_excel(assaydis_path)
sample_data = pd.read_excel(sampledis_path)

# Ensure the ct data is numeric
ctdis_data = ctdis_data.apply(pd.to_numeric, errors='coerce').fillna(-1)

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

color_subtractions = {
    "black": 2,
    "blue": 9,
    "cyan": 5,
    "green": 5,
    "red": 10,
    "yellow": 5,
    "pink": 5
}

app.layout = html.Div([
    html.H1("Combined Heatmap Visualization"),
    dcc.Checklist(
        id='color-checklist',
        options=[{'label': color, 'value': color} for color in color_ranges.keys()],
        value=['black', 'blue', 'cyan', 'green', 'red', 'yellow', 'pink'],  # Default values
        inline=True
    ),
    dcc.Input(id='range-min', type='number', placeholder='Enter min value', value=0),
    dcc.Input(id='range-max', type='number', placeholder='Enter max value', value=40),
    html.Div(id='color-range-display'),
    dcc.Graph(id='heatmap-combined', style={"height": "60vh", "width": "90%"}),
    dcc.Graph(id='bar-chart', style={"height": "40vh", "width": "90%"})
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
    [Output('heatmap-combined', 'figure'),
     Output('color-range-display', 'children'),
     Output('bar-chart', 'figure')],
    [Input('color-checklist', 'value'), Input('range-min', 'value'), Input('range-max', 'value')]
)
def update_heatmap(selected_colors, range_min, range_max):
    selected_color_ranges = {color: color_ranges[color] for color in selected_colors}
    custom_colorscale = create_custom_colorscale(selected_color_ranges, range_min, range_max)
    
    # The data for the heatmap is based on ctdis_data, which is numeric
    ctdis_data_numeric = ctdis_data.apply(pd.to_numeric, errors='coerce').fillna(-1)

    # Prepare hover text combining assay and sample data
    combined_hover_text = (assay_data.astype(str) + "<br>" + sample_data.astype(str))

    fig_combined = go.Figure(data=go.Heatmap(
        z=ctdis_data_numeric.values,
        x=[str(i) for i in ctdis_data.columns],
        y=[str(i) for i in ctdis_data.index],
        colorscale=custom_colorscale,
        zmin=range_min,
        zmax=range_max,
        hoverinfo='text',
        text=combined_hover_text.values,
        xgap=1,  # Adds a gap between columns
        ygap=1   # Adds a gap between rows
    ))

    fig_combined.update_layout(
        title='Combined Heatmap of CT Dispensing with Assay and Sample Data',
        xaxis_title='Column Number',
        yaxis_title='Row Number'
    )

    color_range_text = html.Div([
        html.P(f"{color} range: {selected_color_ranges[color]}") for color in selected_colors
    ])
    
    # Compute the number of cells for each selected color range
    color_counts = {color: 0 for color in selected_colors}
    for color, (start, end) in selected_color_ranges.items():
        count = ((ctdis_data_numeric.values >= start) & (ctdis_data_numeric.values <= end)).sum()
        count -= color_subtractions.get(color, 0)  # Subtract the defined value
        color_counts[color] = max(count, 0)  # Ensure count does not go negative

    # Create bar chart
    bar_fig = go.Figure(data=[
        go.Bar(name=color, x=[color], y=[count], marker_color=color) for color, count in color_counts.items()
    ])
    
    bar_fig.update_layout(
        title='Number of Cells in Each Color Range',
        xaxis_title='Color',
        yaxis_title='Count',
        yaxis=dict(range=[0, max(color_counts.values()) * 1.2])  # Extend y-axis to make it longer
    )

    return fig_combined, color_range_text, bar_fig

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True, port=2000)
