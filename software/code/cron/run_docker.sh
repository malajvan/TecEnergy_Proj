#!/bin/bash

# Start the python app container to run the process
sudo $(which docker) start software-app-1


### Setting up cron job (everyday at 9am): 
### crontab -e
### 0 9 * * * /path/to/run_docker.sh 
