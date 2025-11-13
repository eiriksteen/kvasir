# Time Series

from typing import Literal

SUPPORTED_TASKS = [
    "time_series_forecasting",
    "time_series_classification",
    "time_series_anomaly_detection",
    "time_series_segmentation",
    "image_classification",
    "image_segmentation",
    "text_classification",
]

SUPPORTED_TASKS_LITERAL = Literal[
    "time_series_forecasting",
    "time_series_classification",
    "time_series_anomaly_detection",
    "time_series_segmentation",
    "image_classification",
    "image_segmentation",
    "text_classification",
]


TIME_SERIES_FORECASTING_GUIDELINES = """
## Model selection

In time series forecasting, simple models often perform surprisingly well. These are strong baselines:
- Linear model (AR) and ARIMA
- XGBoost with lag features and potentially date features
- Prophet by Facebook

For neural models, there have recently been proposed generalist architectures that claim to perform well, such as:
- PatchTST
- TimeXer
- TimeMixer
- iTransformer

We currently don't have access to these, but they will come. 

NB: LSTM sucks. Don't use it. 

## Evaluation

Evaluation metrics are typically MSE, MAE, RMSE, MAPE. 
Avoiding data leakage is absolutely crucial. 
A split of 70% train, 15% validation, 15% test is a good starting point. 
As always, choose hyperparameters only on the validation set. 
For autoregressive models, keep in mind we must generate test and validation predictions autoregressively, meaning we generate one prediction at a time, then feed it back into the model to generate the next prediction, all the way through the output window. 
A classic mistake is to do just one-step ahead even for the test set, as we can get away with that during training. 
Do not make this mistake as this is severe data leakage.

## Deployment and inference

After we have finished training and evaluation, we should train the model on all the data, then save the model to make it ready for inference. 
"""

TIME_SERIES_CLASSIFICATION_GUIDELINES = "Currently no guidelines"

TIME_SERIES_ANOMALY_DETECTION_GUIDELINES = "Currently no guidelines"

TIME_SERIES_SEGMENTATION_GUIDELINES = "Currently no guidelines"


# Computer Vision


IMAGE_CLASSIFICATION_GUIDELINES = "Currently no guidelines"

IMAGE_SEGMENTATION_GUIDELINES = "Currently no guidelines"


# Natural Language Processing


TEXT_CLASSIFICATION_GUIDELINES = "Currently no guidelines"


# Tabular


def get_guidelines(task: SUPPORTED_TASKS_LITERAL) -> str:
    if task == "time_series_forecasting":
        return TIME_SERIES_FORECASTING_GUIDELINES
    elif task == "time_series_classification":
        return TIME_SERIES_CLASSIFICATION_GUIDELINES
    elif task == "time_series_anomaly_detection":
        return TIME_SERIES_ANOMALY_DETECTION_GUIDELINES
    elif task == "time_series_segmentation":
        return TIME_SERIES_SEGMENTATION_GUIDELINES
    elif task == "image_classification":
        return IMAGE_CLASSIFICATION_GUIDELINES
    elif task == "image_segmentation":
        return IMAGE_SEGMENTATION_GUIDELINES
    elif task == "text_classification":
        return TEXT_CLASSIFICATION_GUIDELINES
    else:
        raise ValueError(
            f"Unknown task: {task}, supported tasks: {SUPPORTED_TASKS}")
