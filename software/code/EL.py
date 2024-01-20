from datetime import datetime, timedelta
from pytz import timezone

import pandas as pd
import csv

import requests
import glob
import os


from sqlalchemy import create_engine
from sqlalchemy.sql import text

db_name = "TW_op_avail"
db_user = "postgres"
db_pass = "postgres"
db_host = "db"
db_port = "5432"
table_name = "tw_data"

# Connect to PostgreSQL
eng_str = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
engine = create_engine(eng_str)


# Define common params
cycles = {
    0: "Timely",
    1: "Evening",
    3: "Intraday 1",
    4: "Intraday 2",
    7: "Intraday 3",
    5: "Final",
}
current_date = datetime.now(timezone("EST"))


def check_database():
    """
    Check database connections and that table exists
    """
    # Check if connection successfully established
    try:
        conn = engine.connect()
        print("LOG: Connection to database is correct")
        conn.close()
    except Exception as e:
        print(f"ERROR: Connection error: {e}")

    # Check if the table is in the DB
    with engine.connect() as conn:
        try:
            tb_check = text("SELECT EXISTS (SELECT * FROM tw_data);")
            res = conn.execute(tb_check).all()
            if res:
                print("LOG: Table is initialize correctly")
            else:
                print(
                    "WARNING: Table doesn't exist, please check initialization process and database connections. Otherwise, table will be created later"
                )
        except Exception as e:
            print(f"Connection error: {e}")


def check_if_downloaded(date, cycle):
    """
    Check if the combination of date and cycle is already in the table
    """
    with engine.connect() as conn:
        statement = text(
            """SELECT EXISTS (
                                SELECT 1
                                FROM tw_data
                                WHERE "Date" = :date
                                AND "Cycle" = :cycle
                                );"""
        )
        res = conn.execute(statement, {"date": date, "cycle": cycle}).all()
    return res[0][0]


def extract_data():
    """
    Download data from `https://twtransfer.energytransfer.com/ipost/TW/capacity/operationally-available for the past 3 days`
    format: CSV file(s)
    Options:
        Search Type: `All Active Location` (`ALL`)
        Cycle: All available cycles (Timely, Evening, Intraday 1, Intraday 2, Intraday 3, Final)
    Return:
        path of files if everything runs correctly
    TODO: Make this function more configurable
    """
    # list of dates of the past 3 days
    date_list = [
        current_date,
        current_date - timedelta(days=1),
        current_date - timedelta(days=2),
    ]
    for date in date_list:
        # Get data from API
        date = date.strftime("%m/%d/%Y")
        print(date)
        url = "https://twtransfer.energytransfer.com/ipost/capacity/operationally-available"
        for cycle in cycles:
            if not check_if_downloaded(date, cycles[cycle]):
                params = {
                    "f": "csv",
                    "extension": "csv",
                    "asset": "TW",
                    "gasDay": date,
                    "cycle": cycle,
                    "searchType": "ALL",
                    "searchString": "",
                    "locType": "ALL",
                    "locZone": "ALL",
                }
                date_f = date.replace("/", "-")
                cycle_f = cycles[cycle]
                output_file = f"./data/OAC_TW_007933047_{date_f}_{cycle_f}.csv"

                response = requests.get(url, params=params)

                if response.status_code == 200:
                    with open(output_file, "wb") as file:
                        file.write(response.content)
                    print(f"LOG: {output_file} downloaded successfully.")
                else:
                    print(
                        f"ERROR: Failed to download file. Status code: {response.status_code}"
                    )
            else:
                print(
                    f"LOG: Data for cycle '{cycles[cycle]}' of {date} is already downloaded. skipping..."
                )


def validate(csv):
    """
    Parse and validate downloaded CSVs. Check if file is empty, rows and columns follow the constraints.
    Return True if CSV is validated, False if there's an error. This error will be logged in the log file.
    """
    pass


def load():
    """
    Insert validated CSVs into the database. Add necessary columns:
    1. Date
    2. Cycle
    """

    csv_files_path = f"./data/OAC_TW_007933047_*.csv"
    csv_files = glob.glob(csv_files_path)
    dfs = []
    for csv_file in csv_files:
        #
        # if not parse_and_validate(csv_file):
        #     print(f"Error, file {csv_file} is not validated. For more information, check the log file...")
        #     continue
        #     # TODO: more specific error handling (rows/columns, error etc)
        df = pd.read_csv(csv_file)
        df["Date"] = csv_file.split("_")[-2]
        df["Cycle"] = csv_file.split("_")[-1].replace(".csv", "")
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_sql(table_name, engine, if_exists="append", index=False)
    print("LOG: Finished loading to database")

    # Clean up all loaded files
    for csv_file in csv_files:
        print("LOG: Deleting files from filesystem")
        os.remove(csv_file)


if __name__ == "__main__":
    print(
        f"LOG: Starting the process. Today is {current_date.strftime('%m/%d/%Y')}. Downloading data of the last three days."
    )
    check_database()
    extract_data()
    load()
    print("LOG: Finished process. Shutting down...")


