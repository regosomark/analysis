import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from pandas.plotting import table
import os
import seaborn as sns


# Get list of days of the week
days_of_week = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"]

fm.fontManager.addfont(
    './assets/Poppins-Regular.ttf')

# Specify the folder name as 'images'
folder_path = 'image'  # Folder name 'images'
# Make sure the directory exists; if not, create it
if not os.path.exists(folder_path):
  os.makedirs(folder_path)

# For Processing of data, returning with kw (1 hour or 5 minutes)


def process_energy_data(client_data: pd.DataFrame) -> pd.DataFrame:
  client_data['datetime'] = pd.to_datetime(client_data['datetime'])

  # Calculate the average frequency dynamically
  avg_points_per_hour = client_data.resample(
      'h', on='datetime').count().hour.mean().round(0)

  kwh_column = 'kwh'
  kw_column = 'kw'

  # Dynamically calculate 'kw' based on the detected frequency
  if kwh_column in client_data.columns:
    if avg_points_per_hour > 0:  # Avoid division by zero or invalid cases
      frequency = 60 / (60 / avg_points_per_hour)
      client_data[kw_column] = client_data[kwh_column] * frequency
    else:
      # Default case for no transformation
      client_data[kw_column] = client_data[kwh_column]

  return client_data


def generate_energy_summary(
        data, datetime_column='datetime', kwh_column='kwh', kw_column='kw'):
  # Ensure that kwh_column and kw_column are properly formatted and
  # converted to float
  data = data.copy()  # Prevent SettingWithCopyWarning by working on a copy

  # Convert the columns to strings (in case they are not already) before
  # replacing commas
  data[kwh_column] = data[kwh_column].astype(
      str).str.replace(',', '', regex=False).astype(float)
  data[kw_column] = data[kw_column].astype(
      str).str.replace(',', '', regex=False).astype(float)

  # Determine the frequency based on the time intervals in the datetime
  # column
  interval_seconds = data[datetime_column].diff().dt.total_seconds().median()
  frequency = 12 if interval_seconds == 300 else 1  # 12 for 5 minutes, 1 for 1 hour

  # Group by supply_period and aggregate the necessary columns
  energy_summary = data.groupby("supply_period", sort=False).agg({
      "supply_period": "count",
      kwh_column: "sum",
      kw_column: "max"
  })

  # Rename columns for readability
  energy_summary.columns = ["number of intervals", "kwh", "kw"]

  # Calculate 'number of hours' based on frequency and drop 'number of
  # intervals'
  energy_summary["number of hours"] = energy_summary["number of intervals"] / frequency
  energy_summary.drop(columns=["number of intervals"], inplace=True)

  # Add a total row with the sum of kWh and the max of kW
  energy_summary.loc["Total"] = energy_summary.sum()
  energy_summary.loc["Total", "kw"] = energy_summary.iloc[:-1]["kw"].max()

  # Calculate the load factor
  energy_summary["load factor"] = (
      energy_summary["kwh"] / (energy_summary['kw'] * energy_summary["number of hours"])) * 100

  # Create a copy of the summary data without the Total row for statistics
  original_energy_summary = energy_summary.iloc[:-1].copy()

  # Add Average, Max, Min rows based on the original data (excluding 'Total')
  energy_summary.loc["Average"] = original_energy_summary.mean()
  energy_summary.loc["Max"] = original_energy_summary.max()
  energy_summary.loc["Min"] = original_energy_summary.min()

  # Reset index to remove 'supply_period' from being the index
  energy_summary = energy_summary.reset_index()

  # Reorder columns as specified
  energy_summary = energy_summary[[
      "supply_period", "number of hours", "kwh", "kw", "load factor"]]

  # Format columns to display numbers with 2 decimal places and comma
  # separators
  energy_summary["number of hours"] = energy_summary["number of hours"].apply(
      lambda x: "{:,.2f}".format(x))
  energy_summary["kwh"] = energy_summary["kwh"].apply(
      lambda x: "{:,.2f}".format(x))
  energy_summary["kw"] = energy_summary["kw"].apply(
      lambda x: "{:,.2f}".format(x))
  energy_summary["load factor"] = energy_summary["load factor"].apply(
      lambda x: "{:,.2f}%".format(x))

  return energy_summary


