FROM python:3.8
ENV PYTHONUNBUFFERED=1
WORKDIR /pardot-filter
COPY ./pardot-f/requirements.txt /pardot-filter/
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY ./pardot-f/. /pardot-filter/

EXPOSE 8055
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]