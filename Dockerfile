FROM pcic/geospatial-python

RUN mkdir /app
ADD requirements.txt /app
WORKDIR /app
RUN pip3 install -U pip
RUN pip3 install -i https://pypi.pacificclimate.org/simple/ -r requirements.txt

ADD . /app/

RUN python3 ./setup.py install

EXPOSE 8000
ENV FLASK_APP ce.wsgi:app
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

CMD flask run -p 8000 -h 0.0.0.0 --no-reload
