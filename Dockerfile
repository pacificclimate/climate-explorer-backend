FROM pcic/geospatial-python

ADD . /app
WORKDIR /app

RUN pip3 install -U pip
RUN pip3 install --trusted-host tools.pacificclimate.org -i http://tools.pacificclimate.org/pypiserver/ -e .

EXPOSE 8000

CMD python3 scripts/devserver.py -p 8000 -t