FROM python:3.5.2



WORKDIR /app

ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y ruby ruby-dev
RUN gem install bundler

ADD . /app

RUN ./manage.py install_all_govuk_assets

EXPOSE 5000
CMD ./manage.py runserver -h 0.0.0.0
