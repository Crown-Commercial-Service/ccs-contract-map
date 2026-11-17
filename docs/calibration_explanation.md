# Confidence Calibration - Technical Explanation

## Overview

Confidence calibration maps **raw heuristic scores** (numbers) to **true probabilities** (0.0–1.0).
A well-calibrated model means: "When I say 80% confidence, I'm actually right 80% of the time."

---

## 1. How Text is Converted to Numbers

### Step 1: Keyword Matching → Score
The heuristic classifier counts keyword matches and assigns points:

```
Description: "Cloud hosting and storage solution with AWS infrastructure"

Category: "Cloud and Hosting"
  Primary keywords matched:
    - "cloud"        → +5 points
    - "hosting"      → +5 points
    - "storage"      → +5 points
    - "AWS"          → +5 points (also RM code bonus if applicable)
  Secondary keywords matched:
    - "solution"     → +1 point
    - "infrastructure" → +1 point

Total score: 5+5+5+5+1+1 = 22 points
```

### Step 2: Score → Raw Confidence (Before Calibration)
```python
raw_confidence = min(0.95, score / 100.0)
# Score 22 → 0.22 (22%)
# Score 87 → 0.87 (87%)
```
**Problem**: This linear mapping is NOT calibrated. A score of 22 doesn't mean 22% accuracy.

---

## 2. Does It Handle Semantic Meaning?

### Short Answer: The Heuristic Does NOT (but the LLM does)

| Component | Semantic Understanding? | How |
|-----------|------------------------|-----|
| **Heuristic (keywords)** | ❌ No | Exact word/phrase matching via regex. "Cloud hosting" matches "cloud hosting" but NOT "virtualized compute environment" |
| **LLM (fallback)** | ✅ Yes | Understands paraphrasing, synonyms, context. "Virtualized compute environment" → "Cloud and Hosting" |
| **Calibration** | N/A | Only calibrates the heuristic score, not semantic meaning |

### How the Hybrid System Compensates

```
Description: "Virtualized compute environment with elastic storage"
  ↓
Heuristic: No keyword matches → Score: 0 → Falls through to LLM
  ↓
LLM: Understands "virtualized compute" = cloud → "Cloud and Hosting" (confidence: 0.9)
  ↓
Result: LLM decision with 90% confidence
```

The heuristic catches ~78% of contracts (exact keyword matches).
The LLM handles the remaining ~22% (semantic understanding needed).

---

## 3. Calibration Algorithms Explained

### 3.1 Platt Scaling (Sigmoid Calibration)

**What it is**: Fits a logistic regression (sigmoid curve) to map scores to probabilities.

**Formula**:
```
P(correct | score) = 1 / (1 + exp(-(A * score + B)))
```
Where A and B are learned from training data.

**Visual**:
```
Probability
  1.0 ┤                    ╭──────
  0.8 ┤               ╭────╯
  0.6 ┤          ╭────╯
  0.4 ┤     ╭────╯
  0.2 ┤╭────╯
  0.0 ┤╯
      └─────────────────────────── Score
        0   20  40  60  80  100
```

**Pros**:
- Smooth, monotonic curve
- Works well with small datasets
- Parametric (only 2 parameters: A, B)
- Prevents overfitting

**Cons**:
- Assumes sigmoid shape (may not fit all data)
- Less flexible for complex score distributions

**When to use**: Small validation sets (<1000 samples), or when you want smooth predictions.

---

### 3.2 Isotonic Regression (Non-Parametric)

**What it is**: Fits a non-decreasing (monotonic) function using piecewise linear interpolation.
No assumed shape — it learns the exact mapping from data.

**Algorithm**:
1. Sort all (score, is_correct) pairs by score
2. Compute cumulative accuracy at each score level
3. Apply pool-adjacent-violators algorithm (PAVA) to ensure monotonicity
4. Interpolate between known points

**Visual**:
```
Probability
  1.0 ┤                    ╭───╮
  0.8 ┤               ╭────╯   │
  0.6 ┤          ╭────╯       │
  0.4 ┤     ╭────╯           │
  0.2 ┤╭────╯               │
  0.0 ┤╯                    ╰──
      └─────────────────────────── Score
        0   20  40  60  80  100
```
(Notice: can have flat regions and sharp jumps — learns exact data shape)

**Pros**:
- No assumed shape (fits any monotonic relationship)
- More accurate on larger datasets
- Captures complex score→probability mappings

**Cons**:
- Can overfit on small datasets
- May produce step functions (not smooth)
- Needs more data (>500 samples recommended)

**When to use**: Larger validation sets, when you want maximum accuracy.

---

## 4. Comparison Table

| Aspect | Platt Scaling | Isotonic Regression |
|--------|---------------|---------------------|
| **Shape** | Sigmoid (fixed) | Any monotonic (learned) |
| **Parameters** | 2 (A, B) | Unlimited (data-driven) |
| **Data needed** | Small (>100 samples) | Larger (>500 samples) |
| **Overfitting risk** | Low | High on small data |
| **Smoothness** | Always smooth | Can be step-like |
| **Flexibility** | Limited | High |
| **Speed** | Fast | Slower (optimization) |
| **Default in our code** | Available | ✅ **Default** |

---

## 5. Our Implementation

### Building the Calibrator
```bash
python scripts/build_calibrator.py --results-dir data/results --output calibrator.pkl
```

### What Happens Inside
```python
# 1. Load evaluation results
df = pd.read_csv("data/results/eval_keywords_llm_t10_m5.csv")

# 2. Extract (score, is_correct) pairs
scores = df["Heuristic_Score"].tolist()
labels = (df["AI_Prediction"] == df["Category"]).astype(int).tolist()

# 3. Fit isotonic regression
calibrator = IsotonicRegression(out_of_bounds='clip')
calibrator.fit(scores, labels)

# 4. Save
pickle.dump(calibrator, open("calibrator.pkl", "wb"))
```

### At Runtime
```python
# In ContractClassifier.__init__:
self.calibrator = HeuristicScoreCalibrator.load("calibrator.pkl")

# In classify():
confidence = self.calibrator.calibrate(heuristic_score)
# Score 15 → 0.723 (learned from data: 72.3% of score-15 predictions are correct)
```

---

## 6. Expected Calibration Error (ECE)

ECE measures how well calibrated your model is:

```python
def calculate_ece(y_true, y_prob, n_bins=10):
    """
    ECE = Σ (bin_size / total) * |accuracy_in_bin - confidence_in_bin|
    
    Lower is better. 0.0 = perfect calibration.
    """
    ...
```

### Interpretation
| ECE | Meaning |
|-----|---------|
| < 0.02 | Excellent (production-ready) |
| 0.02–0.05 | Good (acceptable) |
| 0.05–0.10 | Fair (needs work) |
| > 0.10 | Poor (miscalibrated) |

---

## 7. Summary

```
Text Description
  ↓
Keyword Matching → Raw Score (e.g., 22)
  ↓
Isotonic Regression → Calibrated Probability (e.g., 0.68)
  ↓
Decision: If confidence ≥ threshold → Use heuristic
          Else → Fall back to LLM
```

The calibration ensures that when the heuristic says "80% confident", it's actually right ~80% of the time, enabling reliable threshold-based routing between heuristic and LLM.