FROM python:3.12-slim-bookworm
WORKDIR /code
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN mkdir data
COPY EL.py EL.py
CMD ["python", "-u", "EL.py"]