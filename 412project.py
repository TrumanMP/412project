import os

import psycopg2


def manual_input():
    dbname = input("Your dbname: ")
    username = input("Your username: ")
    password = input("Your password: ")

    return dbname, username, password


if __name__ == "__main__":
    env_flag = input("Do you have environment variables already set up (Y/N)?: ")

    if env_flag.lower() == "Y".lower():
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

    cur.execute("""SELECT * FROM asu_employee_salary_data;""")

    print(cur.fetchone())

    conn.commit()

    cur.close()
    conn.close()