def energy_consumption_plot(energy_summary):

  # Filter out rows labeled 'Total', 'Average', 'Max', or 'Min'
  monthly_data = energy_summary[~energy_summary['supply_period'].isin(
      ['Total', 'Average', 'Max', 'Min'])].copy()

  # Convert 'kwh' and 'kw' columns to strings first if they are not already
  # Then replace commas and convert back to numeric values
  monthly_data.loc[:, 'kwh'] = pd.to_numeric(
      monthly_data['kwh'].astype(str).str.replace(',', '', regex=False), errors='coerce').astype(float)
  monthly_data.loc[:, 'kw'] = pd.to_numeric(
      monthly_data['kw'].astype(str).str.replace(',', '', regex=False), errors='coerce').astype(float)

  # Find the highest values for setting axis limits
  # Round up to nearest 10,000
  max_kwh = np.ceil(monthly_data['kwh'].max() / 10000) * 10000
  # Round down to nearest 10,000
  min_kwh = np.floor(monthly_data['kwh'].min() / 10000) * 10000
  max_kw = monthly_data['kw'].max()
  min_kw = monthly_data['kw'].min()

  fig, ax1 = plt.subplots(figsize=(12, 7))

  # Bar plot for 'kwh' with thinner bars
  bar_width = 0.4
  bars = ax1.bar(
      monthly_data['supply_period'],
      monthly_data['kwh'],
      color='#F9A31C',
      label='kWh',
      width=bar_width)
  ax1.set_xlabel('Supply Period (Month)')
  ax1.set_ylabel('kWh', color='black')
  ax1.tick_params(axis='y', labelcolor='black')

  # Set kWh axis limits and ticks
  ax1.set_ylim(min_kwh - 10000, max_kwh)
  ax1.set_yticks(np.arange(min_kwh - 10000, max_kwh, 10000))

  # Add labels at the center of each bar's height for kWh values
  for bar in bars:
    label_y_position = min_kwh
    ax1.text(
        bar.get_x() + bar.get_width() / 2, label_y_position,
        f'{bar.get_height():,.2f}', ha='center', va='center', color='black', fontsize=10
    )

  # Secondary y-axis for 'kw' with line plot and markers
  ax2 = ax1.twinx()
  line, = ax2.plot(monthly_data['supply_period'],
                   monthly_data['kw'], color='#3E8E80', marker='o', label='kW')
  ax2.set_ylabel('kW', color='black')
  ax2.tick_params(axis='y', labelcolor='black')

  # Set kW axis limits and ticks
  ax2.set_ylim(100, max_kw + 100)
  ax2.set_yticks(np.arange(100, max_kw + 100, 100))

  # Add labels to each point for kW values with one decimal place
  for x, y in zip(monthly_data['supply_period'], monthly_data['kw']):
    ax2.text(x, y + 10, f'{y:,.2f}', ha='center',
             va='bottom', color='black', fontsize=10)

  # Configure grid: only horizontal lines, no vertical ones
  # Retain only horizontal grid lines
  plt.grid(axis='y', linestyle='-', linewidth=0.5)

  # Remove all the boarders
  ax1.spines['top'].set_visible(False)
  ax1.spines['right'].set_visible(False)
  ax1.spines['left'].set_visible(True)
  ax1.spines['bottom'].set_visible(True)
  ax2.spines['top'].set_visible(False)
  ax2.spines['right'].set_visible(False)
  ax2.spines['left'].set_visible(True)
  ax2.spines['bottom'].set_visible(True)

  # Title and layout adjustments
  plt.title('Monthly Energy Consumption (kWh) and Peak Demand (kW)')
  fig.tight_layout()

  # Save the plot as an image
  image_path = os.path.join(folder_path, 'energy_consumption.png')
  plt.savefig(image_path)
  plt.show()


