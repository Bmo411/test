import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick

import numpy as np 
import pandas as pd

from matplotlib.figure import Figure 
from matplotlib.axes import Axes

from typing import Literal



def create_time_series_chart(time_series: list[tuple[pd.Series, str]],
                             x_label: str,
                             y_label: str,
                             chart_title: str,
                             figsize: tuple[int, int] = (10, 6),
                             unit: str = 'MN',
                             color_list: list[str] = None,
                             with_spines: Literal[False, True, 'left-bottom'] = 'left-bottom',
                             all_plots_labels: Literal[False, True, 'just_last'] = 'just_last',
                             y_min: int = None,
                             ) -> tuple[Figure, Axes]:
    fig, ax = plt.subplots(figsize=figsize)

    if not color_list:
        color_list = [
            "#8727e0",
            "#053658",  
            "#8f0707",  
            "#0CB40C",    
            "#4e2017",  
            "#be178c",  
            "#7f7f7f",  
            "#CACA06",  
            "#17becf",  
            "#ff7f0e",  
        ]


    # set x axe limits 
    all_mins = [ser.index.min() for ser, _ in time_series]
    all_maxs = [ser.index.max() for ser, _ in time_series]

    global_min = min(all_mins)
    global_max = max(all_maxs)

    ax.set_xlim(global_min, global_max)


    used_positions = []
    for idx, (serie, label) in enumerate(time_series):

        if serie.empty:
            continue

        currColor = color_list[idx % len(color_list)]
        ax.plot(serie, label=label, color=currColor)
        ax.scatter(serie.index, serie.values, color=currColor, s=50, zorder=3)


        if all_plots_labels == 'just_last':
            last_x = serie.index[-1]
            last_y = serie.iloc[-1]

            # move text if there is other near 
            while any(abs(last_y - pos) < (last_y * 0.02) for pos in used_positions):
                last_y += last_y * 0.02
            used_positions.append(last_y)

            ax.text(
                    last_x,
                    last_y,
                    f'{last_y:,.2f} {"Kg" if unit.lower() == "kg" else "$"}',
                    va='bottom',
                    ha='center',
                    fontsize=12
                )
            
        elif all_plots_labels:
            for x, y in zip(serie.index, serie.values):
                ax.text(
                    x,
                    y,
                    f'{y:,.2f} {"Kg" if unit.lower() == "kg" else "$"}',
                    va='bottom',
                    ha='center',
                    fontsize=9,
                )
    

    # titles, labels and legends    
    plt.legend(loc='best')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(chart_title)

    if with_spines == 'left-bottom':
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    elif not with_spines:
        for s in ax.spines.values():
            s.set_visible(False)

    # format of y and x axis 
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    fig.autofmt_xdate()
    if unit.strip().lower() == 'kg':
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f} Kg'))
    else:
        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))

    return fig, ax