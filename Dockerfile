FROM pcic/geospatial-python

ADD . /app
WORKDIR /app

RUN pip3 install -U pip
RUN pip3 install -i https://pypi.pacificclimate.org/simple/ -r requirements.txt
RUN python3 ./setup.py install

EXPOSE 8000
ENV FLASK_APP ce.wsgi:app

CMD flask run -p 8000 --with-threads --no-reload
