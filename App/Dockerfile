FROM python:3.12-slim
LABEL Maintainer="Shailesh.Srivastava"

WORKDIR /addnumbers
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY app /addnumbers/app

EXPOSE 9100
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9100"]