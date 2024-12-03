import os

import pandas as pd
import plotly.express as px
import psycopg2
from dash import Dash, Input, Output, dcc, html
from dash.dash_table import DataTable


# Manual PostgreSQL connection handling
def get_db_credentials():
    manual_input = input(
        "Do you have environment variables for db_host, db_port, db_name, db_user, and db_password (Y/N)? : "
    )

    if manual_input.lower() == "y":
        db_host = os.getenv("db_host")
        db_port = os.getenv("db_port")
        db_name = os.getenv("db_name")
        db_user = os.getenv("db_user")
        db_password = os.getenv("db_password")
    else:
        db_host = input("Enter the database host: ")
        db_port = input("Enter the database port: ")
        db_name = input("Enter the database name: ")
        db_user = input("Enter the database username: ")
        db_password = input("Enter the database password: ")

    return db_host, db_port, db_name, db_user, db_password


# Get database credentials
db_host, db_port, db_name, db_user, db_password = get_db_credentials()

try:
    conn = psycopg2.connect(
        host=db_host, port=db_port, database=db_name, user=db_user, password=db_password
    )
    print("Connection to PostgreSQL database successful!")
except Exception as e:
    print(f"Error: {e}")
    exit()

# Fetch unique calendar years for dropdown menu
years_query = "SELECT DISTINCT calendar_year FROM asu_employee_salary_data ORDER BY calendar_year;"
years_data = pd.read_sql_query(years_query, conn)
available_years = years_data["calendar_year"].tolist()

# Initialize Dash app
app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Salary Analysis"),
        html.Label("Select Analysis Type:"),
        dcc.Dropdown(
            id="analysis-dropdown",
            options=[
                {"label": "Average Salary by Department", "value": "avg_salary"},
                {"label": "Highest Individual Salaries", "value": "highest_salaries"},
            ],
            value="avg_salary",  # Default option
        ),
        html.Label("Select Calendar Year:"),
        dcc.Dropdown(
            id="year-dropdown",
            options=[{"label": str(year), "value": year} for year in available_years],
            value=available_years[0],  # Default to the first year
        ),
        html.Label("Select Top N Records:"),
        dcc.Input(
            id="top-n-input",
            type="number",
            value=5,  # Default to Top 5 records
            min=1,
        ),
        dcc.Graph(id="salary-chart"),
        html.Hr(),
        html.H3("Database Table Viewer"),
        DataTable(
            id="data-table",
            columns=[], 
            page_size=10,
            style_table={"overflowX": "auto"},
        ),
    ]
)


# Callback for updating the chart based on user input
@app.callback(
    [
        Output("salary-chart", "figure"), 
        Output("data-table", "columns"),  
        Output("data-table", "data"),     
    ],
    [
        Input("analysis-dropdown", "value"),
        Input("year-dropdown", "value"),
        Input("top-n-input", "value"),
    ],
)
def update_chart_and_table(analysis_type, selected_year, top_n):
    # Default query results
    chart_figure = {}
    table_columns = []
    table_data = []

    if analysis_type == "avg_salary":
        # Query for average salary by department
        query = f"""
            SELECT department_description, AVG(salary) AS avg_salary
            FROM asu_employee_salary_data
            WHERE calendar_year = {selected_year}
            GROUP BY department_description
            ORDER BY avg_salary DESC;
        """
        data = pd.read_sql_query(query, conn)

        # Chart for average salary
        data = data.sort_values(by="avg_salary", ascending=False)
        top_departments = data.iloc[:top_n]
        other_departments = data.iloc[top_n:]

        if not other_departments.empty:
            other_avg_salary = other_departments["avg_salary"].mean()
            top_departments = pd.concat(
                [
                    top_departments,
                    pd.DataFrame(
                        {
                            "department_description": ["Other"],
                            "avg_salary": [other_avg_salary],
                        }
                    ),
                ]
            )

        top_departments.rename(
            columns={
                "department_description": "Department",
                "avg_salary": "Average Salary",
            },
            inplace=True,
        )

        chart_figure = px.bar(
            top_departments,
            x="Average Salary",
            y="Department",
            orientation="h",
            title=f"Average Salary by Department for {selected_year} (Top {top_n} + Other)",
            labels={"Average Salary": "Average Salary ($)", "Department": "Department"},
            text="Average Salary",
        )
        chart_figure.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Average Salary ($)",
            yaxis_title="Department",
            template="plotly_white",
        )
        chart_figure.update_traces(texttemplate="$%{text:.2f}", textposition="outside")

        # Populate table for the database viewer
        table_columns = [{"name": col, "id": col} for col in data.columns]
        table_data = data.to_dict("records")

    elif analysis_type == "highest_salaries":
        # Query for highest individual salaries
        query = f"""
            SELECT full_name, job_description, department_description, salary
            FROM asu_employee_salary_data
            WHERE calendar_year = {selected_year}
            ORDER BY salary DESC
            LIMIT {top_n};
        """
        data = pd.read_sql_query(query, conn)

        # Chart for highest salaries
        data.rename(
            columns={"full_name": "Employee", "salary": "Salary"},
            inplace=True,
        )

        chart_figure = px.bar(
            data,
            x="Salary",
            y="Employee",
            orientation="h",
            title=f"Highest Individual Salaries for {selected_year} (Top {top_n})",
            labels={"Salary": "Salary ($)", "Employee": "Employee"},
            text="Salary",
        )
        chart_figure.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Salary ($)",
            yaxis_title="Employee",
            template="plotly_white",
        )
        chart_figure.update_traces(
            text=data['Salary'].apply(lambda x: f"${x:,.2f}"),  
            textposition="outside"
        )

    
        table_columns = [{"name": col, "id": col} for col in data.columns]
        table_data = data.to_dict("records")

    return chart_figure, table_columns, table_data




if __name__ == "__main__":
    app.run_server(debug=True)
