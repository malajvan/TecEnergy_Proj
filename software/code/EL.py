from datetime import datetime, timedelta
from pytz import timezone

import pandas as pd
import csv

import requests
import glob
import os
import logging

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
    5: "Final"
}
current_date = datetime.now(timezone("EST"))

# Define logging param
logging.basicConfig(
    level=logging.INFO,
    filename="./app.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def check_database():
    """
    Check database connections and that table exists
    """
    # Check if connection successfully established
    try:
        conn = engine.connect()
        logging.info("Connected to the database")
        conn.close()
    except Exception as e:
        logging.exception("Connection error")

    # Check if the table is in the DB
    with engine.connect() as conn:
        try:
            tb_check = text("SELECT EXISTS (SELECT * FROM tw_data);")
            res = conn.execute(tb_check).all()
            if res:
                logging.info("Table is initialized correctly")
            else:
                logging.warning(
                    "Table doesn't exist, please check initialization process and database connections. Otherwise, table will be created later"
                )
        except Exception as e:
            logging.exception(f"Connection error")


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
        logging.info("")
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
                    logging.info(f"{output_file} downloaded successfully.")
                else:
                    logging.error(
                        f"ERROR: Failed to download file. Status code: {response.status_code}"
                    )
            else:
                logging.info(
                    f"Data for cycle '{cycles[cycle]}' of {date} is already in the database. skipping..."
                )


def load():
    """
    Validate CSVs and load them into the database. Add necessary columns:
    1. Date
    2. Cycle
    """

    csv_files_path = f"./data/OAC_TW_007933047_*.csv"
    csv_files = glob.glob(csv_files_path)
    dfs = []

    #TODO: optimize time for this
    for csv_file in csv_files:
        try:
            logging.info(f"Validating {csv_file}...")

            # loading csv into df, also converting bad types to NaN
            df = pd.read_csv(
                csv_file,
                dtype={
                    "Loc": pd.Int64Dtype,
                    "Loc Zn": str,
                    "Loc Name": str,
                    "Loc Purp Desc": str,
                    "Loc/QTI": str,
                    "Flow Ind": str,
                    "DC": pd.Int64Dtype,
                    "OPC": pd.Int64Dtype,
                    "TSQ": pd.Int64Dtype,
                    "OAC": pd.Int64Dtype,
                    "IT": str,
                    "Auth Overrun Ind": str,
                    "Nom Cap Exceed Ind": str,
                    "All Qty Avail": str,
                    "Qty Reason": str,
                },
            )
            # Check if CSV is empty:
            if df.shape[0] == 0:
                logging.warning(f"File {csv_file} is empty. Skipping...")
                continue

            # Validate the dataframe columns
            # check number of columns match (15)
            if df.shape[1] != 15:
                logging.warning(
                    f"File {csv_file} has {df.shape[1]} columns, expecting 15. Skipping..."
                )
                continue

            # check if column names match. There are specific values expected for these columns. See more here, under "Legend": https://twtransfer.energytransfer.com/ipost/TW/capacity/operationally-available#modal-oacInfo
            column_names = {
                "Loc Purp Desc": ["M2", "MQ"],
                "Loc/QTI": ["RPQ", "DPQ"],
                "Flow Ind": ["R", "D"],
                "IT": ["Y", "N"],
                "Auth Overrun Ind": ["Y", "N"],
                "Nom Cap Exceed Ind": ["Y", "N"],
                "All Qty Avail": ["Y", "N"],
            }

            # Changing invalid values to NaN
            df = df.apply(
                lambda x: x.where(x.isin(column_names[x.name]))
                if x.name in column_names
                else x
            )

            # saving Y/N response for columns to boolean
            for col in ["IT","Auth Overrun Ind","Nom Cap Exceed Ind","All Qty Avail"]:
                df[col] = df[col].map({"Y": True, "N":False})

            df["Date"] = csv_file.split("_")[-2]
            df["Cycle"] = csv_file.split("_")[-1].replace(".csv", "")
            dfs.append(df)
            
        except Exception as e:
            logging.exception(f"Failed to validate {csv_file}. Please check this file again. skipping")
            continue

    # Concat dataframes and load into database
    logging.info("Loading validated CSVs...")
    if len(dfs)==0:
        logging.warning("No data to load... End loading process")
        return 
        
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_sql(table_name, engine, if_exists="append", index=False)
    logging.info("Finished loading.")
    # TODO: Handle NaN values better

    # Clean up all loaded files
    for csv_file in csv_files:
        logging.info("Deleting files from filesystem")
        os.remove(csv_file)


if __name__ == "__main__":
    logging.info("")
    logging.info("=========================")
    logging.info(
        f"Starting the process. Today is {current_date.strftime('%m/%d/%Y')}. Downloading data of the last three days."
    )
    check_database()
    extract_data()
    load()
    logging.info("Finished process. Have a good day :)")

