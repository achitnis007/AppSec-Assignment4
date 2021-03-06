FROM ubuntu:18.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV FLASK_APP=/usr/src/app.py

COPY requirements.txt /usr/src/

RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip3 install -r /usr/src/requirements.txt

COPY *.txt /usr/src/
COPY app.py /usr/src/
COPY app/ /usr/src/app/

EXPOSE 8080

# CMD ["flask", "run", "--host=0.0.0.0"]
# CMD ["python3", "/usr/src/app.py"]
