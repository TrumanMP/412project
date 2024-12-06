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
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
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
departments_query = "SELECT DISTINCT department_description FROM asu_employee_salary_data ORDER BY department_description;"
years_data = pd.read_sql_query(years_query, conn)
departments_data = pd.read_sql_query(departments_query, conn)
available_years = years_data["calendar_year"].tolist()
available_departments = departments_data["department_description"].tolist()

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
                {"label": "Median Salary by Department", "value": "median_salary"},
                {
                    "label": "Salary Distribution by Department",
                    "value": "salary_distribution",
                },
                {"label": "Top N Salary Growth Over Years", "value": "salary_growth"},
                {
                    "label": "Individual Department Salary Growth",  # My text editor makes this formatting weird sometimes.
                    "value": "department_salary_growth",
                },  # New option
                {"label": "Highest Individual Salaries", "value": "highest_salaries"},
            ],
            value="avg_salary",  # Default option
        ),
        html.Label("Select a Department (For Salary Growth Analysis):"),
        dcc.Dropdown(
            id="department-dropdown",
            options=[{"label": dept, "value": dept} for dept in available_departments],
            value=available_departments[0],  # Default to the first department
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
        html.Br(),
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
        Input("department-dropdown", "value"),
    ],
)
def update_chart_and_table(analysis_type, selected_year, top_n, selected_department):
    chart_figure = {}
    table_columns = []
    table_data = []

    if analysis_type == "avg_salary":
        query = f"""
            SELECT department_description, AVG(salary) AS avg_salary
            FROM asu_employee_salary_data
            WHERE calendar_year = {selected_year}
            GROUP BY department_description
            ORDER BY avg_salary DESC;
        """
        data = pd.read_sql_query(query, conn)

        # Sort and filter top N
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

        # Rename columns for visualization
        top_departments.rename(
            columns={
                "department_description": "Department",
                "avg_salary": "Average Salary",
            },
            inplace=True,
        )

        # Plot the filtered data
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
        table_columns = [{"name": col, "id": col} for col in data.columns]
        table_data = data.to_dict("records")

    elif analysis_type == "median_salary":
        query = f"""
            SELECT department_description, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary
            FROM asu_employee_salary_data
            WHERE calendar_year = {selected_year}
            GROUP BY department_description
            ORDER BY median_salary DESC;
        """
        data = pd.read_sql_query(query, conn)

        # Sort and filter top N
        top_departments = data.iloc[:top_n]
        other_departments = data.iloc[top_n:]

        if not other_departments.empty:
            other_median_salary = other_departments["median_salary"].median()
            top_departments = pd.concat(
                [
                    top_departments,
                    pd.DataFrame(
                        {
                            "department_description": ["Other"],
                            "median_salary": [other_median_salary],
                        }
                    ),
                ]
            )

        # Rename columns for visualization
        top_departments.rename(
            columns={
                "department_description": "Department",
                "median_salary": "Median Salary",
            },
            inplace=True,
        )

        # Plot the filtered data
        chart_figure = px.bar(
            top_departments,
            x="Median Salary",
            y="Department",
            orientation="h",
            title=f"Median Salary by Department for {selected_year} (Top {top_n} + Other)",
            labels={"Median Salary": "Median Salary ($)", "Department": "Department"},
            text="Median Salary",
        )
        chart_figure.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Median Salary ($)",
            yaxis_title="Department",
            template="plotly_white",
        )
        chart_figure.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
        table_columns = [{"name": col, "id": col} for col in data.columns]
        table_data = data.to_dict("records")

    elif analysis_type == "salary_distribution":
        query = f"""
            SELECT department_description, salary
            FROM asu_employee_salary_data
            WHERE calendar_year = {selected_year};
        """
        data = pd.read_sql_query(query, conn)

        # Aggregate data to compute average salary for filtering
        avg_salary_data = (
            data.groupby("department_description", as_index=False)["salary"]
            .mean()
            .rename(columns={"salary": "avg_salary"})
        )
        avg_salary_data = avg_salary_data.sort_values(by="avg_salary", ascending=False)

        # Filter Top N based on average salary
        top_departments = avg_salary_data.iloc[:top_n][
            "department_description"
        ].tolist()
        filtered_data = data[data["department_description"].isin(top_departments)]

        # Plot salary distribution for the filtered departments
        chart_figure = px.box(
            filtered_data,
            x="department_description",
            y="salary",
            title=f"Salary Distribution by Department for {selected_year} (Top {top_n})",
            labels={"salary": "Salary ($)", "department_description": "Department"},
        )
        chart_figure.update_layout(
            xaxis_title="Department",
            yaxis_title="Salary ($)",
            template="plotly_white",
        )

        table_columns = [{"name": col, "id": col} for col in data.columns]
        table_data = filtered_data.to_dict("records")

        ''' #Work in progress. Currently makes no sense since top N metric is not well-defined.
        elif analysis_type == "salary_growth":
            query = f"""
                SELECT calendar_year, department_description, AVG(salary) AS avg_salary
                FROM asu_employee_salary_data
                GROUP BY calendar_year, department_description
                ORDER BY calendar_year, avg_salary DESC;
            """
            data = pd.read_sql_query(query, conn)

            # Aggregate data to find the most relevant departments for filtering
            avg_salary_data = (
                data.groupby("department_description", as_index=False)["avg_salary"]
                .mean()
                .rename(columns={"avg_salary": "overall_avg_salary"})
            )
            avg_salary_data = avg_salary_data.sort_values(
                by="overall_avg_salary", ascending=False
            )

            # Filter Top N based on average salary
            top_departments = avg_salary_data.iloc[:top_n][
                "department_description"
            ].tolist()
            filtered_data = data[data["department_description"].isin(top_departments)]

            # Plot salary growth for the filtered departments
            chart_figure = px.line(
                filtered_data,
                x="calendar_year",
                y="avg_salary",
                color="department_description",
                title=f"Salary Growth Over Years for Top {top_n} Departments",
                labels={
                    "calendar_year": "Year",
                    "avg_salary": "Average Salary ($)",
                    "department_description": "Department",
                },
            )
            chart_figure.update_layout(
                xaxis_title="Year",
                yaxis_title="Average Salary ($)",
                template="plotly_white",
            )

            table_columns = [{"name": col, "id": col} for col in data.columns]
            table_data = filtered_data.to_dict("records")
            '''

    elif analysis_type == "department_salary_growth":
        query = f"""
                SELECT calendar_year, AVG(salary) AS avg_salary
                FROM asu_employee_salary_data
                WHERE department_description = '{selected_department}'
                GROUP BY calendar_year
                ORDER BY calendar_year;
            """
        data = pd.read_sql_query(query, conn)
        chart_figure = px.line(
            data,
            x="calendar_year",
            y="avg_salary",
            title=f"Salary Growth Over Years for {selected_department}",
        )
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
            text=data["Salary"].apply(lambda x: f"${x:,.2f}"), textposition="outside"
        )

        table_columns = [{"name": col, "id": col} for col in data.columns]
        table_data = data.to_dict("records")

    return chart_figure, table_columns, table_data


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
