# Automatic PNM Endpoint Fetcher

Use this guide to auto-discover and invoke all SNMP-based PNM endpoints under `/docs/pnm/...` in your FastAPI service with a simple helper script.

---

## 🚀 Usage

1. **Set environment variables** (or substitute values directly):

   ```bash
   export URL="http://localhost:8000/docs/pnm/us_ofdma_pre_eq"
   export MAC="aabb.ccdd.eeff"
   export INET="192.168.100.1"
   export COMMUNITY="private"
   export OUT="responses.json"
   ```

2. **Run the fetcher script** from your project root:

   ```bash
   ./src/pypnm/examples/fast-api/fast-api-fetcher.sh \
     --url "$URL" \
     --mac "$MAC" \
     --inet "$INET" \
     --v2c "$COMMUNITY" \
     --output "$OUT"
   ```

3. **Review** the output JSON file (`responses.json`) to see the combined responses.

> **Tip:** View all `/docs/pnm/...` endpoints in your Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs) or see the FastAPI overview: [API Reference](../api/fast-api/index.md).

---

## 📂 Script Location

The helper script lives here:

```
src/pypnm/examples/fast-api/fast-api-fetcher.sh
```

Open it at: [fast-api-fetcher.sh](../../src/pypnm/examples/fast-api/fast-api-fetcher.sh)
