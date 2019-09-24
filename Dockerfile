FROM python:2.7

ENV SUMO_VERSION 0.32.0
ENV SUMO_HOME /opt/sumo

RUN apt-get update &&   \
  apt-get install -y    \
    cmake               \
    gcc-7               \
    g++-7               \
    libxerces-c-dev     \
    libfox-1.6-dev      \
    libgdal-dev         \
    libproj-dev         \
    libgl2ps-dev        \
    swig

# Change used gcc/g++ version from 8 (which is default) to 7
# because building SUMO fails with version 8
RUN rm /usr/bin/gcc
RUN ln -s /usr/bin/gcc-7 /usr/bin/gcc

RUN rm /usr/bin/g++
RUN ln -s /usr/bin/g++-7 /usr/bin/g++

RUN mkdir -p /opt
RUN wget http://downloads.sourceforge.net/project/sumo/sumo/version%20$SUMO_VERSION/sumo-src-$SUMO_VERSION.tar.gz
RUN tar xzf sumo-src-$SUMO_VERSION.tar.gz && \
    mv sumo-$SUMO_VERSION $SUMO_HOME && \
    rm sumo-src-$SUMO_VERSION.tar.gz
RUN cd $SUMO_HOME && ./configure && make install

# First cache dependencies
ADD ./setup.py /app/setup.py
RUN python /app/setup.py install

# Add sources
ADD ./ /app/
WORKDIR /app
CMD ["python","/app/forever.py"]