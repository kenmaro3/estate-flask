FROM python:3.8

WORKDIR /app

COPY ./ /app

RUN pip install --upgrade pip wheel
RUN pip install -r requirements.txt

CMD ["python", "index.py"]
