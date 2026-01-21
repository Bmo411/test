import pandas as pd 
import matplotlib.pyplot as plt 
import matplotlib.ticker as mtick

from matplotlib.figure import Figure 
from matplotlib.axes import Axes


def create_stacked_chart(pivot_table: pd.DataFrame, 
                         figsize=(10, 6),
                         title: str = None, 
                         pre_unit: str = "", 
                         post_unit: str = "",
                         with_legend: bool = False,
                         legend_title: str = "",
                         bar_label: bool = True,
                         label_rotation: int = None,
                         bar_label_rotation: int = None, # Rotation of text above the bars
                         with_axes_spines: bool = True,
                         ) -> tuple[Figure, Axes]:
    
    fig, ax = plt.subplots(figsize=figsize)
    pivot_table.plot(kind="bar", stacked=True, ax=ax)

    if title: 
        ax.set_title(title)

    if not with_axes_spines:
        for s in ax.spines.values():
            s.set_visible(False)


    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter(f'{pre_unit}{{x:,.0f}}{post_unit}'))
    if (with_legend):
        ax.legend(
            title=legend_title,
            loc='best',
            ncol=3,
            frameon=False
        )
    
    if (bar_label):
        total_bars = pivot_table.sum(axis=1)
        for idx, total in enumerate(total_bars):
            ax.text(
                x=idx,
                y = total + total * 0.01,
                s=f'{pre_unit}{total:,.0f}{post_unit}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold',
                rotation=bar_label_rotation if bar_label_rotation else 0
            )
    
    if (label_rotation):
        ax.tick_params(axis='x', labelrotation=label_rotation)
        

    return fig, ax

