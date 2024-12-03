import os

import pandas as pd
import plotly.express as px
import psycopg2
from dash import Dash, Input, Output, dcc, html


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
        html.H1("Salary Analysis by Department"),
        html.Label("Select Calendar Year:"),
        dcc.Dropdown(
            id="year-dropdown",
            options=[{"label": str(year), "value": year} for year in available_years],
            value=available_years[0],  # Default to the first year
        ),
        html.Label("Select Top N Departments:"),
        dcc.Input(
            id="top-n-input",
            type="number",
            value=5,  # Default to Top 5 departments
            min=1,
        ),
        dcc.Graph(id="salary-bar-chart"),
    ]
)


# Callback for updating the chart based on user input
@app.callback(
    Output("salary-bar-chart", "figure"),
    [Input("year-dropdown", "value"), Input("top-n-input", "value")],
)
def update_chart(selected_year, top_n):
    # Fetch department data for the selected year
    query = f"""
        SELECT department_description, AVG(salary) AS avg_salary
        FROM asu_employee_salary_data
        WHERE calendar_year = {selected_year}
        GROUP BY department_description
        ORDER BY avg_salary DESC;
    """
    data = pd.read_sql_query(query, conn)

    # Aggregate data into top N + "Other"
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

    # Rename columns for better display
    top_departments.rename(
        columns={
            "department_description": "Department",
            "avg_salary": "Average Salary",
        },
        inplace=True,
    )

    # Create bar chart
    fig = px.bar(
        top_departments,
        x="Average Salary",
        y="Department",
        orientation="h",
        title=f"Average Salary by Department for {selected_year} (Top {top_n} + Other)",
        labels={"Average Salary": "Average Salary ($)", "Department": "Department"},
        text="Average Salary",
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Average Salary ($)",
        yaxis_title="Department",
        template="plotly_white",
    )
    fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
