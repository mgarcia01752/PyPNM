# CmUsOfdmaPreEq — upstream OFDMA pre-equalization

Parser and helper for upstream OFDMA pre-equalization tap coefficients (CmUsOfdmaPreEq).

> **Module location**
> `src/pypnm/pnm/parser/CmUsOfdmaPreEq.py`

## Inputs

- Upstream OFDMA pre-EQ binary payload captured via the pre-equalization endpoint.

## Outputs

- `CmUsOfdmaPreEqModel.header`: capture timestamp, symbol rate, FFT size.
- `taps`: list of complex coefficients per tap (magnitude/phase).
- `group_delay`: derived values for plotting.

## Usage

```python
from pathlib import Path
from pypnm.pnm.parser.CmUsOfdmaPreEq import CmUsOfdmaPreEq

payload = Path("us_ofdma_pre_eq.bin").read_bytes()
pre_eq = CmUsOfdmaPreEq(payload)

taps = pre_eq.get_taps()
```
