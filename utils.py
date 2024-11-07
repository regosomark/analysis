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



def save_load_factor_table(energy_summary, output_path='load_factor_table.png'):
    """
    Generates a table for the monthly load factor and saves it as an image.

    Parameters:
    - energy_summary (pd.DataFrame): DataFrame with 'supply period' and 'load factor' columns.
    - output_path (str): File path where the table image will be saved.
    """
    # Filter out rows labeled 'Total', 'Average', 'Max', or 'Min'
    filtered_energy_summary = energy_summary[~energy_summary['supply period'].isin(['Total', 'Average', 'Max', 'Min'])]

    # Select the relevant columns for months and load factor
    months_load_factor = filtered_energy_summary[['supply period', 'load factor']]

    # Transpose the DataFrame
    transposed_table = months_load_factor.set_index('supply period').T

    # Plotting the transposed table as an image
    fig, ax = plt.subplots(figsize=(8, 4))  # Set figure size for the table
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=transposed_table.values, colLabels=transposed_table.columns, loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)  # Scale the table for better visibility

    # Save the table as an image
    plt.savefig(output_path, bbox_inches='tight')
    plt.close(fig)  # Close the plot to free up memory

def save_energy_consumption_plot(energy_summary, output_path='energy_consumption_plot.png'):
    # Filter out summary data that we don't want to include in the plot
    monthly_data = energy_summary[~energy_summary['supply period'].isin(['Total', 'Average', 'Max', 'Min'])]

    # Ensure 'kwh' and 'kw' columns are numeric (remove commas and convert to float)
    # Use .loc to avoid SettingWithCopyWarning
    monthly_data = monthly_data.copy()  # Ensure we're working with a copy
    monthly_data['kwh'] = monthly_data['kwh'].str.replace(',', '').astype(float)
    monthly_data['kw'] = monthly_data['kw'].str.replace(',', '').astype(float)

    # Find the highest values for setting axis limits
    max_kwh = monthly_data['kwh'].max()
    max_kw = monthly_data['kw'].max()

    # Plotting
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Bar plot for 'kwh' with thinner bars
    bar_width = 0.4
    bars = ax1.bar(monthly_data['supply period'], monthly_data['kwh'], color='orange', label='kWh', width=bar_width)
    ax1.set_xlabel('Supply Period (Month)')
    ax1.set_ylabel('kWh', color='black')
    ax1.tick_params(axis='y', labelcolor='black')

    # Set kWh axis limits and ticks
    ax1.set_ylim(0, max_kwh + 10000)
    ax1.set_yticks(np.arange(0, max_kwh + 10000, 10000))

    # Add labels at the center of each bar's height for kWh values
    for bar in bars:
        # Position the label at half the height of each bar
        label_y_position = bar.get_height() / 2
        ax1.text(
            bar.get_x() + bar.get_width() / 2, label_y_position,
            f'{bar.get_height():,.2f}', ha='center', va='center', color='black', fontsize=10
        )

    # Secondary y-axis for 'kw' with line plot and markers
    ax2 = ax1.twinx()
    line, = ax2.plot(monthly_data['supply period'], monthly_data['kw'], color='green', marker='o', label='kW')
    ax2.set_ylabel('kW', color='black')
    ax2.tick_params(axis='y', labelcolor='black')

    # Set kW axis limits and ticks
    ax2.set_ylim(100, max_kw + 100)
    ax2.set_yticks(np.arange(100, max_kw + 100, 100))

    # Add labels to each point for kW values with one decimal place
    for x, y in zip(monthly_data['supply period'], monthly_data['kw']):
        ax2.text(x, y + 10, f'{y:,.2f}', ha='center', va='bottom', color='black', fontsize=10)

    # Title and layout adjustments
    plt.title('Monthly Energy Consumption (kWh) and Peak Demand (kW)')
    fig.tight_layout()

    # Handle the legends separately
    lines1, labels1 = ax1.get_legend_handles_labels()  # Get handles and labels for the first axis
    lines2, labels2 = ax2.get_legend_handles_labels()  # Get handles and labels for the second axis
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.1, 0.95))  # Combine and place legend

    # Save the plot as an image
    plt.savefig(output_path, bbox_inches='tight')
    plt.close(fig)  # Close the plot to free up memory

# Example usage:
output_path = 'energy_consumption_plot.png'
save_energy_consumption_plot(energy_summary_result, output_path=output_path)

# Print confirmation message
print(f"Energy consumption plot saved as {output_path}")
