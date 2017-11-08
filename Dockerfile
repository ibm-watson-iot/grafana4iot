FROM ubuntu:16.04

# References:
# - https://github.com/kamon-io/docker-grafana-graphite
# - https://github.com/nodesource/distributions#installation-instructions
# - https://www.frlinux.eu/?p=199
# - http://graphite.readthedocs.org/en/latest/install.html
# - https://github.com/etsy/statsd/blob/master/exampleConfig.js

# =============================================================================
# Installation
# =============================================================================

ENV DEBIAN_FRONTEND noninteractive


# =============================================================================
# Install dependencies
# =============================================================================

RUN apt-get -y update
RUN apt-get -y install git wget curl nano
RUN apt-get -y install gunicorn supervisor nginx-light build-essential

RUN wget http://launchpadlibrarian.net/109052632/python-support_1.0.15_all.deb
RUN dpkg -i python-support_1.0.15_all.deb

RUN apt-get -y install python-pip python-dev \
                       python-simplejson python-cairo \
                       python-pysqlite2 python-memcache

RUN pip install 'django-tagging<0.4'

# Graphite python module dependencies
RUN pip install Twisted==11.1.0
RUN pip install Django==1.5
RUN pip install pytz

# =============================================================================
# Install Graphite, Carbon and Whisper and install
# =============================================================================
RUN mkdir /src
RUN git clone https://github.com/graphite-project/whisper.git /src/whisper &&\
    cd /src/whisper &&\
    git checkout 0.9.x &&\
    python setup.py install

RUN git clone https://github.com/graphite-project/carbon.git /src/carbon &&\
    cd /src/carbon &&\
    git checkout 0.9.x &&\
    python setup.py install


RUN git clone https://github.com/graphite-project/graphite-web.git /src/graphite-web  &&\
    cd /src/graphite-web &&\
    git checkout 0.9.x  &&\
    python setup.py install


# =============================================================================
# Install Grafana
# =============================================================================
#   wget https://grafanarel.s3.amazonaws.com/builds/grafana-2.1.3.linux-x64.tar.gz -O /src/grafana.tar.gz &&
RUN mkdir /src/grafana &&\
    mkdir /opt/grafana &&\
    wget https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana-4.6.1.linux-x64.tar.gz -O /src/grafana.tar.gz &&\
    tar -xzf /src/grafana.tar.gz -C /opt/grafana --strip-components=1 &&\
    rm /src/grafana.tar.gz


# =============================================================================
# Install Grafana auto-configurator
# =============================================================================
RUN mkdir -p /opt/grafana-autoconfig/dashboards
ADD grafana-autoconfig /opt/grafana-autoconfig/


# =============================================================================
# Configuration
# =============================================================================

# Configure Carbon and Graphite-Web
ADD graphite/webapp /opt/graphite/webapp/graphite/
ADD graphite/conf /opt/graphite/conf/

# Initialize Graphite storage
RUN mkdir -p /opt/graphite/storage/whisper
RUN touch /opt/graphite/storage/graphite.db /opt/graphite/storage/index
RUN chown -R www-data /opt/graphite/storage
RUN chmod 0775 /opt/graphite/storage /opt/graphite/storage/whisper
RUN chmod 0664 /opt/graphite/storage/graphite.db
RUN cd /opt/graphite/webapp/graphite && python manage.py syncdb --noinput

# Configure Grafana
ADD grafana/custom.ini /opt/grafana/conf/custom.ini

# Configure nginx and supervisord
ADD nginx/nginx.conf /etc/nginx/nginx.conf
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf


# =============================================================================
# Expose Ports
# =============================================================================

# Grafana
EXPOSE  80

# =============================================================================
# Run
# =============================================================================

CMD     ["/usr/bin/supervisord"]
