#!/bin/bash

# Start the python app container to run the process
$(which docker) start software-app-1


### Setting up cron job (everyday): 
### crontab -e
### 0 0 * * * /path/to/run_docker.sh 
