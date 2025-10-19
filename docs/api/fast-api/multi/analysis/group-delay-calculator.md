# Group Delay Calculator Guide

This guide explains the mathematical foundation and usage of the `GroupDelayCalculator` class for computing group delay from per-subcarrier complex channel estimates, supporting multi-snapshot coherent averaging and comprehensive output via `to_dict()`.


## 1. Group Delay: Continuous Definition

For a frequency response $H(f)$, the **group delay** is defined as:

$$
\tau_g(f) = -\frac{d}{d\omega} \arg\bigl(H(f)\bigr),
$$

where $\omega = 2\pi f$ and $\arg(H(f))$ is the phase of $H(f)$.


## 2. Discrete Approximation

Given $K$ subcarriers at frequencies $f_k$ with unwrapped phases

$$
\phi_k = \mathrm{unwrap}\bigl(\angle H[k]\bigr),
$$

the discrete group delay per subcarrier is approximated by finite differences:

* **Forward difference** at $k=0$:

  $$
  \tau_g[0] = -\frac{\phi_1 - \phi_0}{2\pi(f_1 - f_0)}
  $$

* **Central difference** for $1 \le k \le K-2$:

  $$
  \tau_g[k] = -\frac{\phi_{k+1} - \phi_{k-1}}{2\pi(f_{k+1} - f_{k-1})}
  $$

* **Backward difference** at $k=K-1$:

  $$
  \tau_g[K-1] = -\frac{\phi_{K-1} - \phi_{K-2}}{2\pi(f_{K-1} - f_{K-2})}
  $$


## 3. Multi-Snapshot Coherent Averaging

To reduce noise, average $M$ snapshots of channel estimates $H^{(m)}[k]$ coherently:

$$
\overline{H}[k] = \frac{1}{M} \sum_{m=1}^{M} H^{(m)}[k].
$$

Compute group delay on $\overline{H}[k]$ using the discrete formulas above. Alternatively, compute $\tau_g^{(m)}[k]$ per snapshot and take the median:

$$
\tau_{g,\mathrm{med}}[k] = \mathrm{median}\bigl\{\tau_g^{(1)}[k],\dots,\tau_g^{(M)}[k]\bigr\}.
$$


## 4. Class API

```python
from pypnm import GroupDelayCalculator

# H: array of shape (M, K) or (K,) for single snapshot
# freqs: array of length K with subcarrier frequencies in Hz
calc = GroupDelayCalculator(H, freqs)
```

* **`compute_group_delay_full() -> (freqs, tau_g)`**
  Compute group delay for each subcarrier:

  * `freqs`: $K$-length array of frequencies.
  * `tau_g`: $K$-length array of delays in seconds.

* **`snapshot_group_delay() -> np.ndarray`**
  Returns an $(M, K)$ array of group delays per snapshot.

* **`median_group_delay() -> (freqs, tau_med)`**
  Compute the median group delay across snapshots:

  * `freqs`: $K$-length array.
  * `tau_med`: $K$-length median delays.

* **`dataset_info() -> dict`**
  Returns metadata:

  ```json
  {"subcarriers": K, "snapshots": M}
  ```

* **`to_dict() -> dict`**
  Returns a dictionary containing:

  * `dataset_info`
  * `freqs`, `H_raw`, `H_avg`
  * `group_delay_full`: `{ "freqs": [...], "tau_g": [...] }`
  * `snapshot_group_delay`: `[[...], ...]`
  * `median_group_delay`: `{ "freqs": [...], "tau_med": [...] }`


## 5. Usage Example

```python
import numpy as np
from pypnm import GroupDelayCalculator

# Simulate two snapshots of a two-tap channel
K = 6
freqs = np.linspace(5e6, 6e6, K)
tau_true = 1e-7
H1 = 1 + 0.5*np.exp(-1j*2*np.pi*freqs*tau_true)
H2 = 1 + 0.6*np.exp(-1j*2*np.pi*freqs*(tau_true+1e-9))
Hs = np.vstack([H1, H2])  # shape (2, K)

calc = GroupDelayCalculator(Hs, freqs)

# Full group delay per subcarrier
freqs_full, tau_full = calc.compute_group_delay_full()

# Per-snapshot delays
taus = calc.snapshot_group_delay()

# Median group delay
freqs_med, tau_med = calc.median_group_delay()

# Dataset info and all data
data = calc.to_dict()

print("Full delays:", tau_full)
print("Median delays:", tau_med)
print("Dataset info:", data['dataset_info'])
```

The `to_dict()` output can be serialized to JSON for logging or API responses.
