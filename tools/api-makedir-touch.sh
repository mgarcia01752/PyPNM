#!/usr/bin/env bash

# Base file names to create in each route directory
FILES=("router.py" "service.py" "schemas.py")

# List of all route directories
ROUTE_DIRS=(
  "src/api/routes/system/sysdescr"
  "src/api/routes/docs/dev/eventlog"
  "src/api/routes/docs/if31/system/diplexer"
  "src/api/routes/docs/if31/ds/ofdm/profile/stats"
  "src/api/routes/docs/if31/ds/ofdm/chan/stats"
  "src/api/routes/docs/if30/ds/scqam/chan/stats"
  "src/api/routes/docs/if30/us/atdma/chan/stats"
  "src/api/routes/docs/if31/us/ofdma/chan/stats"
  "src/api/routes/docs/dev/reset"
  "src/api/routes/docs/pnm/ds/ofdm/rxmer"
  "src/api/routes/docs/pnm/ds/ofdm/fec_summary"
  "src/api/routes/docs/pnm/ds/ofdm/chan_est_coeff"
  "src/api/routes/docs/pnm/ds/histogram"
  "src/api/routes/docs/pnm/ds/ofdm/const_display"
  "src/api/routes/docs/pnm/ds/ofdm/modulation_profile"
  "src/api/routes/docs/pnm/us/ofdma/pre_equalization"
  "src/api/routes/docs/pnm/spectrumAnalyzer"
  "src/api/routes/docs/pnm/ds/ofdm/symbol_capture"
  "src/api/routes/docs/pnm/latency_report"
  "src/api/routes/system_config"
  "src/api/routes/advance/multiRxMer"
)

FILES=("router.py" "service.py" "schemas.py")

ROUTE_DIRS=(
  "src/api/routes/advance/multi_ds_chan_est"
)

echo "Creating route directories and files..."

for dir in "${ROUTE_DIRS[@]}"; do
  mkdir -p "$dir"
  for file in "${FILES[@]}"; do
    touch "$dir/$file"
  done
done

echo "All routes and files created."
