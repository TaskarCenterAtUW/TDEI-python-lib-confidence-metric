FROM python:3.11.4
WORKDIR /code
COPY ./requirement.txt /code/requirement.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirement.txt
# Add code for confidence metrics library
COPY ./src /code/src
COPY ./test.py /code/test.py