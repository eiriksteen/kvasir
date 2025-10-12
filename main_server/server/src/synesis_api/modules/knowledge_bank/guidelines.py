

TIME_SERIES_FORECASTING_GUIDELINES = """
# Time Series Forecasting Guidelines

## 1. Problem Characterization

### Dataset Structure
- **Global forecasting**: Multiple series across entities, train jointly (assumes shared patterns)
- **Local forecasting**: Fit separate models per series (use when patterns differ significantly)

### Input/Output Dimensionality
- **Univariate**: Single variable input/output (simplest, use when variables are independent)
- **Multivariate**: Multiple variables (use when cross-variate correlations exist)
- **Channel independence**: If multivariate but variables uncorrelated, treat as separate univariate problems

### Forecast Type
- **Deterministic**: Point predictions (most common, predicts conditional mean)
- **Probabilistic**: Distribution predictions (required for uncertainty quantification, anomaly detection, risk assessment)

### Data Characteristics
- **Regular sampling**: Most models assume fixed intervals (hourly, daily, etc.)
- **Irregular sampling**: Requires specialized models - use model search with "irregular time series" query
- **Frequency**: Match output frequency to input frequency

## 2. Data Preparation

### Critical Checks
1. **Stationarity**: Check if mean/variance are stable over time
   - Non-stationary → apply differencing, detrending, or log transforms
   - Test with ADF/KPSS tests
   
2. **Missing values**: Most models require complete sequences
   - Forward/backward fill for short gaps
   - Interpolation for longer gaps
   - If pervasive, use models that handle missingness natively

3. **Outliers**: Can severely impact model training
   - Detect using IQR, z-scores, or isolation forests
   - Cap, remove, or use robust scaling methods

4. **Scaling**: Critical for deep learning, beneficial for most models
   - Standardization (mean=0, std=1): Default choice
   - Min-max scaling: When need bounded range
   - Robust scaling: When outliers present
   - **Important**: Fit scaler on train data only, transform all splits

### Feature Engineering
- **Lag features**: Previous values (t-1, t-2, ..., t-k)
- **Rolling statistics**: Moving averages, std dev over windows
- **Time-based**: Day of week, month, quarter, is_weekend, is_holiday
- **Fourier features**: For capturing seasonality
- **Exogenous variables**: External predictors (weather, events, holidays)
  - Encode categoricals: one-hot, label, or ordinal encoding

## 3. Model Selection

### Decision Tree
1. **Start simple**: AR/ARIMA, Exponential Smoothing, Prophet, XGBoost
   - Required when: Short series (<100 points), few series, need interpretability
   - Fast to train, strong baselines

2. **Consider deep learning** when:
   - Large datasets (>10K samples or >100 long series)
   - Complex cross-variate patterns
   - Global forecasting with many entities
   - Probabilistic forecasting requirements
   - Models: Transformer, N-BEATS, DeepAR, TFT, Informer

3. **Ensemble methods**: Combine multiple models for robustness
   - Different model types (statistical + ML)
   - Different lookback windows
   - Different feature sets

### Computational Constraints
- Training time budget: Favor simpler models if limited
- Inference latency: Avoid deep models if real-time required
- Memory constraints: Local models use less memory than global

## 4. Validation Strategy

### Critical Rules
1. **Never randomly shuffle** time series data for splits
2. **Always maintain temporal order**: train → validation → test
3. **Test set must be most recent data**, never used for hyperparameter tuning

### Approach 1: Sequential Split (Fast, reasonable for stable patterns)
- Split data chronologically: Train (70-80%), Val (10-15%), Test (10-15%)
- Test set should be ≥ forecast horizon length
- Include at least one full seasonal cycle in test if seasonality present
- Limitation: Single validation point, can't detect temporal degradation

### Approach 2: Time Series Cross-Validation (Preferred, more robust)
Use walk-forward or expanding window on train+val data:

```
Split 1: Train[0:60%]  → Val[60%:70%]
Split 2: Train[0:70%]  → Val[70%:80%]
Split 3: Train[0:80%]  → Val[80%:90%]
Final:   Train[0:90%]  → Test[90%:100%]
```

Advantages:
- Multiple validation points → more robust metric estimates
- Detects temporal degradation
- Better simulates production deployment
- Worth the extra computation for production models

## 5. Pipeline Construction

### Stage 1: Hyperparameter Selection
Fixed parameters (determined by requirements):
- Output columns
- Forecast horizon (default: 96 steps if not specified)
- Data frequency

Tunable parameters:
- Lookback window / input sequence length
- Input columns / features
- Model hyperparameters (learning rate, depth, regularization)
- Batch size, epochs, dropout (for DL)

Use time series CV to select best parameters. Output chosen config to variables object.

### Stage 2: Training
- Use hyperparameters from Stage 1
- **For evaluation**: Train on train+val data, evaluate on test set
- **For production**: Retrain final model on ALL data (train+val+test) - you want maximum historical context
- For local forecasting with multiple entities: train one model per entity
- Save trained model artifacts
- Generate predictions on train, validation, and test sets for evaluation

### Stage 3: Inference
- Load trained model
- Accept most recent data as input (length = lookback window)
- Output forecasts for specified horizon
- Return point predictions and/or prediction intervals (if probabilistic)

## 6. Evaluation

### Deterministic Metrics
**Scale-dependent** (compare models on same dataset):
- MSE, RMSE, MAE
- In case of multiple epochs, make sure to output the loss curve

**Scale-independent** (compare across datasets):
- MAPE: % error (undefined if y=0, biased toward low values)
- MASE: Scaled error vs naive forecast (robust, preferred)
- sMAPE: Symmetric MAPE (better than MAPE)

### Probabilistic Metrics
- **CRPS**: Continuous ranked probability score (proper scoring rule)
- **Quantile loss**: For specific quantiles (p10, p50, p90)
- **Calibration plots**: Are 90% intervals actually 90%?
- **Coverage**: Fraction of actuals within prediction intervals

### Output Requirements
Return as output variables:
- All metrics (train, val, test)
- Train/val/test forecasts
- Trained model artifacts
- Chosen hyperparameters
- Feature importance (if available)

## 7. Common Pitfalls

- Using scaling parameters from entire dataset (leakage)
- Not respecting temporal order in CV splits
- Choosing models before understanding data characteristics
- Ignoring stationarity requirements
- Using single train/val/test split (fragile estimate)
- Comparing MAPE across series with different scales
"""

# TODO: Add guidelines for other tasks, such as classification, regression, clustering, etc.
