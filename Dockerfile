FROM python:3.5.2



WORKDIR /app

ADD requirements/common.txt /app/requirements/common.txt
ADD requirements/docker.txt /app/requirements/docker.txt
RUN pip install -r requirements/docker.txt

RUN apt-get update && apt-get install -y ruby ruby-dev
RUN gem install bundler

ADD . /app

RUN ./manage.py install_all_govuk_assets

# local dev server port
EXPOSE 5000

# uWSGI port
EXPOSE 3031

CMD uwsgi --socket 0.0.0.0:3031 --manage-script-name --module=app.wsgi:app -pp=./app --processes 4 --threads 2
