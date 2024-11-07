import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt

fm.fontManager.addfont(
  './assets/Poppins-Regular.ttf')

# Get list of days of the week
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_energy_summary(data, kwh_column='kwh', kw_column='kw', frequency=1):
  energy_summary = data.groupby("supply period", sort=False).agg({
    "supply period": "count",
    kwh_column: "sum",
    kw_column: "max"
  })

  # Rename columns
  energy_summary.columns = ["number of hours", "kwh", "kw"]

  # Convert number of hours
  energy_summary["number of hours"] = energy_summary["number of hours"] / frequency

  # Add row Total kwh sum and kw max
  energy_summary.loc["Total"] = energy_summary.sum()
  energy_summary.loc["Total", "kw"] = energy_summary.iloc[:-1]["kw"].max()

  # Compute for load factor
  energy_summary["load factor"] = (energy_summary["kwh"] / (energy_summary['kw']
                                                            * energy_summary["number of hours"])) * 100

  original_energy_summary = energy_summary.iloc[:-1].copy()

  # Add Average, Max, Min rows
  energy_summary.loc["Average"] = original_energy_summary.mean()
  energy_summary.loc["Max"] = original_energy_summary.max()
  energy_summary.loc["Min"] = original_energy_summary.min()

  # Remove supply period as index
  energy_summary = energy_summary.reset_index()

  # Permanent display of 2 decimal places as string 0,000.00
  energy_summary["number of hours"] = energy_summary["number of hours"].apply(lambda x: "{:,.2f}".format(x))
  energy_summary["kwh"] = energy_summary["kwh"].apply(lambda x: "{:,.2f}".format(x))
  energy_summary["kw"] = energy_summary["kw"].apply(lambda x: "{:,.2f}".format(x))
  energy_summary["load factor"] = energy_summary["load factor"].apply(lambda x: "{:,.2f}".format(x))

  return energy_summary


def plot_hourly_load_curve(hourly_summary, column_name='max', unit='MW', ylabel='Peak Demand', ylim: list = None):
  if ylim is not None:
    assert ylim[0] < ylim[1], "ylim should be a list with 2 elements, where the first element is less than the second."

  # Create figure and axis
  fig, ax = plt.subplots(figsize=(15, 5))

  # Plot
  hourly_summary[column_name].plot(
    ax=ax, kind='area',
    legend=True, color='#ff7f0e',
    label=f'{ylabel} ({unit})'
  )

  # Set x- and y-axis labels
  ax.set_xlabel("Hour")
  plt.ylabel(f'{ylabel} ({unit})')

  # Set y-axis minimum to 0
  if ylim is not None:
    ax.set_ylim(bottom=ylim[0], top=ylim[1])

  # Show y-axis ticks 0,000.00
  ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,.2f}".format(x)))

  # Show all x-ticks
  ax.set_xticks(hourly_summary.index)

  # Get list of existing legend
  legend = [l.get_text() for l in ax.get_legend().get_texts()]
  # Place legend at the bottom of the plot
  ax.legend(
    legend,
    loc='upper center',
    bbox_to_anchor=(0.5, 0.99),
    bbox_transform=fig.transFigure,
    ncol=len(legend),
  )

  # Set x-ticks to be horizontal
  plt.xticks(rotation=0)

  # Set font to Poppins
  # Load Poppins font
  plt.rcParams['font.family'] = 'Poppins'

  # Remove border box
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)
  ax.spines['left'].set_visible(False)
  ax.spines['bottom'].set_visible(False)

  # Add gray horizontal gridlines
  ax.yaxis.grid(color='gray', linestyle='-', linewidth=0.25)

  # Remove y-axis ticks only (keep labels)
  ax.tick_params(axis='y', which='both', left=False)

  # Remove x-axis ticks only (keep labels)
  ax.tick_params(axis='x', which='both', bottom=False)

  plt.show()


def plot_hourly_by_day_load_curve(hourly_by_day_summary, column_name='max', unit='MW', ylabel='Peak Demand', ylim: list = None):
  if ylim is not None:
    assert ylim[0] < ylim[1], "ylim should be a list with 2 elements, where the first element is less than the second."

  # Create figure and axis
  fig, ax = plt.subplots(figsize=(15, 5))

  # Plot
  hourly_by_day_summary.plot(
    ax=ax, kind='line',
    legend=True, colormap='tab10',
    label=f'{ylabel} ({unit})'
  )

  # Set x- and y-axis labels
  ax.set_xlabel("Hour")
  ax.set_ylabel(f'{ylabel} ({unit})')

  # Set y-axis minimum to 0
  if ylim is not None:
    ax.set_ylim(bottom=ylim[0], top=ylim[1])

  # Show y-axis ticks 0,000.00
  ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,.2f}".format(x)))

  # Show all x-ticks
  ax.set_xticks(hourly_by_day_summary.index)

  # Get list of existing legend
  legend = days_of_week
  # Place legend at the bottom of the plot
  ax.legend(
    legend,
    loc='upper center',
    bbox_to_anchor=(0.5, 0.99),
    bbox_transform=fig.transFigure,
    ncol=len(legend),
  )

  # Set x-ticks to be horizontal
  plt.xticks(rotation=0)

  # Set font to Poppins
  # Load Poppins font
  plt.rcParams['font.family'] = 'Poppins'

  # Remove border box
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)
  ax.spines['left'].set_visible(False)
  ax.spines['bottom'].set_visible(False)

  # Add gray horizontal gridlines
  ax.yaxis.grid(color='gray', linestyle='-', linewidth=0.25)

  # Remove y-axis ticks only (keep labels)
  ax.tick_params(axis='y', which='both', left=False)

  # Remove x-axis ticks only (keep labels)
  ax.tick_params(axis='x', which='both', bottom=False)

  plt.show()

def save_energy_consumption_plot(energy_summary, output_path):
    import matplotlib.pyplot as plt

    # Copy data to avoid SettingWithCopyWarning
    energy_summary = energy_summary.copy()
    
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot kWh as a bar plot
    ax1.bar(energy_summary.index, energy_summary['kwh'], color='skyblue', label='Energy (kWh)')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Energy (kWh)', color='skyblue')
    ax1.tick_params(axis='y', labelcolor='skyblue')
    
    # Adding labels on the bars
    for index, value in enumerate(energy_summary['kwh']):
        ax1.text(index, value / 2, f'{value:.2f}', ha='center', color='black', fontweight='bold')
    
    # Plot kW as a line plot
    ax2 = ax1.twinx()
    ax2.plot(energy_summary.index, energy_summary['kw'], color='orange', marker='o', linestyle='-', label='Demand (kW)')
    ax2.set_ylabel('Demand (kW)', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    # Adding labels on the kW data points
    for index, value in enumerate(energy_summary['kw']):
        ax2.text(index, value + 0.1, f'{value:.2f}', ha='center', color='orange', fontweight='bold')
    
    fig.tight_layout()

    # Correctly combine legend handles and labels
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.1, 0.95))
    
    # Save plot as an image
    plt.savefig(output_path)
    plt.close(fig)
    
    print(f"Energy consumption plot saved as {output_path}")



