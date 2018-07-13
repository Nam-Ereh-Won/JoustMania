#!/bin/bash

#this is for development purposes only, to stop the automattically
#running joustmania scripts
sudo supervisorctl stop joustmania
kill $(ps aux | grep 'joustmania' | awk '{print $2}')
