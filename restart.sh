#!/bin/ash
docker stop $1
docker rm $1
docker run -d --name $1 --restart always --env-file $1_env ety001/btsbots-cli