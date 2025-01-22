import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State, ALL

app = Dash(__name__, suppress_callback_exceptions=True)

# Define the paths to the files
assaydis_path = 'Assay_dispensing.csv'
sampledis_path = 'Sample_dispensing.csv'
ctdis_path = 'Cts Dispensing pattern.csv'

# Read the CSV files into pandas DataFrames
ctdis_data = pd.read_csv(ctdis_path, index_col=0)
assay_data = pd.read_csv(assaydis_path, index_col=0)
sample_data = pd.read_csv(sampledis_path, index_col=0)

# Ensure the ct data is numeric
ctdis_data = ctdis_data.apply(pd.to_numeric, errors='coerce').fillna(-1.0)

# Create the Dash app
app = Dash(__name__)
server = app.server

# Define helper functions
def create_custom_colorscale(selected_color_ranges, zmin, zmax):
    """Create a custom color scale for the heatmap."""
    colorscale = []
    for color, (range_min, range_max) in selected_color_ranges.items():
        # Normalize the ranges to fit within zmin and zmax
        norm_min = max(0, min((range_min -zmin) / (zmax - zmin), 1))
        norm_max = min(0, min((range_max - zmin) / (zmax - zmin), 1))

        # Append normalized ranges and their corresponding color
        colorscale.append([norm_min, color])
        colorscale.append([norm_max, color])

    colorscale.insert(0, [0, "white"])  # Add a starting color for the lowest value
    colorscale.append([1, "black"])    # Add an ending color for the highest value
    return colorscale

def calculate_color_counts(data, color_ranges):
    """Calculate the count of data points within each color range."""
    counts = {color: 0 for color in color_ranges}
    for value in data.values.flatten():
        for color, (low, high) in color_ranges.items():
            if low <= value <= high:
                counts[color] += 1
                break
    return counts

# App layout
app.layout = html.Div([
    html.H1(
        "Plate Monkey Analysis",
        style={"font-family": "Arial", "text-align": "left"}  # Set font-family to Arial and align to center (optional)
    ),    
    html.Label(
        "Select a Colorscale:",
        style={"font-family": "Arial"}),
    dcc.Dropdown(
        id="colorscale-selector",
        options=[
            {"label": "Red-Blue (Diverging)", "value": "RdBu"},
            {"label": "Viridis (Sequential)", "value": "Viridis"},
            {"label": "Cividis (Sequential)", "value": "Cividis"},
            {"label": "Inferno (Sequential)", "value": "Inferno"},
            {"label": "Plasma (Sequential)", "value": "Plasma"},                {"label": "Turbo (Sequential)", "value": "Turbo"}
        ],
        value="RdBu",
        style={"font-family": "Arial"}

    ),
    html.Div(id="color-range-inputs"),  
    dcc.Graph(id="heatmap-plot"),
    dcc.Graph(id="bar-chart"),
    dcc.Graph(id="pie-chart"),
    html.Div(id="color-ranges"),
    html.Button("Update Heatmap and Bar Chart", id="update-btn")
])


# Callbacks for interactivity
@app.callback(
    [
        Output("heatmap-plot", "figure"),
        Output("bar-chart", "figure"),
        Output("pie-chart", "figure"),
        Output("color-ranges", "children"),
    ],
    [
        Input("update-btn", "n_clicks"),
        State("colorscale-selector", "value"),  # User-selected colorscale
        State({"type": "color-range", "color": ALL, "part": ALL}, "value")  # User-defined ranges
    ]
)
def update_heatmap_and_barchart(n_clicks, selected_colorscale, ranges):
    if not selected_colorscale:
        selected_colorscale = "RdBu"

    # Ensure ranges are in the expected format
    if len(ranges) % 2 != 0:
        return go.Figure(), go.Figure(), go.Figure(), "Invalid ranges provided."

    # Generate user-defined ranges
    selected_color_ranges = {}
    for i in range(0, len(ranges), 2):
        color = f"color-{i//2}"  # Assign a unique name for each range
        try:
            range_min = ranges[i]
            range_max = ranges[i + 1]
            selected_color_ranges[color] = (range_min, range_max)
        except IndexError:
            return go.Figure(), go.Figure(), go.Figure(), f"Error processing range {i}."

    if not selected_color_ranges:
        return go.Figure(), go.Figure(), go.Figure(), "No valid ranges provided."

    # Heatmap logic
    z = ctdis_data.values
    x_labels = ctdis_data.columns
    y_labels = ctdis_data.index

    combined_hover_text = (
        "Sample ID: " + assay_data.astype(str) + "<br>Sample Type: " + sample_data.astype(str)
    ).values

    zmin = ctdis_data.values.min()
    zmax = ctdis_data.values.max()

    heatmap_fig = go.Figure(go.Heatmap(
        z=ctdis_data.values,
        x=[str(i) for i in ctdis_data.columns],
        y=[str(i) for i in ctdis_data.index],
        colorscale=selected_colorscale,
        zmin=zmin,
        zmax=zmax,
        hoverinfo='text',
        text=combined_hover_text,
        colorbar=dict(
            tickvals=list(range(int(zmin), int(zmax) + 1, 5)),
            title="Value Range",
            titleside="right"
        ),
        xgap=1,
        ygap=1
    ))

    heatmap_fig.update_layout(
        title="Combined Heatmap of CT Dispensing with Assay and Sample Data",
        xaxis_title="Column Number",
        yaxis_title="Row Number",
        font=dict(family="Arial", color="black"),
        width=1000,
        height=700
    )

    # Bar chart logic
    color_counts = calculate_color_counts(ctdis_data, selected_color_ranges)
    bar_chart_fig = create_broken_axis_bar_chart(color_counts, selected_color_ranges)

    # Pie chart logic
    labels = list(color_counts.keys())
    values = list(color_counts.values())

    pie_chart_fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            hoverinfo="label+percent+value",
            textinfo="label+percent"
        )
    )
    pie_chart_fig.update_layout(
        title="Distribution of Samples Across Color Ranges",
        font=dict(family="Arial", color="black"),
        height=500,
        width=500
    )

    # Display selected ranges
    color_range_text = html.Div([
        html.P(f"{color} range: {selected_color_ranges[color]}") for color in selected_color_ranges
    ])

    return heatmap_fig, bar_chart_fig, pie_chart_fig, color_range_text

