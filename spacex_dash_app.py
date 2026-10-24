import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

# Load dataset
spacex_df = pd.read_csv("spacex_launch_dash.csv")

# Remove the unnecessary index column
spacex_df = spacex_df.loc[:, ~spacex_df.columns.str.startswith("Unnamed:")]

# Ensure required columns exist
required_columns = ["Launch Site", "class", "Payload Mass (kg)"]
missing = [col for col in required_columns if col not in spacex_df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

# Prepare values
launch_sites = sorted(spacex_df["Launch Site"].dropna().unique())
min_payload = int(spacex_df["Payload Mass (kg)"].min())
max_payload = int(spacex_df["Payload Mass (kg)"].max())

app = dash.Dash(__name__)

app.layout = html.Div(
    style={"fontFamily": "Arial", "margin": "30px"},
    children=[
        html.H1(
            "SpaceX Launch Records Dashboard",
            style={"textAlign": "center"}
        ),

        html.Label("Select Launch Site:"),

        dcc.Dropdown(
            id="site-dropdown",
            options=[
                {"label": "All Sites", "value": "All Sites"}
            ] + [
                {"label": site, "value": site}
                for site in launch_sites
            ],
            value="All Sites",
            clearable=False
        ),

        html.Br(),

        html.Div(
            dcc.Graph(id="success-pie-chart")
        ),

        html.Hr(),

        html.Label("Select Payload Mass Range (kg):"),

        dcc.RangeSlider(
            id="payload-slider",
            min=min_payload,
            max=max_payload,
            step=250,
            marks={
                int(value): str(int(value))
                for value in range(
                    (min_payload // 1000) * 1000,
                    max_payload + 1,
                    1000
                )
            },
            value=[min_payload, max_payload],
            tooltip={"placement": "bottom", "always_visible": True}
        ),

        html.Br(),

        html.Div(
            dcc.Graph(id="success-payload-scatter-chart")
        )
    ]
)


@app.callback(
    Output("success-pie-chart", "figure"),
    Input("site-dropdown", "value")
)
def get_pie_chart(launch_site):
    if launch_site == "All Sites":
        site_data = spacex_df.groupby("Launch Site")["class"].agg(
            ["sum", "count"]
        ).reset_index()

        site_data["Failure"] = site_data["count"] - site_data["sum"]

        chart_data = pd.DataFrame({
            "Launch Site": site_data["Launch Site"],
            "Successful Landings": site_data["sum"],
            "Unsuccessful Landings": site_data["Failure"]
        }).melt(
            id_vars="Launch Site",
            var_name="Landing Outcome",
            value_name="Number of Launches"
        )

        fig = px.bar(
            chart_data,
            x="Launch Site",
            y="Number of Launches",
            color="Landing Outcome",
            barmode="group",
            title="Successful and Unsuccessful Landings by Launch Site"
        )

    else:
        site_data = spacex_df[spacex_df["Launch Site"] == launch_site]
        outcome_counts = (
            site_data["class"]
            .map({0: "Unsuccessful Landing", 1: "Successful Landing"})
            .value_counts()
            .reset_index()
        )
        outcome_counts.columns = ["Landing Outcome", "Number of Launches"]

        fig = px.pie(
            outcome_counts,
            names="Landing Outcome",
            values="Number of Launches",
            title=f"Landing Outcomes at {launch_site}"
        )

    return fig


@app.callback(
    Output("success-payload-scatter-chart", "figure"),
    [
        Input("site-dropdown", "value"),
        Input("payload-slider", "value")
    ]
)
def get_payload_chart(launch_site, payload_range):
    low, high = payload_range

    filtered_df = spacex_df[
        (spacex_df["Payload Mass (kg)"] >= low) &
        (spacex_df["Payload Mass (kg)"] <= high)
    ]

    if launch_site != "All Sites":
        filtered_df = filtered_df[
            filtered_df["Launch Site"] == launch_site
        ]

    fig = px.scatter(
        filtered_df,
        x="Payload Mass (kg)",
        y="class",
        color="Booster Version Category",
        hover_data=["Flight Number", "Launch Site", "Booster Version"],
        title="Payload Mass vs Landing Outcome",
        labels={
            "class": "Landing Outcome (0 = Unsuccessful, 1 = Successful)",
            "Payload Mass (kg)": "Payload Mass (kg)",
            "Booster Version Category": "Booster Version"
        }
    )

    fig.update_yaxes(
        tickmode="array",
        tickvals=[0, 1],
        ticktext=["Unsuccessful", "Successful"]
    )

    return fig


if __name__ == "__main__":
    app.run(debug=True)
