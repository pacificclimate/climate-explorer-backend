FROM pcic/geospatial-python

ADD . /app
WORKDIR /app

RUN pip3 install -U pip
RUN pip3 install -i https://pypi.pacificclimate.org/simple/ -r requirements.txt
RUN python3 ./setup.py install

EXPOSE 8000

CMD devserver.py -p 8000
