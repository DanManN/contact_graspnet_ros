#!/usr/bin/env bash
xhost +
docker run --gpus 1 --rm -it -e DISPLAY=${DISPLAY} -v /tmp:/tmp contact-graspnet bash
