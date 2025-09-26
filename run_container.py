#!/usr/bin/env python3

# NOTE: please use only standard libraries
import os
import json
import argparse
import subprocess
from pathlib import Path
from rospkg import RosPack

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-host", type=str, default="localhost", help="host name or ip-address"
    )
    parser.add_argument(
        "launch_args",
        nargs=argparse.REMAINDER,
        help="launch args in ros style e.g. foo:=var",
    )
    args = parser.parse_args()

    has_cgn = False
    has_docker = subprocess.call("which docker > /dev/null", shell=True) == 0
    if has_docker:
        r = subprocess.check_output('docker image ls --format json',shell=True)
        for line in r.decode().split('\n'):
            try:
                c = json.loads(line)
                if c['Repository'] == 'contact-graspnet':
                    has_cgn = True
                    break
            except:
                pass
    has_alt = subprocess.call("which singularity > /dev/null", shell=True) == 0

    if has_cgn:
        docker_run_command = """
        docker run \
            --rm --net=host -it --gpus 1 \
            -e QT_QPA_PLATFORM=offscreen \
            -e PYOPENGL_PLATFORM='egl' \
            -e DISPLAY=$DISPLAY -v /tmp:/tmp \
            -v $HOME/.Xauthority:/home/user/.Xauthority \
            contact-graspnet:latest \
            /bin/bash -i -c \
            "source ~/.bashrc; \
            roscd cgn_ros; \
            export ROS_IP={ip}; export ROS_MASTER={host}; export ROS_MASTER_URI=http://{host}:11311; \
            roslaunch cgn_ros grasp_server.launch"
        """.format(
            ip=os.environ['ROS_IP'] if 'ROS_IP' in os.environ else '127.0.0.1',
            host=args.host,
        )
        print(docker_run_command)
        subprocess.call(docker_run_command, shell=True)
    elif has_alt:
        rp = RosPack()
        sif_file = rp.get_path('cgn_ros') + '/contact-graspnet.sif'
        singularity_run_command = """
        singularity exec \
            --contain \
            --no-home \
            --bind /tmp:/tmp \
            --bind $HOME/.Xauthority:/home/user/.Xauthority \
            --bind dotros:/home/user/.ros \
            --env PYOPENGL_PLATFORM='egl' \
            --env DISPLAY=$DISPLAY \
            --nv \
            {sif} \
            /bin/bash -i -c "export HOME=/home/user; source /home/user/.bashrc; \
            roscd cgn_ros; \
            export ROS_IP={ip}; export ROS_MASTER={host}; export ROS_MASTER_URI=http://{host}:11311; \
            roslaunch cgn_ros grasp_server.launch"
        """.format(
            sif=sif_file,
            ip=os.environ['ROS_IP'] if 'ROS_IP' in os.environ else '127.0.0.1',
            host=args.host,
        )
        print(singularity_run_command)
        subprocess.call(singularity_run_command, shell=True)
    else:
        print(
            "Neither docker nor singularity is installed. Please install one of them."
        )
