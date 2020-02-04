FROM python:latest

# Install dependencies.
ADD requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# Copy files.
COPY neko/neko.py /

CMD python ./neko.py
