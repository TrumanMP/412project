import os
import time

import matplotlib.pyplot as plt
import numpy as np
import psycopg2


def manual_input():
    dbname = input("Your dbname: ")
    username = input("Your username: ")
    password = input("Your password: ")

    return dbname, username, password


def plot_histogram(salaries):
    bin_count = 30  # Maybe make this a slider later

    min_salary = min(salaries)
    max_salary = max(salaries)

    bins = np.linspace(min_salary, max_salary, bin_count)
    # Clear the previous plot and create a new histogram
    plt.clf()
    plt.hist(salaries, bins=bins, edgecolor="black", alpha=0.7)
    plt.title("Faculty Salaries Distribution")
    plt.xlabel("Salary")
    plt.ylabel("Frequency")
    plt.draw()
    plt.pause(0.001)  # Pause to update the plot in real-time


if __name__ == "__main__":
    env_flag = input("Do you have environment variables already set up (Y/N)?: ")

    if env_flag.lower() == "y":
        dbname = os.getenv("DBNAME")
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
    else:
        dbname, username, password = manual_input()

    conn = psycopg2.connect(
        host="localhost",
        dbname=f"{dbname}",
        user=f"{username}",
        password=f"{password}",
        port=5432,
    )

    cur = conn.cursor()

    # Select only the salary data from the table
    cur.execute("""SELECT salary FROM asu_employee_salary_data;""")

    # Initialize a list to store salaries
    salaries = []

    # Set up matplotlib for dynamic plotting
    plt.ion()  # Turn on interactive mode
    plt.figure(figsize=(10, 6))

    # Fetch and plot data dynamically
    for row in cur:
        salary = row[0]
        salary = float(salary.replace("$", "").replace(",", ""))
        salaries.append(salary)

        # Plot the histogram dynamically
        plot_histogram(salaries)

    # Close the cursor and connection
    cur.close()
    conn.close()

    # Keep the plot open
    plt.ioff()  # Turn off interactive mode
    plt.show()
