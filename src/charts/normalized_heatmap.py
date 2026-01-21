import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import seaborn as sns 

from matplotlib.figure import Figure

def create_normalized_heatmap(pivot_df : pd.DataFrame, 
                              figsize=(10, 6),
                              cmap: str = 'RdYlGn_r',
                              fmt: str = '.2f',
                              with_cbar : bool = False,
                              title: str = None,
                              x_title: str = None,
                              y_title: str = None,
                              ) -> tuple [Figure, plt.Axes]:
    
    norm_df = pivot_df.copy()

    # Create a normalized df 
    for col in norm_df.columns:
        min_val = norm_df[col].min()
        max_val = norm_df[col].max()

        if min_val == max_val:
            norm_df[col] = norm_df[col].apply(lambda x: 0.5 if pd.notnull(x) else np.nan)
        else:
            norm_df[col] = (norm_df[col] - min_val) / (max_val - min_val)

        
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        norm_df,
        cmap=cmap,
        annot=pivot_df,
        fmt=fmt,
        cbar=with_cbar,
    )

    if title:
        ax.set_title(title)

    if x_title:
        ax.set_xlabel(x_title)

    if y_title:
        ax.set_ylabel(y_title) 

    return fig, ax
