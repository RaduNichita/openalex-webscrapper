FROM ubuntu:22.04

ADD . .

RUN apt-get update

RUN apt-get -y install libssl3

RUN apt-get -y install wget libssl-dev

RUN apt-get --assume-yes install xfonts-75dpi xfonts-base fontconfig libjpeg-turbo8 libx11-6 libxext6 libxrender1



#install libssl1.1
RUN wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb
RUN dpkg -i libssl1.1_1.1.1f-1ubuntu2_amd64.deb


# install wkhtmltopdf
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb
RUN dpkg -i wkhtmltox_0.12.5-1.bionic_amd64.deb
RUN apt install -y xvfb

RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN apt-get -y -q install wkhtmltopdf

RUN apt-get install -y python3 python3-pip

RUN pip3 install --upgrade pip

RUN pip install -r requirements.txt

CMD ["python3", "main.py"]