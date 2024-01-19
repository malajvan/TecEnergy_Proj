import time
import random

from sqlalchemy import create_engine, text
from sqlalchemy.sql import text

db_name = "TW_op_avail"
db_user = "postgres"
db_pass = "postgres"
db_host = "db"
db_port = "5432"

# Connecto to the database
db_string = "postgresql://{}:{}@{}:{}/{}".format(
    db_user, db_pass, db_host, db_port, db_name
)
engine = create_engine(db_string)


def add_new_row(n):
    with engine.connect() as conn:
        statement = text(
            f"INSERT INTO numbers(number, timestamp) VALUES ({n}, {int(round(time.time() * 1000))});")

        # Insert a new number into the 'numbers' table.
        conn.execute(statement)
        conn.commit()
        print(statement)


def get_last_row():
    # Retrieve the last number inserted inside the 'numbers'
    with engine.connect() as conn:
        query = text(
            """SELECT * FROM numbers LIMIT 10"""
        )

        result_set = conn.execute(query)
        for r in result_set:
            return r[-1]


if __name__ == "__main__":

    while True:
        add_new_row(random.randint(1, 100))
        print("The last value inserted is: {}".format(get_last_row()))
        time.sleep(5)
