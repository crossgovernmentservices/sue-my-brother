FROM python:3.5.2



WORKDIR /app

ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y ruby ruby-dev
RUN gem install bundler

ADD . /app

RUN ./manage.py install_all_govuk_assets

# local dev server port
EXPOSE 5000

# uWSGI port
EXPOSE 3031

CMD uwsgi --socket 0.0.0.0:3031 --manage-script-name --module=wsgi:app -pp=./app --processes 4 --threads 2
