# http-service

Backend http service to serve ep4ever solar station web app
but you can easily turn it to something else :)

## How does it work

This http service delivers **static** content unless the uri provided begins with **/api**.
when the uri as the */api* prefix the service lookup for a so called **domain**.

For exemple /api/config will try to look for a Class (see: routes.py) called **Config** and
invoke it's *execute* implementation (class must inherit from BaseCommand).

This mecanism is needed for the solar station web app witch is a frontend first app with
REST api call to fetch datas to update & display content.

## Getting started

copy the .env.dist to **.env** and edit it to fit your needs.For example you can turn on
https by uncomenting the last five keys after having:

- generating a ssl key pair (genssl.sh)
- set SSL=1 and login / password http basic auth keys

pypoetry management is provided here only to handle dependencies. To build the service
pyinstaller is use and you must install dependencies using pip.

- install the relevant packages found in pypoetry.toml
- run python httpservice.py

> by default the service serves static content from webapp folder