def energy_behavior_plot(data):
  """
  Plots the energy behavior (Demand in kW) over the supply period.

  Parameters:
      data (pd.DataFrame): DataFrame containing at least 'datetime' and 'kw' columns.
  """
  plt.figure(figsize=(14, 7))
  plt.plot(
      data['datetime'],
      data['kw'],
      linestyle='-',
      color='orange',
      label='Demand (kW)')

  # Set title based on the actual date range in 'datetime', with start date
  # shifted by one month
  start_date = (
      data['datetime'].min() +
      pd.DateOffset(
          months=1)).strftime('%b-%y')
  end_date = data['datetime'].max().strftime('%b-%y')
  plt.title(
      f'Energy Behavior Over Supply Period: {start_date} to {end_date}')

  plt.xlabel('Date & Time')
  plt.ylabel('Demand (kW)')

  # Adjust the x-axis to show Month-Year format (e.g., May-24, Jun-24)
  plt.xticks(
      pd.date_range(
          start=data['datetime'].min(),
          end=data['datetime'].max(),
          freq='MS'),
      labels=pd.date_range(
          start=data['datetime'].min(),
          end=data['datetime'].max(),
          freq='MS').strftime('%b-%y')
  )

  # Configure grid: only horizontal lines, no vertical ones
  # Retain only horizontal grid lines
  plt.grid(axis='y', linestyle='-', linewidth=0.5)

  # Remove all borders
  plt.gca().spines['top'].set_visible(False)
  plt.gca().spines['right'].set_visible(False)
  plt.gca().spines['left'].set_visible(True)
  plt.gca().spines['bottom'].set_visible(True)

  # Add legend
  plt.legend()

  # Display the plot
  image_path = os.path.join(folder_path, 'energy_bevahior.png')
  plt.savefig(image_path)
  plt.show()


def plot_hourly_load_curve(hourly_summary, column_name='max',
                           unit='MW', ylabel='Peak Demand', ylim: list = None):
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
  ax.get_yaxis().set_major_formatter(
      plt.FuncFormatter(
          lambda x, loc: "{:,.2f}".format(x)))

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


def plot_hourly_by_day_load_curve(
        hourly_by_day_summary, column_name='max', unit='MW', ylabel='Peak Demand', ylim: list = None):
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
  ax.get_yaxis().set_major_formatter(
      plt.FuncFormatter(
          lambda x, loc: "{:,.2f}".format(x)))

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

  # Save the plot as an image in the specific folder
  image_path = os.path.join(folder_path,
                            'peak_demand_plot.png')  # Save to 'plots' folder
  plt.savefig(image_path)
  plt.show()


def hourly_load_table(hourly_by_day_summary, folder_path='image'):
  """
  Creates and displays a heatmap table of the hourly load curve by day.

  Parameters:
      hourly_by_day_summary (DataFrame): The summarized hourly load data.
      folder_path (str): Directory to save the heatmap image (default: 'image').
  """
  import matplotlib.pyplot as plt
  import numpy as np
  import seaborn as sns
  import matplotlib.colors as mcolors
  import os  # For directory handling

  # Define the new color map based on the provided colors
  cmap = mcolors.LinearSegmentedColormap.from_list(
      "", ["#63BE7B", "#FFEB84", "#F8696B"]  # Custom colors for the heatmap
  )

  # Define weekday labels
  weekday_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

  # Make sure the directory exists; if not, create it
  if not os.path.exists(folder_path):
    os.makedirs(folder_path)

  # Display the hourly load curve by day as a heatmap table with the new color map
  plt.figure(figsize=(15, 7))
  ax = sns.heatmap(
      hourly_by_day_summary,
      annot=True,
      fmt=".2f",
      cmap=cmap,  # Use the updated colormap
      cbar_kws={'label': 'Load (kW)'}
  )

  # Move x-axis labels to the top
  ax.xaxis.set_ticks_position('top')

  # Set custom labels for the x-axis on top with centered alignment
  ax.set_xticks(np.arange(len(weekday_labels)) + 0.5)
  ax.set_xticklabels(weekday_labels, rotation=0, ha='center')

  # Rotate y-axis (hour) labels to make them vertical
  ax.set_yticklabels(ax.get_yticklabels(), rotation=0, ha='center')

  plt.xlabel("Day", fontsize=15)  # X-axis title at the top
  plt.ylabel("Hour", fontsize=15)  # Y-axis title

  plt.title("Hourly Load Curve by Day (kW)", fontsize=16, pad=20)  # Add padding to title

  # Save the plot as an image in the specified folder
  image_path = os.path.join(folder_path, 'hourly_load_curve.png')
  plt.savefig(image_path)
  plt.show()


