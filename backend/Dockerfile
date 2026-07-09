FROM python:3.10-slim

WORKDIR /app

# Copy requirements.txt to leverage Docker's layer cache
COPY requirements.txt .

# Install PyTorch CPU-only first to prevent GPU PyTorch bloat, then install remaining dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download and cache the sentence-transformers model during the build phase
# This ensures container startups are instant (less than 2 seconds) and runs 100% locally.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
