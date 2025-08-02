# import
import dash
import dash_bootstrap_components as dbc
# Corrected Input, Output to be capitalized
from dash import dcc, Input, Output, html
import plotly.express as px
import pandas as pd


# loading data
def load_data():
    df = pd.read_csv("asset/healthcare.csv")
    # Ensure 'Billing Amount' is numeric. The original line was adding it to itself.
    df["Billing Amount"] = pd.to_numeric(df["Billing Amount"], errors='coerce')
    # Corrected column name from "Date of Admission" to "Date of Admission"
    df["Date of Admission"] = pd.to_datetime(
        df["Date of Admission"], errors='coerce')
    df["year month"] = df["Date of Admission"].dt.to_period(
        'M')  # Use the already converted datetime column
    return df


df = load_data()

num_records = len(df)
average_billing = df["Billing Amount"].mean()


# create a web app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# layout and design - This must come BEFORE app.run_server
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Healthcare Dashboard"),
                width=12, className="text-center my-5")
    ]),
    # hospital statistics
    dbc.Row([
        dbc.Col(html.Div(f"Total Records: {num_records}",
                         className="text-center my-3 top-text"), width=5),
        dbc.Col(html.Div(f"Average Billing: ${average_billing:,.2f}",
                         className="text-center my-3 top-text"), width=4)
    ], className="mb-5"),

    # male or female demographics
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Patient Demographics", className="card-title"),
                    dcc.Dropdown(
                        id="gender-filter",
                        options=[{'label': gender, 'value': gender}
                                 for gender in df["Gender"].unique()],
                        value=None,
                        placeholder="Select Gender"
                    ),
                    dcc.Graph(id="age-distribution")
                ])
            ])
        ], width=7),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Medical condition Distribution",
                            className="card-title"),
                    dcc.Graph(id="condition-distribution")
                ])
            ])
        ], width=5)
    ]),

    # insurance Provider data
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Insurance Provider Comparison ",
                            className="card-title"),
                    dcc.Graph(id="insurance-provider-comparison")
                ])
            ])
        ], width=12)
    ]),

    # billing distribution
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Billing Amount Distribution",
                            className="card-title"),
                    dcc.Slider(id="billing-slider", min=df["Billing Amount"].min(), max=df["Billing Amount"].max(), value=df["Billing Amount"].median(),
                               marks={int(value): f'${int(value):,}' for value in df["Billing Amount"].quantile([0, 0.25, 0.5, 0.75, 1]).values}, step=100),
                    dcc.Graph(id="billing-distribution")
                ])
            ])
        ], width=12)
    ]),

    # trends in admission
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Trends in Admission", className="card-title"),
                    dcc.RadioItems(
                        id='chart-type',
                        options=[{"label": "line chart", 'value': 'line'},
                                 {"label": "bar chart", 'value': 'bar'}],
                        value='line',
                        inline=True,
                        className='mb-4'
                    ),
                    dcc.Dropdown(id='condition-filter', options=[{'label': condition, 'value': condition} for condition in df["Medical Condition"] .unique()],
                                 value=None,
                                 placeholder="Select a condition"
                                 ),
                    dcc.Graph(id="admission-trends")
                ])
            ])
        ], width=12)
    ])
], fluid=True)

# create our clallbacks


@app.callback(
    Output('age-distribution', 'figure'),
    Input('gender-filter', 'value')
)
def update_distribution(selected_gender):
    if selected_gender:
        filtered_df = df[df["Gender"] == selected_gender]
    else:
        filtered_df = df

    if filtered_df.empty:
        return {}
    return px.histogram(
        filtered_df,
        x="Age",
        nbins=20,
        color="Gender",
        title="Age distribution by Gender",
        color_discrete_sequence=["#2c9ace", "#E64199"]
    )

# medical condition distribution


@app.callback(
    Output('condition-distribution', 'figure'),
    Input('gender-filter', 'value')
)
def update_medical_condition(selected_gender):
    filtered_df = df[df["Gender"] ==
                     selected_gender] if selected_gender else df
    fig = px.pie(filtered_df, names="Medical Condition",
                 title="Medical Condition Distribution")
    return fig

# insurance provider comparison


@app.callback(
    Output('insurance-provider-comparison', 'figure'),
    Input('gender-filter', 'value')
)
def update_insurance_provider(selected_gender):
    filtered_df = df[df["Gender"] ==
                     selected_gender] if selected_gender else df
    fig = px.bar(filtered_df, x="Insurance Provider", y="Billing Amount", color="Medical Condition", barmode="group",
                 title="Insurance Provider Price Comparison", color_discrete_sequence=px.colors.qualitative.Set2)
    return fig


# billing distribution

@app.callback(
    Output('billing-distribution', 'figure'),
    [Input('gender-filter', 'value'),
     Input('billing-slider', 'value')]
)
def update_billing_distribution(selected_value, slider_value):
    filtered_df = df[df["Gender"] == selected_value] if selected_value else df
    filtered_df = filtered_df[filtered_df["Billing Amount"] <= slider_value]
    fig = px.histogram(filtered_df, x="Billing Amount", nbins=20,
                       title="Billing Amount Distribution", template="plotly")
    return fig


# Trends in admission


@app.callback(
    Output('admission-trends', 'figure'),
    Input('chart-type', 'value'),
    Input('condition-filter', 'value')
)
def update_admission_trends(chart_type, selected_condition):
    filtered_df = df[df["Medical Condition"] ==
                     selected_condition] if selected_condition else df

    trends_df = filtered_df.groupby(
        'year month').size().reset_index(name='Count')
    trends_df['year month'] = trends_df['year month'].astype(str)
    if chart_type == 'line':
        fig = px.line(trends_df, x='year month', y='Count',
                      title='admission trends over time')
    else:
        fig = px.bar(trends_df, x='year month', y='Count',
                     title='admission trends over time')
    return fig


# Callbacks
if __name__ == "__main__":
    app.run(debug=True)
