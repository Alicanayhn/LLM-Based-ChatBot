FROM python:3.9

WORKDIR /llm

COPY requirements.txt /llm/requirements.txt

RUN pip install -r /llm/requirements.txt

COPY . /llm/

CMD [ "python", "app.py" ]