def plot_demand_and_consumption_WESM(data):
  """
  Plots hourly average demand (kW) and consumption (kWh) against WESM average.

  Parameters:
  - data (DataFrame): DataFrame containing 'hour', 'kwh', 'kw', and 'wesm' columns.
  """

  # Ensure 'kwh', 'kw', and 'wesm' columns are numeric
  # Ensure 'kwh', 'kw', and 'wesm' columns are numeric
  data['kwh'] = pd.to_numeric(data['kwh'], errors='coerce')
  data['kw'] = pd.to_numeric(data['kw'], errors='coerce')
  data['wesm'] = pd.to_numeric(data['wesm'], errors='coerce')

  # Group by the 'hour' column and calculate the mean for 'kw', 'kwh', and
  # 'wesm'
  hourly_data = data.groupby('hour')[['kw', 'kwh', 'wesm']].mean()

  # Plotting
  fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

  # First plot: Hourly Average Demand (kW) vs. WESM Average
  ax1.plot(
      hourly_data.index,
      hourly_data['kw'],
      color='orange',
      label='Hourly Average Demand (kW)')
  ax1.set_ylabel('Demand (kW)', color='black')
  ax1.tick_params(axis='y', labelcolor='black')
  ax1.set_xticks(range(1, 25))  # Set x-axis ticks from 1 to 24
  ax1.set_xticklabels(range(1, 25))  # Label x-axis ticks from 1 to 24

  # Remove plot borders (spines) for the first plot
  for spine in ax1.spines.values():
    spine.set_visible(False)

  # Second y-axis for WESM on the right for the first plot
  ax1_twin = ax1.twinx()
  ax1_twin.plot(
      hourly_data.index,
      hourly_data['wesm'],
      color='blue',
      label='WESM Average')
  ax1_twin.set_ylabel('WESM', color='black')
  ax1_twin.tick_params(axis='y', labelcolor='black')

  # Remove the spines around the second y-axis as well
  for spine in ax1_twin.spines.values():
    spine.set_visible(False)

  # Title and legends for the first plot
  ax1.set_title('Hourly Average Demand vs. WESM Average')
  ax1.legend(loc="upper left")  # Add legend inside the first plot
  # Add legend inside the right y-axis for WESM
  ax1_twin.legend(loc="upper right")

  # Enable only horizontal grid lines for the first plot
  ax1.grid(True, axis='y')

  # Second plot: Hourly Average Consumption (kWh) vs. WESM Average
  ax2.plot(
      hourly_data.index,
      hourly_data['kwh'],
      color='orange',
      label='Hourly Average Consumption (kWh)')
  ax2.set_xlabel('Hour (1-24)')
  ax2.set_ylabel('Consumption (kWh)', color='black')
  ax2.tick_params(axis='y', labelcolor='black')
  ax2.set_xticks(range(1, 25))  # Set x-axis ticks from 1 to 24
  ax2.set_xticklabels(range(1, 25))  # Label x-axis ticks from 1 to 24

  # Remove plot borders (spines) for the second plot
  for spine in ax2.spines.values():
    spine.set_visible(False)

  # Second y-axis for WESM on the right for the second plot
  ax2_twin = ax2.twinx()
  ax2_twin.plot(
      hourly_data.index,
      hourly_data['wesm'],
      color='blue',
      label='WESM Average')
  ax2_twin.set_ylabel('WESM', color='black')
  ax2_twin.tick_params(axis='y', labelcolor='black')

  # Remove the spines around the second y-axis for the second plot
  for spine in ax2_twin.spines.values():
    spine.set_visible(False)

  # Title and legends for the second plot
  ax2.set_title('Hourly Average Consumption vs. WESM Average')
  ax2.legend(loc="upper left")  # Add legend inside the second plot
  # Add legend inside the right y-axis for WESM
  ax2_twin.legend(loc="upper right")

  # Enable only horizontal grid lines for the second plot
  ax2.grid(True, axis='y')

  # Adjust layout to add spacing between the plots
  plt.tight_layout()
  # Adjust vertical space between the two plots
  plt.subplots_adjust(hspace=0.5)

  # Show the plots
  image_path = os.path.join(folder_path, 'demand_consumption_wesm.png')
  plt.savefig(image_path)
  plt.show()


