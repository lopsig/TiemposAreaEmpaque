import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# Leer las hojas del archivo Excel
data = {
    "ADICION_AGUA": pd.read_excel("DatosAreaEmpaque.xlsx", sheet_name="ADICION_AGUA"),
    "SUCCION_AGUA": pd.read_excel("DatosAreaEmpaque.xlsx", sheet_name="SUCCION_AGUA"),
    "TIEMPOS_EMPACAR": pd.read_excel("DatosAreaEmpaque.xlsx", sheet_name="TIEMPOS_EMPACAR")
}

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Tiempos de Procesos en Área de Empaque", style={'textAlign': 'center'}),

    html.H2("Suministro de Agua"),
    dcc.Dropdown(
        id='dropdown-adicion',
        options=[{"label": val, "value": val} for val in sorted(data["ADICION_AGUA"]["OnePiece"].unique())],
        multi=True,
        placeholder="Filtrar por OnePiece"
    ),
    dcc.DatePickerRange(
        id='fecha-adicion',
        display_format='YYYY-MM-DD',
        start_date_placeholder_text="Fecha inicio",
        end_date_placeholder_text="Fecha fin"
    ),
    dcc.Graph(id='grafico-adicion'),

    html.H2("Succión de Agua"),
    dcc.Dropdown(
        id='dropdown-succion',
        options=[{"label": val, "value": val} for val in sorted(data["SUCCION_AGUA"]["OnePiece"].unique())],
        multi=True,
        placeholder="Filtrar por OnePiece"
    ),
    dcc.DatePickerRange(
        id='fecha-succion',
        display_format='YYYY-MM-DD',
        start_date_placeholder_text="Fecha inicio",
        end_date_placeholder_text="Fecha fin"
    ),
    dcc.Graph(id='grafico-succion'),

    html.H2("Tiempos de Procesos de Empaque"),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='filtro-onepiece-empacar',
                options=[{"label": op, "value": op} for op in sorted(data["TIEMPOS_EMPACAR"]["OnePiece"].unique())],
                multi=True,
                placeholder="Filtrar por OnePiece"
            )
        ]),
        html.Div([
            dcc.Dropdown(
                id='filtro-proceso-empacar',
                options=[{"label": p, "value": p} for p in sorted(data["TIEMPOS_EMPACAR"]["Proceso"].unique())],
                multi=True,
                placeholder="Filtrar por Proceso"
            )
        ]),
    ]),

    html.Br(),

    html.Label("Filtrar por Rango de Fechas:"),
    dcc.DatePickerRange(
        id='rango-fechas-empacar',
        start_date=data["TIEMPOS_EMPACAR"]["Fecha"].min(),
        end_date=data["TIEMPOS_EMPACAR"]["Fecha"].max(),
        display_format='YYYY-MM-DD'
    ),

    dcc.Graph(id='grafico-empacar')
])

# Función genérica para crear figura
def create_figure(df, filtro_col, filtro_vals, date_range, titulo):
    dff = df.copy()

    if filtro_vals:
        dff = dff[dff[filtro_col].isin(filtro_vals)]

    if 'Fecha' in dff.columns and date_range and all(date_range):
        dff['Fecha'] = pd.to_datetime(dff['Fecha'], errors='coerce')
        dff = dff[(dff['Fecha'] >= pd.to_datetime(date_range[0])) & (dff['Fecha'] <= pd.to_datetime(date_range[1]))]

    agrupado = dff.groupby(filtro_col)["Tiempo Unidad [s]"].mean().reset_index()
    agrupado["Tiempo promedio [s]"] = agrupado["Tiempo Unidad [s]"].round(2)

    fig = px.bar(
        agrupado,
        x=filtro_col,
        y="Tiempo promedio [s]",
        text="Tiempo promedio [s]",
        labels={filtro_col: filtro_col.upper(), "Tiempo promedio [s]": "SEG"},
        title=titulo,
        color_discrete_sequence=['#2C73D2']
    )

    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_tickangle=-45,
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        title_x=0.5,
        yaxis=dict(title='Tiempo promedio [s]'),
        margin=dict(l=40, r=40, t=60, b=100),
        height=700
    )
    return fig

# Callbacks
@app.callback(
    Output('grafico-adicion', 'figure'),
    Input('dropdown-adicion', 'value'),
    Input('fecha-adicion', 'start_date'),
    Input('fecha-adicion', 'end_date')
)
def actualizar_adicion(onepiece_vals, start_date, end_date):
    return create_figure(data["ADICION_AGUA"], "OnePiece", onepiece_vals, [start_date, end_date], "Tiempo Promedio de Suministro de Agua")

@app.callback(
    Output('grafico-succion', 'figure'),
    Input('dropdown-succion', 'value'),
    Input('fecha-succion', 'start_date'),
    Input('fecha-succion', 'end_date')
)
def actualizar_succion(onepiece_vals, start_date, end_date):
    return create_figure(data["SUCCION_AGUA"], "OnePiece", onepiece_vals, [start_date, end_date], "Tiempo Promedio de Succión de Agua")

@app.callback(
    Output('grafico-empacar', 'figure'),
    [Input('filtro-onepiece-empacar', 'value'),
     Input('filtro-proceso-empacar', 'value'),
     Input('rango-fechas-empacar', 'start_date'),
     Input('rango-fechas-empacar', 'end_date')]
)
def actualizar_grafico_empacar(onepiece_seleccionados, proceso_seleccionados, fecha_inicio, fecha_fin):
    df = data['TIEMPOS_EMPACAR'].copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df[df['Fecha'].between(pd.to_datetime(fecha_inicio), pd.to_datetime(fecha_fin))]

    if onepiece_seleccionados:
        df = df[df['OnePiece'].isin(onepiece_seleccionados)]
    if proceso_seleccionados:
        df = df[df['Proceso'].isin(proceso_seleccionados)]

    df_grouped = df.groupby(['OnePiece', 'Proceso'])['Tiempo Unidad [s]'].mean().reset_index()
    df_grouped['Etiqueta'] = df_grouped['OnePiece'] + " - " + df_grouped['Proceso']
    df_grouped['Promedio'] = df_grouped['Tiempo Unidad [s]'].round(2)

    fig = px.bar(
        df_grouped,
        x='Etiqueta',
        y='Promedio',
        text='Promedio',
        labels={'Etiqueta': 'ONE PIECE - PROCESO', 'Promedio': 'SEG'},
        title='Tiempo Promedio por Proceso de Empaque',
        color_discrete_sequence=['#2C73D2']
    )

    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_tickangle=-45,
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        title_x=0.5,
        yaxis=dict(title='Tiempo promedio [s]'),
        margin=dict(l=40, r=40, t=60, b=100),
        height=700
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)