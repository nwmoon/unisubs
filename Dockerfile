FROM ubuntu:12.04
MAINTAINER Amara "http://amara.org"

RUN (echo "deb http://archive.ubuntu.com/ubuntu precise main universe multiverse" > /etc/apt/sources.list)
RUN (echo "deb-src http://archive.ubuntu.com/ubuntu precise main universe multiverse" >> /etc/apt/sources.list)
RUN (echo "deb http://archive.ubuntu.com/ubuntu precise-updates main universe multiverse" >> /etc/apt/sources.list)
RUN (echo "deb-src http://archive.ubuntu.com/ubuntu precise-updates main universe multiverse" >> /etc/apt/sources.list)
RUN (echo "deb http://ppa.launchpad.net/mozillateam/firefox-next/ubuntu precise main" >> /etc/apt/sources.list)
RUN (echo "deb-src http://ppa.launchpad.net/mozillateam/firefox-next/ubuntu precise main" >> /etc/apt/sources.list)
RUN apt-get update
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get -y install wget python-dev python-setuptools make gcc s3cmd libmysqlclient-dev libmemcached-dev supervisor libxml2-dev libxslt-dev zlib1g-dev swig libssl-dev libyaml-dev git-core python-m2crypto subversion openjdk-6-jre libjpeg-dev libfreetype6-dev gettext build-essential gcc dialog mysql-client firefox flashplugin-installer xvfb node-uglify ruby-sass
# fix PIL
RUN ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
RUN ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
RUN ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/
ADD . /opt/apps/unisubs
RUN mkdir -p /opt/extras/pictures
RUN mkdir -p /opt/extras/videos
ENV REVISION staging
ENV APP_DIR /opt/apps/unisubs
ENV CLOSURE_PATH /opt/google-closure
RUN git clone https://github.com/google/closure-library $CLOSURE_PATH
RUN (cd $CLOSURE_PATH && git checkout adbcc8ef6530ea16bac9f877901fe6b32995c5ff)
RUN ln -sf $CLOSURE_PATH $APP_DIR/media/js/closure-library
ADD .docker/known_hosts /root/.ssh/known_hosts
ADD .docker/config_env.sh /usr/local/bin/config_env
ADD .docker/build_media.sh /usr/local/bin/build_media
ADD .docker/run_migrations.sh /usr/local/bin/run_migrations
ADD .docker/rebuild_index.sh /usr/local/bin/rebuild_index
ADD .docker/update_index.sh /usr/local/bin/update_index
ADD .docker/master-worker.sh /usr/local/bin/master-worker
ADD .docker/worker.sh /usr/local/bin/worker
ADD .docker/test_app.sh /usr/local/bin/test_app
ADD .docker/update_translations.sh /usr/local/bin/update_translations
ADD .docker/entry.sh /usr/local/bin/entry
RUN easy_install pip
RUN pip install uwsgi
RUN (cd $APP_DIR/deploy && pip install --src /opt/src/unisubs/ -r requirements.txt)
# this fixes the nose bug (https://github.com/django-nose/django-nose/issues/54)
RUN rm /usr/local/man
ADD .docker/run.sh /usr/local/bin/run

WORKDIR /opt/apps/unisubs
VOLUME /opt/apps/unisubs
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entry"]
CMD ["app"]
