FROM tensorflow/tensorflow:2.2.2-gpu

ARG DEBIAN_FRONTEND=noninteractive

ENV CPU_NR 8
ENV SQLITE_VERSION 3340000
ENV SQLITE_YEAR 2020
ENV LIBTIFF_VERSION 4.2.0
ENV LIBGEOTIFF_VERSION 1.6.0
ENV XERCES_VERSION 3.2.3
ENV GEOS_VERSION 3.9.1
ENV PROJ_VERSION 7.2.1
ENV GDAL_VERSION 3.2.1
ENV JEOLIB_VERSION 1.0.2

RUN apt-get update

# create temporary dir for compilations
RUN mkdir /tmp/src

# install basic stuff
RUN apt-get install apt-utils -y
RUN apt-get install wget pkg-config bash-completion -y
RUN apt-get install build-essential libtool m4 automake -y
RUN apt-get install libz-dev openssl libssl-dev swig libcurl4-gnutls-dev -y

ENV PYTHONPATH /usr/local/lib/python3.6/dist-packages:/usr/local/lib/python3/dist-packages

# install sqlite
RUN cd /tmp/src && \
    wget https://sqlite.org/${SQLITE_YEAR}/sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    tar -xzf sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    cd sqlite-autoconf-${SQLITE_VERSION} && \
    ./configure --prefix=/usr/local && \
    make -j${CPU_NR} && \
    make install

# install libtiff
RUN cd /tmp/src && \
    wget https://download.osgeo.org/libtiff/tiff-${LIBTIFF_VERSION}.tar.gz && \
    tar -xzf tiff-${LIBTIFF_VERSION}.tar.gz && \
    cd tiff-${LIBTIFF_VERSION} && \
    ./configure --prefix=/usr/local && \
    make -j${CPU_NR} && \
    make install

# install PROJ
RUN cd /tmp/src && \
    wget https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz && \
    tar -zvxf proj-${PROJ_VERSION}.tar.gz && \
    cd proj-${PROJ_VERSION} && \
    ./configure --disable-dependency-tracking && \
    make -j${CPU_NR} && \
    make install

# install xerces
RUN cd /tmp/src && \
    wget https://github.com/apache/xerces-c/archive/v${XERCES_VERSION}.tar.gz -O xerces-c-${XERCES_VERSION}.tar.gz && \
    tar -zxvf xerces-c-${XERCES_VERSION}.tar.gz && \
    cd xerces-c-${XERCES_VERSION} && \
    ./reconf && \
    ./configure && \
    make -j${CPU_NR} && \
    make install

# install geotiff
RUN cd /tmp/src && \
    wget -q https://github.com/OSGeo/libgeotiff/releases/download/${LIBGEOTIFF_VERSION}/libgeotiff-${LIBGEOTIFF_VERSION}.tar.gz && \
    tar -xzf libgeotiff-${LIBGEOTIFF_VERSION}.tar.gz && \
    cd libgeotiff-${LIBGEOTIFF_VERSION} && \
    ./configure --prefix=/usr/local --with-libtiff=/usr/local && \
    make -j${CPU_NR} && \
    make install

# install geos
RUN cd /tmp/src && \
    wget http://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2 && \
    bunzip2 geos-${GEOS_VERSION}.tar.bz2 && \
    tar xvf  geos-${GEOS_VERSION}.tar && \
    cd geos-${GEOS_VERSION} && \
    ./configure && \
    make -j${CPU_NR} && \
    make install

# install GDAL
RUN cd /tmp/src && \
    wget http://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz && \
    tar -zvxf gdal-${GDAL_VERSION}.tar.gz && \
    cd gdal-${GDAL_VERSION} && \
    ./configure --prefix=/usr/local --with-threads \
    --with-libtiff=/usr/local --with-geotiff=/usr/local --with-jpeg=internal --with-sqlite3 \
    --with-gif=internal --with-png=internal --with-libz=/usr --with-python -with-proj=/usr/local \
    --with-xerces --with-geos --with-curl=/usr/bin/curl-config && \
    make -j${CPU_NR} && \
    make install && \
    ldconfig

# install pip dependecies
COPY requirements.txt /tmp/src/requirements.txt
RUN pip install -r /tmp/src/requirements.txt

# install mialib dependencies
RUN apt-get install -yq \
    libgsl-dev \
    libgsl0-dev \
    libfann-dev \
    libfftw3-dev \
    libjsoncpp-dev \
    uthash-dev \
    doxygen \
    libshp-dev

# install mialib
RUN cd /tmp/src/ && \
    git clone https://github.com/pesekon2/jeolib-miallib.git && \
    cd jeolib-miallib && \
    git checkout phd_necessary_changes && \
    make generic && \
    make install-generic

# install jiplib dependencies
RUN apt-get install cmake libboost-filesystem-dev libboost-serialization-dev python3-numpy -y

# install jiplib
RUN cd /tmp/src && \
    wget https://github.com/ec-jrc/jeolib-jiplib/archive/${JEOLIB_VERSION}.tar.gz -O jeolib-jiplib-${JEOLIB_VERSION}.tar.gz && \
    tar -zvxf jeolib-jiplib-${JEOLIB_VERSION}.tar.gz && \
    cd jeolib-jiplib-${JEOLIB_VERSION} && \
    mkdir build && \
    cd build && \
    cmake .. -DCMAKE_MODULE_PATH=/tmp/src/jeodpp-packages/jiplib/ && \
    make -j${CPU_NR} && \
    make install

# install pyJEO
RUN cd /tmp/src && \
    wget https://github.com/ec-jrc/jeolib-pyjeo/archive/${JEOLIB_VERSION}.tar.gz -O jeolib-pyjeo-${JEOLIB_VERSION}.tar.gz && \
    tar -zxvf jeolib-pyjeo-${JEOLIB_VERSION}.tar.gz && \
    cd jeolib-pyjeo-${JEOLIB_VERSION} && \
    python setup.py install

# clean the mess
RUN rm -r /tmp/src

CMD ["bash"]
