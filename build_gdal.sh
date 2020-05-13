# If we're not executing in a Travis environment, just use /tmp
if [[ -z "$TRAVIS_BUILD_DIR" ]]; then
    TRAVIS_BUILD_DIR="/tmp"
    #HOME="/tmp"
fi

if [[ -z "$GDALVERSION" ]]; then
    echo "GDALVERSION environment variable is unset. Please set it :)"
    exit 1
fi

GDALINST=$HOME/gdalinstall
GDALBUILD=$HOME/gdalbuild
CPLUS_INCLUDE_PATH=$GDALINST/include
C_INCLUDE_PATH=$GDALINST/include
CFLAGS=-I$GDALINST/include
PROJ_VERSION=6.3.2

# Trivial change to test Travis's build cache
if [[ ! -d "$GDALBUILD" ]]; then
    mkdir $GDALBUILD
fi
if [[ ! -d "$GDALINST" ]]; then
    mkdir $GDALINST
fi
pushd $GDALBUILD

wget -c -O proj-${PROJ_VERSION}.tar.gz https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz
tar -xzvf proj-${PROJ_VERSION}.tar.gz
pushd proj-${PROJ_VERSION}
./configure --prefix=${GDALINST}
make -j2 && make install
popd

wget -c -O gdal-$GDALVERSION.tar.gz http://download.osgeo.org/gdal/$GDALVERSION/gdal-$GDALVERSION.tar.gz
tar -xzf gdal-$GDALVERSION.tar.gz
cd gdal-$GDALVERSION
./configure --prefix=${GDALINST} --with-proj=${GDALINST}
make -j2
make install
popd

export PATH=$GDALINST/bin:$PATH
export LD_LIBRARY_PATH=$GDALINST/lib:$LD_LIBRARY_PATH
export GDAL_MINOR_VERSION=$(echo $GDALVERSION | sed -e "s/\\.[0-9]\+$//")