def create_broken_axis_bar_chart(color_counts, selected_color_ranges):
    # Define cut points for the axis break
    height = 800
    width = 800
    cut_interval = [60, 300]  # Adjust as needed

    # Split data into upper and lower ranges for broken axis
    upper_data = {k: v if v > cut_interval[1] else 0 for k, v in color_counts.items()}
    lower_data = {k: v if v <= cut_interval[1] else cut_interval[0] for k, v in color_counts.items()}

    # Map colors dynamically to match heatmap
    color_map = {"color-0": "red", "color-1": "blue", "color-2": "green", "color-3": "pink"}
    bar_colors = [color_map.get(color, "black") for color in color_counts.keys()]

    # Generate x_labels with dynamic color ranges
    x_labels = [
        f"{color}<br>({range_min}-{range_max})"
        for color, (range_min, range_max) in selected_color_ranges.items()
    ]

    bar_colors = "black"  # Change this to any color you prefer


    # Prepare subplots for the broken axis
    fig = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.02,  # Adjust space between the two axes
        shared_xaxes=True,     # Use the same x-axis labels for both sections
    )

    # Add upper axis trace
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=list(upper_data.values()),  # Data for the upper axis
            name="Upper Axis",
            marker=dict(color=bar_colors),  # Match the colors to the heatmap
        ),
        row=1, col=1
    )

    # Add lower axis trace
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=list(lower_data.values()),  # Data for the lower axis
            name="Lower Axis",
            marker=dict(color=bar_colors),  # Match the colors to the heatmap
        ),
        row=2, col=1
    )

    # Adjust the ranges for both axes
    fig.update_yaxes(
        range=[cut_interval[1], max(upper_data.values()) * 1.1],  # Upper axis range
        row=1, col=1,
        showline=True,
        showticklabels=True,
        linecolor="black",
        linewidth=2,
        ticks="outside",
        tickfont=dict(family="Arial", color="black", size=12)
    )
    fig.update_yaxes(
        range=[0, cut_interval[0]],  # Lower axis range
        row=2, col=1,
        showline=True,
        showticklabels=True,
        linecolor="black",
        linewidth=2,
        ticks="outside",
        tickfont=dict(family="Arial", color="black", size=12)
    )

    # Update x-axis (shared across both sections)
    fig.update_xaxes(
        showline=True,
        showticklabels=True,
        linecolor="black",
        linewidth=2,
        ticks="outside",
        tickfont=dict(family="Arial", color="black", size=12),
        row=2, col=1  # Apply only on the lower axis (shared x-axis)
    )

    # Customize layout
    fig.update_layout(
        title="Number of Cells in Each Color Range (Broken Axis)",
        xaxis2_title="Ct Range",
        yaxis_title="Number of Samples in Range",
        font=dict(family="Arial", color="black"),
        showlegend=False,
        height=height,
        width=width
    )

    return fig
 
@app.callback( 
    Output("color-range-inputs", "children"),
    [Input("colorscale-selector", "value")]
)
def update_color_inputs(selected_colors):
    if not selected_colors:
        return "Select colors to set ranges."
    
    inputs = []
    for color in selected_colors:
        inputs.append(html.Div([
            html.Label(f"{color.capitalize()} Range:"),
            dcc.Input(id={'type': 'color-range', 'color': color, 'part': 'min'}, 
                      type="number", placeholder="Min", style={"margin-right": "10px"}),
            dcc.Input(id={'type': 'color-range', 'color': color, 'part': 'max'}, 
                      type="number", placeholder="Max"),
        ]))
    return inputs

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=3000)



