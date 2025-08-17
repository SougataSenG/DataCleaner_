import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

def analyze_dtypes(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze data types in dataframe
    
    Parameters:
        df: Input DataFrame
    
    Returns:
        Dictionary with type analysis
    """
    return {
        'current_dtypes': df.dtypes.astype(str).to_dict(),
        'numeric_cols': df.select_dtypes(include=np.number).columns.tolist(),
        'datetime_cols': df.select_dtypes(include=np.datetime64).columns.tolist(),
        'categorical_cols': df.select_dtypes(include=['object', 'category']).columns.tolist()
    }

def convert_dtypes(
    df: pd.DataFrame,
    conversions: Dict[str, str],
    datetime_format: Optional[str] = None,
    categories: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Convert data types of columns
    
    Parameters:
        df: Input DataFrame
        conversions: Dictionary of {column: target_type}
                    Supported types: 'int', 'float', 'str', 'bool', 
                                    'datetime', 'category'
        datetime_format: Format string for datetime conversion
        categories: Dictionary of {column: categories} for categorical conversion
    
    Returns:
        Processed DataFrame and report
    """
    analysis = analyze_dtypes(df)
    conversion_report = {}
    
    for col, target_type in conversions.items():
        if col not in df.columns:
            continue
            
        original_type = str(df[col].dtype)
        
        try:
            if target_type == 'datetime':
                df[col] = pd.to_datetime(df[col], format=datetime_format)
            elif target_type == 'category':
                df[col] = pd.Categorical(
                    df[col], 
                    categories=categories.get(col, None) if categories else None
                )
            else:
                df[col] = df[col].astype(target_type)
            
            conversion_report[col] = {
                'from': original_type,
                'to': target_type,
                'success': True
            }
        except Exception as e:
            conversion_report[col] = {
                'from': original_type,
                'to': target_type,
                'success': False,
                'error': str(e)
            }
    
    return df, {
        'original_analysis': analysis,
        'conversions': conversion_report
    }