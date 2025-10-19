# Phase‑Slope Echo Detection: Theory, Implementation, and Usage

This guide presents the mathematical foundation, class API, and practical usage of the `PhaseSlopeEchoDetector`, which estimates echo delays and reflector distances from OFDM channel estimates.


## 1. Theory and Justification

A simple two‑path channel (direct path + reflection) has the frequency response:

$$
H(f) = H_0 \,+\, H_1 \;e^{-j2\pi f\tau_{rt}},
$$

where $\tau_{rt}$ is the **round‑trip** delay of the echo. Taking the complex phase:

$$
\varphi(f) = \arg H(f) \approx -2\pi f\,\tau_{rt} + \text{constant}.
$$

Sampling at subcarrier frequencies $f_k$ and unwrapping:

$$
\phi_k = \mathrm{unwrap}\bigl(\angle H[f_k]\bigr),
$$

we perform a linear fit:

$$
\phi_k \approx a\,f_k + b,
$$

with slope:

$$
a = \frac{d\phi}{df} \approx -2\pi\,\tau_{rt},
\quad\Longrightarrow\quad
\tau_{rt} = -\frac{a}{2\pi}.
$$

The **one‑way** delay is

$$
\tau = \frac{|\tau_{rt}|}{2},
$$

and the distance to the reflector is

$$
d = v \,\tau,
$$

where $v = c_0 \times \mathrm{prop\_speed\_frac}$ is the propagation velocity (fraction of the speed of light).


## 2. Class API

The `PhaseSlopeEchoDetector` exposes a simple interface for delay estimation:

```python
class PhaseSlopeEchoDetector:
    def __init__(
        self,
        H: array-like,
        f: Sequence[float],
        prop_speed_frac: float = 0.87
    ):
        """
        Parameters:
        -----------
        H : array-like
            Channel estimates per subcarrier (shape: \(K\), or \((M,K)\), or \((...,K,2)\) for real/imag pairs).
        f : Sequence[float]
            Subcarrier frequencies in Hz (length \(K\)).
        prop_speed_frac : float
            Fraction of light speed for wave propagation (default 0.87).
        """

    def estimate_delay(self) -> float:
        """Return the signed round‑trip delay \(\tau_{rt}\) in seconds."""

    def detect_echo(self) -> dict:
        """
        Perform detection and return:
          - `delay_rt_s`: signed round‑trip delay (s)
          - `delay_s`: positive one‑way delay (s)
          - `distance_m`: one‑way distance to reflector (m)
        """

    def dataset_info(self) -> dict:
        """Return metadata: `{ 'subcarriers': K, 'snapshots': M }`."""

    def to_dict(self) -> dict:
        """Return a comprehensive dict of inputs, parameters, and results."""
```


## 3. Practical Usage

1. Compute the phase slope:

   ```python
   detector = PhaseSlopeEchoDetector(H, f, prop_speed_frac=0.9)
   results = detector.detect_echo()
   ```
2. Inspect `results['delay_s']` and `results['distance_m']` for one‑way delay and reflector distance.
3. Use `detector.to_dict()` to serialize full inputs and outputs for logging or further analysis.


## 4. References

1. **Delay Estimation via Phase Slope** — DSPRelated.com
2. **Multipath Channel Models and Rake Receivers** — WirelessPi


> **Tip:** Ensure phase unwrapping is robust (e.g., via `numpy.unwrap`) before fitting. Small frequency spacing improves delay resolution.
