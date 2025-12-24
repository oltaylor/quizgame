# DOCKERFILE FOR SERVER.PY
FROM python:3.13-slim

# install git
RUN apt-get update && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/oltaylor/charades.git .

# install server deps
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    asyncio

CMD ["python", "server.py"]
