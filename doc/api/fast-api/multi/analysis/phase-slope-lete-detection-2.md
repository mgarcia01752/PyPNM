# Multi-Resolution Echo Detection Pipeline

This document outlines the high-level steps and supporting mathematics for implementing a multi-resolution phase-slope echo detection workflow. Each step will later map to Python functions and classes.

---

## 1. Data Ingestion

Collect $M$ independent OFDM channel-estimate snapshots, each of length $K$:

$$
H^{(m)}[k],\quad m=1,\ldots,M;\quad k=1,\ldots,K
$$

Aggregate into an array of shape $(M, K)$.

---

## 2. (Optional) Coherent Averaging

Compute a noise-reduced baseline channel estimate:

$$
\overline H[k] = \frac{1}{M}\sum_{m=1}^M H^{(m)}[k]
$$

Use $\overline H$ for subsequent steps if desired.

---

## 3. Phase-Slope Delay Estimation

For each snapshot (or $\overline H$):

1. **Phase unwrapping**:

   $$
   \phi_k = \mathrm{unwrap}\bigl(\angle H[k]\bigr)
   $$
2. **Linear fit** $\phi_k \approx a f_k + b$ via least squares:

   $$
   a = \frac{\sum_k (f_k-\bar f)(\phi_k-\bar\phi)}{\sum_k (f_k-\bar f)^2},
   \quad
   \tau_{rt} = -\frac{a}{2\pi}.
   $$
3. **One-way delay** and **distance**:

   $$
   \tau = \frac{|\tau_{rt}|}{2},
   \quad
   d = v\,\tau,\quad v = c_0\times\mathrm{prop\_speed\_frac}.
   $$

---

## 4. Per-Subcarrier Group-Delay Extraction

Estimate instantaneous group-delay per subcarrier using centered differences:

$$
\tau_k \approx -\frac{\phi_{k+1}-\phi_{k-1}}{2\pi(f_{k+1}-f_{k-1})}.
$$

---

## 5. Global Flatness Metric

Compute overall mean and standard deviation of \\(\tau\_k) across all $K$ subcarriers:

$$
\mu = \frac{1}{K} \sum_{k=1}^K \tau_k,
\quad
\sigma_{\mathrm{tot}} = \sqrt{\frac{1}{K-1} \sum_{k=1}^K (\tau_k - \mu)^2}.
$$

---

## 6. Coarse-Bin Analysis (1 MHz bins)

Partition the occupied bandwidth $B$ into $N_b = \lceil B/1\mathrm{MHz}\rceil$ bins. For each bin $j$ with subcarrier set $\mathcal{K}_j$:

$$
\mu_j = \frac{1}{|\mathcal{K}_j|} \sum_{k\in\mathcal{K}_j} \tau_k,
\quad
\sigma_j = \sqrt{\frac{1}{|\mathcal{K}_j|-1} \sum_{k\in\mathcal{K}_j} (\tau_k - \mu_j)^2},
$$

Define anomaly metric:

$$
\Delta\sigma_j = |\sigma_j - \sigma_{\mathrm{tot}}|.
$$

---

## 7. Anomaly Flagging

Mark bin $j$ as **disturbed** if

$$
\Delta\sigma_j > T,
$$

where $T$ is an empirical threshold based on baseline ripple.

---

## 8. Multi-Resolution Refinement

For each flagged 1 MHz bin:

1. Subdivide into finer bins (e.g., 500 kHz, then 100 kHz).
2. Recompute $\Delta\sigma$ in each sub-bin.
3. Continue subdividing regions exceeding $T$ until target resolution is reached.

This hierarchical strategy focuses computation on likely disturbance regions.

---

## 9. Reporting

Produce a summary of:

* Flagged frequency intervals
* Corresponding \\(\Delta\sigma) values
* Estimated one-way delays \\(\tau) and distances $d$

This report can be serialized as JSON, plotted, or integrated into monitoring dashboards.

---

**Next Steps:** Translate each step into Python modules and functions, handling data I/O, phase unwrapping, regression, binning logic, and iterative refinement.
