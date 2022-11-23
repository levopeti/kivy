# sudo docker build -t kivy_test -f docker_test.dockerfile . (--force-rm)
# sudo docker run -it --rm kivy_test

FROM ubuntu:18.04
ENV PYTHONIOENCODING="utf8"

RUN dpkg --add-architecture i386
RUN apt-get update
RUN apt-get upgrade
RUN apt-get -y install libltdl-dev libffi-dev libssl-dev autoconf autotools-dev
# RUN apt-get install -y python3.8 python3.8-dev python3.8-distutils python3.8-venv

RUN apt-get install libltdl-dev libffi-dev libssl-dev autoconf autotools-dev

RUN apt-get install -y python3-pip
RUN apt-get install -y \
    python-pip \
    build-essential \
    git \
    python \
    python3-dev \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev

RUN pip3 install --upgrade setuptools
RUN pip3 install wheel numpy cython
RUN pip3 install --upgrade cython
RUN pip3 install kivy

RUN apt-get install -y \
    build-essential \
    ccache \
    libncurses5:i386 \
    libstdc++6:i386 \
    libgtk2.0-0:i386 \
    libpangox-1.0-0:i386 \
    libpangoxft-1.0-0:i386 \
    libidn11:i386 \
    python2.7 \
    python2.7-dev \
    openjdk-8-jdk \
    zip \
    unzip \
    zlib1g-dev \
    zlib1g:i386 \
    libltdl-dev \
    libffi-dev \
    libssl-dev \
    libtool \
    autoconf \
    automake \
    pkgconf \
    autotools-dev \
    cmake

RUN mkdir -p ~/buildozer-repo
WORKDIR ~/buildozer-repo
RUN git clone https://github.com/kivy/buildozer.git
WORKDIR buildozer
RUN python3 setup.py install
WORKDIR /

# git clone https://github.com/levopeti/kivy.git
# git clone https://github.com/levopeti/stroke_prediction.git
# sudo docker cp <containerId>:/file/path/within/container /host/path/target
# android.permissions = BLUETOOTH_ADMIN,BLUETOOTH
# buildozer -v android debug
