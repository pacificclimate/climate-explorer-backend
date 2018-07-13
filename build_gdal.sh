# If we're not executing in a Travis environment, just use /tmp
if [[ -z "$TRAVIS_BUILD_DIR" ]]; then
    TRAVIS_BUILD_DIR="/tmp"
    HOME="/tmp"
fi

GDALINST=$HOME/gdalinstall
GDALBUILD=$HOME/gdalbuild
GDALVERSION="2.3.1"
CPLUS_INCLUDE_PATH=$GDALINST/include
C_INCLUDE_PATH=$GDALINST/include
CFLAGS=-I$GDALINST/include

mkdir $GDALBUILD
mkdir $GDALINST
pushd $GDALBUILD
wget http://download.osgeo.org/gdal/$GDALVERSION/gdal-$GDALVERSION.tar.gz
tar -xzf gdal-$GDALVERSION.tar.gz
cd gdal-$GDALVERSION
./configure --prefix=$GDALINST
make -j2
make install
popd

export PATH=$GDALINST/bin:$PATH
export LD_LIBRARY_PATH=$GDALINST/lib:$LD_LIBRARY_PATH
export GDAL_MINOR_VERSION=$(echo $GDALVERSION | sed -e "s/\\.[0-9]\+$//")
