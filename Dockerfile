# CrimeSense by DevWithData — Catalyst AppSail custom runtime (Streamlit)
FROM python:3.11-slim

WORKDIR /app

# system deps for matplotlib/networkx rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 libpng16-16 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# build the synthetic crime database at image-build time (read-only at runtime)
RUN python data/generate_data.py

# Catalyst injects the port to listen on via X_ZOHO_CATALYST_LISTEN_PORT
ENV X_ZOHO_CATALYST_LISTEN_PORT=9000
EXPOSE 9000

CMD streamlit run app/app.py \
    --server.port ${X_ZOHO_CATALYST_LISTEN_PORT} \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --browser.gatherUsageStats false
