FROM python:3.11-slim

WORKDIR /sandbox

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash sandbox \
    && chown -R sandbox:sandbox /sandbox

USER sandbox

COPY --chown=sandbox:sandbox sandbox_policy.json /sandbox/sandbox_policy.json

CMD ["sleep", "infinity"]
