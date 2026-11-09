FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY dukan_drishti ./dukan_drishti
ENV PORT=8080 PYTHONUNBUFFERED=1
EXPOSE 8080
HEALTHCHECK CMD python -c "import urllib.request,os;urllib.request.urlopen('http://localhost:'+os.environ.get('PORT','8080')+'/api/health')"
CMD ["python", "-m", "dukan_drishti", "serve"]
