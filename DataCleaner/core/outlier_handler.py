import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from typing import Dict, Any, List, Union, Tuple
from io import BytesIO
import base64

from typing import Optional

def detect_outliers(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = 'iqr',
    threshold: float = 1.5,
    generate_plots: bool = False
) -> Dict[str, Any]:
    """
    Detect outliers in numeric columns with optional visualization
    
    Parameters:
        df: Input DataFrame
        columns: Columns to analyze (None for all numeric)
        method: 'iqr' or 'zscore'
        threshold: Threshold multiplier for detection
        generate_plots: Whether to generate plot images
    
    Returns:
        Dictionary with outlier analysis and visualization
    """
    if columns is None:
        columns = df.select_dtypes(include=np.number).columns.tolist()
    
    results = {}
    
    for col in columns:
        if method == 'iqr':
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            outliers = (df[col] < lower) | (df[col] > upper)
        else:  # zscore
            zscore = (df[col] - df[col].mean()) / df[col].std()
            outliers = np.abs(zscore) > threshold
        
        col_results = {
            'count': outliers.sum(),
            'percentage': outliers.mean() * 100,
            'indices': df.index[outliers].tolist(),
            'method': method,
            'threshold': threshold,
            'bounds': {
                'lower': lower if method == 'iqr' else (df[col].mean() - threshold * df[col].std()),
                'upper': upper if method == 'iqr' else (df[col].mean() + threshold * df[col].std())
            }
        }
        
        if generate_plots:
            col_results['visualizations'] = generate_outlier_plots(df, col, outliers, col_results['bounds'])
        
        results[col] = col_results
    
    return results

def generate_outlier_plots(
    df: pd.DataFrame,
    column: str,
    outlier_mask: pd.Series,
    bounds: Dict[str, float]
) -> Dict[str, str]:
    """
    Generate box plot and scatter plot visualization for outliers
    
    Parameters:
        df: Input DataFrame
        column: Column being analyzed
        outlier_mask: Boolean mask of outliers
        bounds: Dictionary with lower/upper bounds
    
    Returns:
        Dictionary with base64 encoded plot images
    """
    import matplotlib
    matplotlib.use('Agg')
    plots = {}

    try:
        # Box plot
        fig, ax = plt.subplots(figsize=(8, 4))
        df[column].plot(kind='box', ax=ax)
        ax.set_title(f'Box Plot of {column} with Outliers')
        plots['boxplot'] = fig_to_base64(fig)
        plt.close(fig)
        
        # Scatter plot (index vs values)
        fig, ax = plt.subplots(figsize=(10, 5))
        inliers = df[~outlier_mask]
        outliers = df[outlier_mask]
        
        ax.scatter(inliers.index, inliers[column], color='blue', label='Normal')
        ax.scatter(outliers.index, outliers[column], color='red', label='Outlier')
        
        if bounds:
            ax.axhline(y=bounds['lower'], color='orange', linestyle='--', label='Lower Bound')
            ax.axhline(y=bounds['upper'], color='orange', linestyle='--', label='Upper Bound')
        
        ax.set_title(f'Scatter Plot of {column} with Outliers Marked')
        ax.set_xlabel('Index')
        ax.set_ylabel(column)
        ax.legend()
        plots['scatterplot'] = fig_to_base64(fig)
        plt.close(fig)
    except Exception as e:
        print(f"Plotting error: {str(e)}")
       
    return plots

def fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 encoded image"""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def handle_outliers(
    df: pd.DataFrame,
    strategy: str = 'cap',
    generate_plots: bool = False,
    **kwargs
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle outliers in numeric columns with visualization support
    
    Parameters:
        df: Input DataFrame
        strategy: 'cap', 'remove', 'log', or 'ignore'
        generate_plots: Whether to generate before/after plots
        kwargs: Additional parameters for detection
    
    Returns:
        Tuple of (processed DataFrame, report dictionary)
    """
    # Before processing analysis
    before_analysis = detect_outliers(df, generate_plots=generate_plots, **kwargs)
    processed_cols = {}
    after_plots = {}
    
    for col, stats in before_analysis.items():
        if strategy == 'cap' and stats['count'] > 0:
            # Store original values for visualization
            original_values = df[col].copy()
            
            if stats['method'] == 'iqr':
                df[col] = df[col].clip(stats['bounds']['lower'], stats['bounds']['upper'])
            else:  # zscore
                mean = df[col].mean()
                std = df[col].std()
                cutoff = stats['threshold'] * std
                df[col] = df[col].clip(mean - cutoff, mean + cutoff)
            
            processed_cols[col] = 'capped'
            
            if generate_plots:
                # Generate after plots for comparison
                fig, ax = plt.subplots(1, 2, figsize=(12, 5))
                
                # Before/After distribution
                original_values.plot(kind='density', ax=ax[0], color='red', label='Original')
                df[col].plot(kind='density', ax=ax[0], color='green', label='Processed')
                ax[0].set_title(f'Distribution Comparison: {col}')
                ax[0].legend()
                
                # After scatter plot
                current_outliers = detect_outliers(pd.DataFrame({col: df[col]}), [col], **kwargs)
                outlier_mask = df.index.isin(current_outliers[col]['indices'])
                
                inliers = df[~outlier_mask]
                outliers = df[outlier_mask]
                ax[1].scatter(inliers.index, inliers[col], color='blue', label='Normal')
                ax[1].scatter(outliers.index, outliers[col], color='red', label='Outlier')
                if 'bounds' in stats:
                    ax[1].axhline(y=stats['bounds']['lower'], color='orange', linestyle='--')
                    ax[1].axhline(y=stats['bounds']['upper'], color='orange', linestyle='--')
                ax[1].set_title(f'Processed Data: {col}')
                ax[1].set_xlabel('Index')
                ax[1].set_ylabel(col)
                
                after_plots[col] = fig_to_base64(fig)
                plt.close(fig)
        
        elif strategy == 'remove':
            outliers = df.index.isin(stats['indices'])
            df = df[~outliers]
            processed_cols[col] = 'rows_removed'
        
        elif strategy == 'log':
            df[col] = np.log1p(df[col])
            processed_cols[col] = 'log_transform'
    
    # After processing analysis
    after_analysis = detect_outliers(df, **kwargs) if any(processed_cols.values()) else None
    
    return df, {
        'original_analysis': before_analysis,
        'action_taken': strategy,
        'processed_columns': processed_cols,
        'after_analysis': after_analysis,
        'visualizations': {
            'before': {col: data['visualizations'] for col, data in before_analysis.items() 
                      if 'visualizations' in data},
            'after': after_plots
        } if generate_plots else None
    }