import pandas as pd
from typing import Dict, Any, Optional, Callable
from .missing_handler import analyze_missing, get_missing_value_suggestion
from .duplicate_handler import analyze_duplicates
from .outlier_handler import detect_outliers
from .type_converter import analyze_dtypes

def generate_quality_report(df: pd.DataFrame, log_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """
    Generate comprehensive data quality report
    
    Parameters:
        df: Input DataFrame
        log_callback: Optional function to log messages (accepts single string argument)
    
    Returns:
        Dictionary with complete quality analysis
    """
    # return {
    #     'missing_values': analyze_missing(df),
    #     'duplicates': analyze_duplicates(df),
    #     'outliers': detect_outliers(df),
    #     'data_types': analyze_dtypes(df),
    #     'shape': {
    #         'rows': len(df),
    #         'columns': len(df.columns),
    #         'memory_usage': df.memory_usage(deep=True).sum()
    #     }
    # }

    # Initialize report
    report = {
        'missing_values': None,
        'duplicates': None,
        'outliers': None,
        'data_types': None,
        'shape': None
    }
    
    try:
        if log_callback:
            log_callback("Analyzing missing values...")
        report['missing_values'] = analyze_missing(df)
        
        if log_callback:
            log_callback("Checking for duplicates...")
        report['duplicates'] = analyze_duplicates(df)
        
        if log_callback:
            log_callback("Detecting outliers...")
        report['outliers'] = detect_outliers(df)
        
        if log_callback:
            log_callback("Analyzing data types...")
        report['data_types'] = analyze_dtypes(df)
        
        report['shape'] = {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum()
        }
        
        if log_callback:
            missing_count = report['missing_values']['counts'].sum()
            dup_count = report['duplicates']['total_duplicates']
            log_callback(
                f"Analysis complete. Found: {missing_count} missing values, "
                f"{dup_count} duplicates, {len(report['outliers'])} columns with outliers"
            )
            
    except Exception as e:
        if log_callback:
            log_callback(f"Analysis failed: {str(e)}", level='error')
        raise
    
    return report

# def get_cleaning_recommendations(report: Dict[str, Any], df:pd.DataFrame) -> Dict[str, Any]:
#     """
#     Generate automatic cleaning recommendations based on analysis
    
#     Parameters:
#         report: Quality report from generate_quality_report()
#         df: Original DataFrame needed for type conversion analysis
        
#     Returns:
#         Dictionary with recommended cleaning actions
#     """
#     recommendations = {
#         'missing_values': {},
#         'duplicates': None,
#         'outliers': {},
#         'type_conversions': []
#     }
    
#     for col, count in report['missing_values']['counts'].items():
#         col_series = df[col]
#         total_rows = report['shape']['rows']
#         recommendations['missing_values'][col] = get_missing_value_suggestion(col_series, count, total_rows)
#     # Duplicates recommendations
#     if report['duplicates']['total_duplicates'] > 0:
#         dup_percent = report['duplicates']['percentage']
#         recommendations['duplicates'] = 'drop' if dup_percent < 5 else 'flag'
    
#     # Outliers recommendations
#     for col, stats in report['outliers'].items():
#         if stats['count'] > 0:
#             recommendations['outliers'][col] = 'cap' if stats['percentage'] < 5 else 'log_transform'
    
#     # Type conversion recommendations
#     for col, dtype in report['data_types']['current_dtypes'].items():
#         if 'object' in dtype and len(df[col].unique()) < 20:
#             recommendations['type_conversions'].append((col, 'category'))
#         elif 'float' in dtype and df[col].dropna().mod(1).eq(0).all():
#             recommendations['type_conversions'].append((col, 'int'))
    
#     return recommendations

def get_cleaning_recommendations(
    report: Dict[str, Any], 
    df: pd.DataFrame,
    log_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Generate automatic cleaning recommendations with logging
    
    Parameters:
        report: Quality report from generate_quality_report()
        df: Original DataFrame needed for type conversion analysis
        log_callback: Optional function to log messages
        
    Returns:
        Dictionary with recommended cleaning actions
    """
    if log_callback:
        log_callback("Generating cleaning recommendations...")
    
    recommendations = {
        'missing_values': {},
        'duplicates': None,
        'outliers': {},
        'type_conversions': []
    }
    
    try:
        # Missing values recommendations
        if log_callback:
            log_callback("Analyzing missing value handling strategies...")
            
        for col, count in report['missing_values']['counts'].items():
            col_series = df[col]
            total_rows = report['shape']['rows']
            recommendation = get_missing_value_suggestion(col_series, count, total_rows)
            recommendations['missing_values'][col] = recommendation
            
            if log_callback and count > 0:
                log_callback(
                    f"Column '{col}': {count} missing values ({count/total_rows:.1%}) - "
                    f"recommend {recommendation}"
                )
        
        # Duplicates recommendations
        if report['duplicates']['total_duplicates'] > 0:
            dup_percent = report['duplicates']['percentage']
            recommendations['duplicates'] = 'drop' if dup_percent < 5 else 'flag'
            if log_callback:
                log_callback(
                    f"Found {report['duplicates']['total_duplicates']} duplicates "
                    f"({dup_percent:.1f}%) - recommend {recommendations['duplicates']}"
                )
        
        # Outliers recommendations
        if log_callback and report['outliers']:
            log_callback("Analyzing outlier handling strategies...")
            
        for col, stats in report['outliers'].items():
            if stats['count'] > 0:
                recommendation = 'cap' if stats['percentage'] < 5 else 'log_transform'
                recommendations['outliers'][col] = recommendation
                if log_callback:
                    log_callback(
                        f"Column '{col}': {stats['count']} outliers "
                        f"({stats['percentage']:.1f}%) - recommend {recommendation}"
                    )
        
        # Type conversion recommendations
        if log_callback:
            log_callback("Analyzing type conversion opportunities...")
            
        for col, dtype in report['data_types']['current_dtypes'].items():
            if 'object' in dtype and len(df[col].unique()) < 20:
                recommendations['type_conversions'].append((col, 'category'))
                if log_callback:
                    log_callback(f"Column '{col}': recommend conversion to category")
            elif 'float' in dtype and df[col].dropna().mod(1).eq(0).all():
                recommendations['type_conversions'].append((col, 'int'))
                if log_callback:
                    log_callback(f"Column '{col}': recommend conversion to integer")
        
        if log_callback:
            log_callback("Finished generating recommendations")
            
    except Exception as e:
        if log_callback:
            log_callback(f"Recommendation generation failed: {str(e)}", level='error')
        raise
    
    return recommendations