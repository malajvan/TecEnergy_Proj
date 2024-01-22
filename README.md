# TEC Energy Dev Candidate Project
##### by Hong Van Pham

### Table of contents
---

[Overview](#overview)

[Getting Started](#getting-started)
  - [Building and running](#building-and-running)
  - [Debugging and Logging](#debugging-and-logging)
  - [(Optional) Run a cron job](#optional-run-a-cron-job)
- [Deliverables](#deliverables)
  
[Documentations](#documentations)
  - [Folder structure](#folder-structure)
  - [Extra](#extra)
  - [Design choices](#design-choices)
  - [Future todos](#future-todos)
  - [Objective](#objective)

---

## Overview
A software project to download, parse, and validate natural gas shipment data from [Energy Transfer](https://twtransfer.energytransfer.com/ipost/TW/capacity/operationally-available), inserting it into a relational database. 

Main stack:
- Python (Pandas, sqlalchemy)
- PostgreSQL
- Docker


## Getting Started
Quick-start guide to setup an instance of this software.  

You'll need to install Docker to run this app. Follow the official instructions [here](https://docs.docker.com/get-docker/).
### Building and running
1. Clone this repo
   
   ```
   git clone https://github.com/malajvan/TecEnergy_Proj/```
2. Make sure Docker is running
   ```
   docker -v
   ```
3. Building and running
   ```
   # get to the correct directory
   cd TechEnergy_proj/software
   
   # build and run containers
   sudo docker compose up
   ```

    **Note:** Once the app has finished running, the `software-app` container will automatically shut down, while the `software-db` container persists. You can access the PostgreSQL database in the `software-db` container (database: `TW_op_avail`, table:`tw_data`). 
        
        ```
        # while in software-db CLI 
        psql -U postgres -d TW_op_avail
        ```

    **Note:** To re-run the software and extract more data, simply rerun the `software-app` container (or follow the steps above again.)

### Debugging and Logging
To see and follow the application, track these 2 files

1. Docker logs: For containers initializations and critical errors.
2. `software/code/app.log`: infos and warnings from the main python application. 

### (Optional) Run a cron job
To automate running the software on a schedule, quickly setup a cron job. Note that you will have to leave Docker and the containers running in the background.
```
crontab -e

# a text editor automatically opens
# add following lines at end of file

# ex: schedule to run and load everyday at 9am
0 9 * * * </abosolute/path/to>/software/code/cron/run_docker.sh 

# save and quit by pressing ESC and enter ":wq"
```


## Deliverables
- [x] "DDL of a database table(s) where the data will be inserted."

    **The create table query is presented at [`software/db/create_table.sql`](https://github.com/malajvan/TecEnergy_Proj/blob/main/software/db/create_table.sql)*

- [x] "Instructions on how to run the code in the form of a readme."

  **See "Getting Started" above*

- [x] "The code to facilitate the downloading, validation, and insertion of the data."

  **The main code is presented at [`software/code/EL.py`](https://github.com/malajvan/TecEnergy_Proj/blob/main/software/code/EL.py)*



## Documentations



### Folder structure
```
TecEnergy_Proj
├── README.md
├── data_exploration            # explore the data from API
├── software                    # Dockerized app
│   ├── code                    # Main Python code
│   │   ├── Dockerfile
│   │   ├── EL.py               # Python orchestrator code
│   │   ├── __init__.py
│   │   ├── app.log             # log file for Python code
│   │   ├── cron                # optional cron job
│   │   │   └── run_docker.sh
│   │   └── requirements.txt    # python packages
│   ├── db                      # Initialization for PostgreSQL 
│   │   ├── Dockerfile
│   │   └── create_table.sql    # DDL of the database table
│   └── docker-compose.yml      
├── tests                       # Tests (unfinished)
│   └── test_python.py
└── .github/workflows           # Github Actions jobs
    ├── docker_up_test.yml      # Test docker build and db table
    └── python_unittest.yml     
```


### Extra
Other notable details of this project:

1. **Github Actions:** 
   A Docker build check and import test for the application was deployed to Github Actions. See more under `tests/` and `.github/workflows/`, or see it in action on github.
2. **AWS EC2:** 
   This app was also deployed on an EC2 instance, with the cron job configured to run everyday at 9am. 

### Design choices
1. Database - Normalization vs. Simplicity:
   
    - I only implemented 1 single table to load these CSVs.
    - While multiple tables aid normalization, for the project's scope, we're only dealing with a single CSV format. This favors simplicity and easier maintenance. There is also no obvious complex data models and relationships.
    - For future querying: No complex joins necessary, keeping it straightforward until complexity is justified.

2. Data validations and Loading:
   - Avoids duplicates by checking for existing rows based on "Date" and "Cycle.".
   - `pandas` validates field types and checks for acceptable values.
   - Handles inconsistent data by converting non-compliant entries to "Null" and skipping incorrect files with missing columns.
   - Converts "Y/N" columns to Boolean for consistency.
   - Ensures data adheres to PostgreSQL table constraints during loading.
  
  - Decision rationale: Prioritizes accuracy and data consistency over speed, terminating after attempting to load all available data. 

### Future todos
Despite completing the app, time constraints prevented me from implementing some planned enhancements:

- **Extensive Python Unittests**: I intended to create a thorough suite for enhanced reliability.
- **Code Linter**: A linter would have ensured code consistency and readability.
- **Configurability**: I aimed to add more options for increased flexibility and reusability.
- **Enhanced Error Handling**: Although basic handling is in place, I planned more extensive coverage for a broader range of scenarios.
- **Integrated scheduler**: Better implementation of the cron job so that there's no need for manual setup.

### Objective
Below is the requirements given by TEC Energy (for reference purpose)

```
TEC Energy Dev Candidate Project:

Objective:

The objective of this project is to create a software project which when launched will download CSVs from the internet, parse and validate the data contained in the CSVs and then insert it into a relational database.

The CSVs describe the shipment of natural gas. There are CSVs published multiple times a day (each day is divided into cycles). When launched the program should download, parse and insert the data available from the last three days.

Deliverables:

- DDL of a database table(s) where the data will be inserted. (Postgres SQL preferred, but any relational DB is okay)

- The necessary query(s) to insert this data.

- The code to facilitate the downloading, validation, and insertion of the data. C# and Python are our preferred languages but feel free to use something else if you would feel more comfortable.

- Instructions on how to run the code in the form of a readme.

The deliverables should all be uploaded to a public git repository (like GitHub)

The site where the data is found:
https://twtransfer.energytransfer.com/ipost/TW/capacity/operationally-available

An example url that can be used to download the CSV over HTTP:
https://twtransfer.energytransfer.com/ipost/capacity/operationally-available?f=csv&extension=csv&asset=TW&gasDay=01%2F18%2F2024&cycle=3&searchType=NOM&searchString=&locType=ALL&locZone=ALL ```
```