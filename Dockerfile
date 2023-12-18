FROM python:3.11
ADD . /src
RUN pip install kopf
CMD kopf run /src/controller.py --verbose
