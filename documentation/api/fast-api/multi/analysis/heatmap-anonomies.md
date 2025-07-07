# Anomaly Detection in 2D Arrays

This guide describes a pipeline for detecting and localizing anomalous regions in a 2D numerical array (e.g., a heat map) by thresholding its global z-score and extracting bounding boxes around connected anomalies.

---

## Mathematical Formulation

Given an `M x N` array of values `X[i,j]`:

1. **Global Mean**:

   ```
   μ = (1 / (M * N)) * Σ(i=1 to M) Σ(j=1 to N) X[i,j]
   ```

2. **Global Standard Deviation**:

   ```
   σ = sqrt((1 / (M * N)) * Σ(i=1 to M) Σ(j=1 to N) (X[i,j] - μ)^2)
   ```

3. **Z-Score Map**:

   ```
   z[i,j] = (X[i,j] - μ) / σ
   ```

4. **Anomaly Mask** (for threshold `T`):

   ```
   mask[i,j] = 1 if |z[i,j]| > T, else 0
   ```

5. **Bounding Box Extraction** for each connected component (4‑connectivity):

   ```
   row_min = min{i where mask[i,j] = 1}
   row_max = max{i where mask[i,j] = 1}
   col_min = min{j where mask[i,j] = 1}
   col_max = max{j where mask[i,j] = 1}
   ```

---

## JSON Output Format

The detection function returns a JSON object with the threshold and a list of bounding boxes:

```json
{
  "threshold": 3.0,
  "boxes": [
    { "row_min": 10, "col_min": 20, "row_max": 12, "col_max": 22 },
    { "row_min": 35, "col_min": 40, "row_max": 37, "col_max": 42 }
  ]
}
```

* `threshold`: z-score cutoff `T`
* `boxes`: array of detected regions with top-left `(row_min, col_min)` and bottom-right `(row_max, col_max)` coordinates

---

## Algorithm Steps

1. **Compute statistics**

   * Calculate global mean `μ` and standard deviation `σ`.

2. **Create anomaly mask**

   * Compute z-score map and apply threshold `T`.

3. **Connected-component labeling**

   * Identify distinct anomaly clusters using 4‑connectivity.

4. **Extract bounding boxes**

   * For each cluster, compute `min`/`max` row and column indices.

5. **Return results**

   * Return `threshold` and all bounding boxes in JSON.

---

> 💡 **Tip:** Choose the threshold `T` based on expected noise (e.g., 3–4 standard deviations). Use 8‑connectivity if you want diagonally-connected anomalies grouped together.
