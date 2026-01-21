import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from matplotlib.figure import Figure
from matplotlib.axes import Axes


from ..utils.formatting import to_currency, to_kg, to_percentage


def create_stacked_horizontal_chart(pivot_table: pd.DataFrame,
                                    x_label: str,
                                    y_label: str,
                                    figsize=(10,6),
                                    units: str = 'MN',
                                    legend: str = None,
                                    with_axes_spines: bool = True,
                                    with_ticks: bool = True,
                                    with_bar_notations: bool = True,
                                    title: str = None
                                    ) -> tuple[Figure, Axes]:
    
    
    if units not in ('KG', 'MN', '%'):
        raise ValueError('Unit must be kg, mn or %')
    
    if units == 'KG':
        to_units = to_kg
    elif units == '%':
        to_units = to_percentage
    else: 
        to_units = to_currency

    fig, ax = plt.subplots(figsize=figsize)
    
    #Create a list of the pivot table rows length
    left_vector = np.zeros(len(pivot_table))
    pivot_table.index = pivot_table.index.astype(str)
    for col in pivot_table.columns:
        ax.barh(
            pivot_table.index,
            pivot_table[col],
            left=left_vector,
            label=col,
        )
        left_vector += pivot_table[col].to_numpy()

    # Add title 
    if title: 
        ax.set_title(title)

    # Add paddign to y axe label
    ax.yaxis.set_tick_params(pad=10)

    if with_bar_notations:
        totals = pivot_table.sum(axis=1)
        for y_pos, total in enumerate(totals):
            ax.text(total + 5, y_pos, to_units(total), va='center', ha='left', fontsize=12)

    if with_axes_spines:
        for s in ax.spines.values():
            s.set_visible(False)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    if legend:
        ax.legend(title=legend, loc='best')

    # Format x axis 
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, pos: to_units(x)))

    


    return fig, ax