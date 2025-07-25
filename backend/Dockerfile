FROM python:3.9

WORKDIR /llm_based_chatbot

COPY requirements.txt /llm_based_chatbot/requirements.txt

RUN pip install -r requirements.txt

COPY app.py /llm_based_chatbot/app.py

CMD [ "python", "app.py"]   