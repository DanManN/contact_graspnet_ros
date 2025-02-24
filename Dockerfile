FROM rwthika/ros-cuda:noetic-desktop-full

RUN useradd user && \
	echo "user ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/user && \
	chmod 0440 /etc/sudoers.d/user && \
	mkdir -p /home/user && \
	chown user:user /home/user && \
	chsh -s /bin/bash user

RUN echo 'root:root' | chpasswd
RUN echo 'user:user' | chpasswd

# setup environment
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
# RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F42ED6FBAB17C654
# RUN apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub
RUN apt update && apt upgrade curl wget cmake gdb git python3-dev cuda-nvcc-11-4 libcudnn8 -y && \
	apt download libcublas-12-0 && \
	mkdir contents && \
	dpkg-deb -xv $(ls | grep libcublas-12-0*.deb) contents/ && \
	mv contents/usr/local/cuda-12.0/targets/x86_64-linux/lib/* /usr/local/cuda/lib64/ && \
	rm -rf contents && \
	rm -rf /var/lib/apt/lists/*

USER user
SHELL ["/usr/bin/bash", "-ic"]
ENV PATH=/home/user/miniconda3/bin:$PATH

RUN mkdir -p ~/miniconda3 && \
	wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh && \
	bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && \
	rm ~/miniconda3/miniconda.sh && \
	conda init

RUN conda create -n contact_graspnet_env \
	python=3.9 \
	cudatoolkit=11.8 \
	cudnn \
	pip

# RUN conda activate contact_graspnet_env && \
# 	pip uninstall -y tensorflow-gpu && \
# 	pip install -U tensorflow

RUN conda activate contact_graspnet_env && \
	pip uninstall em && \
	pip install empy==3.3.4 rospkg catkin-pkg transformations \
	tensorflow==2.5 \
	opencv-python-headless==4.9.0.80 \
	pyrender==0.1.45 \
	pyyaml==6.0.1 \
	tqdm==4.66.1 \
	configobj \
	pyqt5 \
	https://github.com/enthought/mayavi/zipball/main

WORKDIR /home/user/

# RUN git clone https://github.com/NVlabs/contact_graspnet.git && \
RUN git clone https://github.com/tlpss/contact_graspnet.git && \
	cd contact_graspnet && \
	conda activate contact_graspnet_env && \
	sh compile_pointnet_tfops.sh

########################################
########### WORKSPACE BUILD ############
########################################
# Installing catkin package
RUN mkdir -p /home/user/cgn_ws/src
COPY --chown=user . /home/user/cgn_ws/src/cgn_ros
RUN mv /home/user/contact_graspnet /home/user/cgn_ws/src/cgn_ros
RUN source /opt/ros/noetic/setup.bash && \
	conda activate contact_graspnet_env && \
	cd /home/user/cgn_ws && catkin_make

########################################
########### ENV VARIABLE STUFF #########
########################################
RUN echo "source ~/cgn_ws/devel/setup.bash" >> ~/.bashrc && \
	echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc && \
	echo "conda activate contact_graspnet_env" >> ~/.bashrc

WORKDIR /home/user/cgn_ws/src/cgn_ros

CMD ["bash"]
