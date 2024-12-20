"""
plots.py - Plotting Functions for PyBeePop+
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_timeseries(output=None, columns=[]):
    """Function to plot a BeePop+ output as a time series.

    Args:
        output (DatFrame, optional): DataFrame of pybeepop+ model run output. Defaults to None.
        columns (list, optional): List of column names to plot (as strings). Defaults to ["Colony Size", "Adult Workers", "Capped Worker Brood", "Worker Larvae", "Worker Eggs"].

    Returns:
        Matplotlib Axes object: A Matploitlib Axes object for further customization.
    """
    if (output is not None) and columns:
        output_trimmed = output.iloc[1:, :].set_index("Date")  # drop 'Initial' row
        output_trimmed.index = pd.DatetimeIndex(
            output_trimmed.index
        )  # convert Date column to DateTimeIndex
        fig, ax = plt.subplots()
        for column in columns:
            ax.plot(
                output_trimmed.index.to_numpy(), output_trimmed[column].to_numpy(), label=column
            )
        ax.legend()
        ax.xaxis.set_major_formatter(
            mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
        )  # format date axis
        plt.show()
        return ax
