import pandas as pd
from typing import Dict, Any, List, Optional

def analyze_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze duplicate rows in dataframe
    
    Parameters:
        df: Input DataFrame
        subset: Columns to consider for duplicates (None for all columns)
    
    Returns:
        Dictionary with duplicate analysis results
    """
    dup_mask = df.duplicated(subset=subset, keep=False)
    dup_count = dup_mask.sum()
    
    return {
        'total_duplicates': dup_count,
        'percentage': dup_count / len(df) * 100,
        'duplicate_groups': df[dup_mask].groupby(subset if subset else list(df.columns)).size().to_dict(),
        'affected_columns': subset if subset else list(df.columns)
    }

def handle_duplicates(
    df: pd.DataFrame,
    strategy: str = 'drop',
    subset: Optional[List[str]] = None,
    keep: str = 'first',
    flag_col: str = 'is_duplicate',
    log_callback: Optional[callable] = None
) -> pd.DataFrame:
    """
    Handle duplicate rows in dataframe
    
    Parameters:
        df: Input DataFrame
        strategy: 'drop', 'flag', or 'keep'
        subset: Columns to consider for duplicates
        keep: 'first', 'last', or False (only when strategy='drop')
        flag_col: Column name for flagging duplicates
    
    Returns:
        Processed DataFrame
    """
    analysis = analyze_duplicates(df, subset)
    
    if strategy == 'drop':
        df = df.drop_duplicates(subset=subset, keep=keep)
    elif strategy == 'flag':
        df[flag_col] = df.duplicated(subset=subset, keep=keep)
    
    if log_callback:
            log_callback = (
            f"Handled duplicates using {strategy} strategy. "
            f"{df['rows_removed']} rows removed." if strategy == 'drop' else "Duplicates flagged."
        )
    return df, {
        **analysis,
        'action_taken': strategy,
        'rows_removed': analysis['total_duplicates'] if strategy == 'drop' else 0
    }