def generate_daily_report(client_data, values_column='kw', wesm_column='wesm'):
  """
  Generate daily kW and WESM reports and display them as a heatmap.

  Args:
      client_data (pd.DataFrame): Input DataFrame with required columns (e.g., 'hour', 'kw', 'wesm').
      values_column (str): Column name for kW values. Default is 'kw'.
      wesm_column (str): Column name for WESM values. Default is 'wesm'.
      folder_path (str): Path to the folder where the heatmap image will be saved. Default is 'image'.
  """
  # Generate daily kW report
  daily_kw_report = pd.pivot_table(
      client_data,
      index='hour',
      values=values_column,
      aggfunc=['mean', 'max', 'min', 'sum'],
      sort=False,
      margins=True,
      margins_name='Grand Total'
  ).reset_index()

  # Drop extra level in columns and convert 'hour' to string
  daily_kw_report.columns = daily_kw_report.columns.droplevel(1)
  daily_kw_report['hour'] = daily_kw_report['hour'].astype(str)

  # Generate daily WESM report
  daily_wesm_report = pd.pivot_table(
      client_data,
      index='hour',
      values=wesm_column,
      aggfunc='mean',
      sort=False,
      margins=True,
      margins_name='Grand Total'
  ).reset_index()
  daily_wesm_report['hour'] = daily_wesm_report['hour'].astype(str)

  # Calculate % of Consumption
  daily_kw_report['% of Consumption'] = daily_kw_report['sum'] / daily_kw_report.loc[
      daily_kw_report['hour'] == 'Grand Total', 'sum'
  ].values[0] * 100

  # Merge kW and WESM reports
  daily_kw_report = daily_kw_report.merge(daily_wesm_report, on='hour', how='left')
  daily_kw_report.columns = ['Hour', 'Mean', 'Max', 'Min', 'Sum', '% of Consumption', 'WESM']

  # Trim the report to remove "Grand Total"
  daily_kw_report_trimmed = daily_kw_report[daily_kw_report['Hour'] != 'Grand Total']

  # Create output folder if it doesn't exist
  if not os.path.exists(folder_path):
    os.makedirs(folder_path)

  # Define a custom colormap for the heatmap
  cmap = mcolors.LinearSegmentedColormap.from_list(
      "", ["#63BE7B", "#FFEB84", "#F8696B"]
  )

  # Helper function to normalize data
  def normalize_column(column):
    return (column - column.min()) / (column.max() - column.min())

  # Display the report as a heatmap
  def display_table_as_heatmap(report):
    numeric_columns = ['Mean', 'Max', 'Min', 'Sum', '% of Consumption', 'WESM']

    # Normalize each column separately
    normalized_data = report[numeric_columns].apply(normalize_column, axis=0)

    # Format annotations with commas and two decimal places
    formatted_annotations = report[numeric_columns].apply(lambda col: col.map(lambda x: f"{x:,.2f}"))

    # Create a heatmap
    plt.figure(figsize=(15, 7))
    ax = sns.heatmap(
        normalized_data,
        annot=formatted_annotations,
        fmt="s",
        cmap=cmap,
        yticklabels=np.arange(1, 25),
        xticklabels=numeric_columns
    )

    # Customize axes and title
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    ax.yaxis.set_tick_params(rotation=0)

    plt.title("Daily kW Report", fontsize=16, pad=20)
    plt.ylabel("Hour", fontsize=15)
    plt.xlabel("Metrics", fontsize=15)

    # Save the heatmap
    image_path = os.path.join(folder_path, 'daily_kw_report.png')
    plt.savefig(image_path, bbox_inches='tight', format='png')
    plt.show()

  # Display the heatmap
  display_table_as_heatmap(daily_kw_report_trimmed)
