import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple

def analyze_missing(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze missing values in dataframe"""
    missing_counts = df.isnull().sum()
    total_rows = df.shape[0]
     
    return {
        'counts': missing_counts.to_dict(),
        'percentages': (missing_counts / total_rows * 100).round(2).to_dict(),
        'columns_dropped': [],
        'columns_filled': []
    }

def get_missing_value_suggestion(col: pd.Series, count: int, total_rows: int) -> str:
    """Get suggested handling method for a column with missing values"""
    if count == 0:
        return "no_action"
    
    percent_missing = count / total_rows
    dtype = col.dtype
    
    if np.issubdtype(dtype, np.number):
        if percent_missing > 0.5:
            return "drop_column"
        elif percent_missing > 0.2:
            return "fill_median"
        elif percent_missing > 0.05:
            return "fill_mean"
        else:
            return "fill_median"  # Default for small amounts of missing data
        
    elif dtype == 'object':
        if percent_missing > 0.5:
            return "drop_column"
        elif percent_missing > 0.1:
            return "fill_mode"
        else:
            return "fill_ffill"
    elif np.issubdtype(dtype, np.datetime64):
        return "fill_ffill"
    else:
        return "fill_bfill"


def handle_missing_values(
    df: pd.DataFrame,
    threshold: float = 0.5,
    numeric_strategy: str = 'mean',
    categorical_strategy: str = 'mode',
    datetime_strategy: str = 'ffill',
    interpolation_method: str = 'linear',
    custom_fill: Optional[Dict[str, Any]] = None,
    auto_apply_suggestions: bool=False,
    log_callback: Optional[callable] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values with multiple strategies
    
    Parameters:
        df: Input DataFrame
        threshold: Drop columns with missing ratio > threshold (0-1)
        numeric_strategy: 'mean', 'median', 'interpolate', 'drop', or 'custom'
        categorical_strategy: 'mode', 'ffill', 'bfill', or 'drop'
        datetime_strategy: 'ffill', 'bfill', 'interpolate', or 'drop'
        interpolation_method: 'linear', 'time', 'index', 'pad', etc.
        custom_fill: Dictionary of {column_name: fill_value} for custom filling
        auto_apply_suggestions: Whether to use get_missing_value_suggestion()
        log_callback: Optional function to log messages (accepts single string argument)

    Returns:
        Processed DataFrame and report dictionary
    """
    result_info = analyze_missing(df)
    total_rows = df.shape[0]
    custom_fill = custom_fill or {}
    df = df.copy()

    if auto_apply_suggestions:
        for col in df.columns:
            count = df[col].isnull().sum()
            if count > 0:
                suggestion = get_missing_value_suggestion(df[col], count, total_rows)
                if suggestion.startswith('fill_'):
                    custom_fill[col] = suggestion[5:]  # Remove 'fill_' prefix
                elif suggestion == 'drop_column':
                    custom_fill[col] = 'drop'

    for col in list(df.columns):
        if col in custom_fill:
            strategy = custom_fill[col]
            
            if strategy == 'drop':
                # new
                if log_callback:
                    log_callback(f"Dropped column '{col}' (missing ratio > {threshold})")
                df.drop(columns=[col], inplace=True)
                result_info['columns_dropped'].append(col)
                continue
                
            if strategy in ['mean', 'median', 'mode']:
                if strategy == 'mean' and np.issubdtype(df[col].dtype, np.number):
                    fill_val = df[col].mean()
                elif strategy == 'median' and np.issubdtype(df[col].dtype, np.number):
                    fill_val = df[col].median()
                elif strategy == 'mode':
                    fill_val = df[col].mode()[0] if not df[col].mode().empty else "UNKNOWN"
                else:
                    continue
                                    
                df[col].fillna(fill_val, inplace=True)
                if log_callback:
                    log_callback(f"Filled missing values in '{col}' with {strategy} (value: {fill_val})")
                result_info['columns_filled'].append((col, strategy, fill_val))
                continue

            elif strategy in ['ffill', 'bfill', 'interpolate']:
                if strategy == 'interpolate' and np.issubdtype(df[col].dtype, np.number):
                    df[col] = df[col].interpolate(method=interpolation_method)
                    if log_callback:
                        log_callback(f"Interpolated missing values in '{col}' using {interpolation_method} method")
                else:
                    df[col].fillna(method=strategy, inplace=True)
                    if log_callback:
                        log_callback(f"Filled missing values in '{col}' with {strategy} (value: {fill_val})")
                result_info['columns_filled'].append((col, strategy, None))
                continue

            if log_callback:
                log_callback(f"Missing value handling complete. "
                            f"Filled {len(result_info['columns_filled'])} columns, "
                            f"dropped {len(result_info['columns_dropped'])} columns")

            

    return df, result_info