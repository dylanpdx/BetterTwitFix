FROM python:3.10-alpine AS build
RUN apk add build-base python3-dev linux-headers pcre-dev jpeg-dev zlib-dev
RUN pip install --upgrade pip
RUN pip install pillow gunicorn

FROM python:3.10-alpine AS deps
WORKDIR /twitfix
COPY requirements.txt requirements.txt
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
RUN pip install -r requirements.txt

FROM python:3.10-alpine AS runner
EXPOSE 8000
RUN apk add pcre-dev jpeg-dev zlib-dev
WORKDIR /twitfix
CMD ["gunicorn", "wsgi:app","--bind","0.0.0.0:9000"]
COPY --from=build /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY . .
