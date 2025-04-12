import numpy as np
from scipy import stats
import statsmodels.api as sm
from typing import List
from sklearn.decomposition import PCA
from pydantic_ai import RunContext, Tool
from .deps import EDADepsBasic, EDADepsAdvanced


def check_missing_values(ctx: RunContext[EDADepsBasic]) -> str:
    """
    Check for missing values in the df in the context.

    Parameters:
    ctx (RunContext[str]): The context of the current call (contains a dataframe).

    Returns:
    str: A textual representation of the count of missing values for each column.
    """
    df = ctx.deps.df
    missing_values = df.isnull().sum()

    return "Missing values:" + missing_values.to_string()


def correlation_matrix(ctx: RunContext[EDADepsBasic], method: str = 'pearson') -> str:
    """
    Compute the correlation matrix for the df in the context.

    Parameters:
    ctx (RunContext[str]): The context of the current call (contains a dataframe).
    method (str): The method to use for computing the correlation matrix ('pearson', 'kendall', or 'spearman').

    Returns:
    str: A textual representation of the correlation matrix.
    """
    df = ctx.deps.df
    corr_matrix = df.corr(method=method)

    return "Correlation matrix:" + corr_matrix.to_string()


def moments_of_distribution(ctx: RunContext[EDADepsBasic], column: str) -> str:
    """
    Compute the moments of distribution (mean, variance, skewness, kurtosis) for a specific column in the df in the context.

    Parameters:
    ctx (RunContext[str]): The context of the current call.
    column (str): The column to compute the moments of distribution for.

    Returns:
    str: A textual representation of the moments of distribution.
    """
    df = ctx.deps.df
    mean = df[column].mean()
    variance = df[column].var()
    skewness = df[column].skew()
    kurtosis = df[column].kurt()

    return (f'Moments of distribution for {column}:\n'
            f'Mean: {mean}\n'
            f'Variance: {variance}\n'
            f'Skewness: {skewness}\n'
            f'Kurtosis: {kurtosis}')


def summary_statistics(ctx: RunContext[EDADepsBasic]) -> str:
    """
    Compute summary statistics of the df in the context.

    Parameters:
    ctx (RunContext[str]): The context of the current call (contains a dataframe).

    Returns:
    str: A textual representation of the summary statistics for each group.
    """
    df = ctx.deps.df
    summary_stats = df.describe()

    return summary_stats.to_string()


def summary_statistics_grouped(ctx: RunContext[EDADepsBasic], group_by: str):
    """
    Compute summary statistics for each group in the df in the context after grouping by the specified column.

    Parameters:
    ctx (RunContext[str]): The context of the current call (contains a dataframe).
    group_by (str): The column to group by.

    Returns:
    str: A textual representation of the summary statistics for each group.
    """
    df = ctx.deps.df
    grouped = df.groupby(group_by)
    summary_stats = grouped.describe()

    return summary_stats.to_string()


def check_outliers(ctx: RunContext[EDADepsBasic], column: str, method: str = 'iqr') -> str:
    """
    Check for outliers in a specific column of the df in the context using the specified method.

    Parameters:
    ctx (RunContext[str]): The context of the current call (contains a dataframe).
    column (str): The column to check for outliers.
    method (str): The method to use for detecting outliers ('iqr' or 'zscore').

    Returns:
    str: A textual representation of the number and percentage of outliers.
    """
    df = ctx.deps.df
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = (df[column] < lower_bound) | (df[column] > upper_bound)
    elif method == 'zscore':
        z_scores = np.abs(stats.zscore(df[column].dropna()))
        outliers = z_scores > 3
    else:
        raise ValueError("Method must be 'iqr' or 'zscore'")

    num_outliers = outliers.sum()
    total_points = len(df[column])
    percent_outliers = (num_outliers / total_points) * 100

    return (f'Number of outliers in {column}: {num_outliers}\n'
            f'Percentage of outliers in {column}: {percent_outliers:.2f}%')


def regression(ctx: RunContext[EDADepsAdvanced], endo: str, exo: List[str]) -> str:
    """
    Runs an ordinary least squares regression.

    Parameters:
    ctx (RunContext[str]): The context of the current call (contains a dataframe).
    endo (str): the endogenous variable.
    exo (List[str]): exogenous variable used to explain the endogenous.

    Returns:
    str: a textual representation of the regression.
    """
    df = ctx.deps.df
    df = df.dropna()
    X = df[exo]
    Y = df[[endo]]
    model = sm.OLS(Y, X)
    results = model.fit(cov_type="HC2")
    summary = results.summary()

    return summary.as_text()


def anova(ctx: RunContext[EDADepsAdvanced], numerical_col: str, group_by: str) -> str:
    """
    Perform ANOVA (Analysis of Variance) to determine if there are statistically 
    significant differences between the means of groups defined by a categorical column.

    Parameters:
    ctx (RunContext[str]): The context of the current call (contains a dataframe).
    numerical_col (str): The numerical column to analyze.
    group_by (str): The categorical column to group by.

    Returns:
    str: A textual representation of the ANOVA results.
    """
    df = ctx.deps.df
    model = sm.formula.ols(f'{numerical_col} ~ C({group_by})', data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    return anova_table.to_string()


def pca_analysis(ctx: RunContext[EDADepsAdvanced], n_components: int = 2) -> str:
    """
    Perform Principal Component Analysis (PCA) on the dataframe in the context.

    Parameters:
    ctx (RunContext[str]): The context of the current call (contains a dataframe).
    n_components (int): The number of principal components to compute.

    Returns:
    str: A textual representation of the explained variance ratio of the principal components.
    """

    df = ctx.deps.df
    df = df.dropna()
    pca = PCA(n_components=n_components)
    pca.fit(df)
    explained_variance = pca.explained_variance_ratio_

    return (f'Explained variance ratio of the first {n_components} principal components: {explained_variance}')


eda_cs_basic_tools = [
    Tool(check_missing_values, takes_ctx=True, docstring_format="google"),
    Tool(correlation_matrix, takes_ctx=True, docstring_format="google"),
    Tool(summary_statistics, takes_ctx=True, docstring_format="google"),
    Tool(summary_statistics_grouped, takes_ctx=True, docstring_format="google"),
    Tool(check_outliers, takes_ctx=True, docstring_format="google"),
]

eda_cs_advanced_tools = [
    Tool(regression, takes_ctx=True, docstring_format="google"),
    Tool(anova, takes_ctx=True, docstring_format="google"),
    Tool(pca_analysis, takes_ctx=True, docstring_format="google"),
]
