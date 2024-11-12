import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt

fm.fontManager.addfont(
  './assets/Poppins-Regular.ttf')

# Get list of days of the week
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

import pandas as pd

def load_data(data):
    """
    Process energy data by ensuring kWh and kW columns are present and named consistently.
    
    Parameters:
    - data (DataFrame): Input DataFrame containing energy data with datetime and kWh/kW columns.
    
    Returns:
    - DataFrame: Modified DataFrame with 8th column named 'kwh' and 9th column named 'kw'.
    """
    
    # Ensure datetime is in correct format
    data['datetime'] = pd.to_datetime(data['datetime'])

    # Determine column indices: 8th column (index 7) for kwh and 9th column (index 8) for kw
    kwh_column_idx = 7
    kw_column_idx = 8

    # Check datetime interval to determine if it's 5-minute or 1-hour data
    time_diff = data['datetime'].diff().dt.total_seconds().median()
    frequency = 12 if time_diff == 300 else 1  # 5-minute interval if median diff is 300 seconds, otherwise 1 hour

    # Check the number of columns in the DataFrame
    num_columns = data.shape[1]

    # Handling 5-minute data
    if frequency == 12:  # 5-minute interval
        if num_columns == 8:
            # If 8th column is labeled 'kw', rename it to 'kwh' and compute 'kw' as 8th * 12
            if data.columns[kwh_column_idx].lower() == 'kw':
                data.rename(columns={data.columns[kwh_column_idx]: 'kwh'}, inplace=True)
                data['kw'] = data['kwh'] * 12
            else:
                # If 8th column is already 'kwh', compute 'kw' as 8th * 12
                data['kw'] = data.iloc[:, kwh_column_idx] * 12
                data.rename(columns={data.columns[kwh_column_idx]: 'kwh'}, inplace=True)
        
        elif num_columns == 9:
            # Rename the 8th and 9th columns as 'kwh' and 'kw'
            data.rename(columns={data.columns[kwh_column_idx]: 'kwh', data.columns[kw_column_idx]: 'kw'}, inplace=True)

    # Handling 1-hour data
    elif frequency == 1:  # 1-hour interval
        if num_columns == 8:
            # Copy the 8th column to the 9th as 'kw' and rename the columns
            data['kw'] = data.iloc[:, kwh_column_idx]
            data.rename(columns={data.columns[kwh_column_idx]: 'kwh', 'kw': 'kw'}, inplace=True)
            
        elif num_columns == 9:
            # Ensure the 8th and 9th columns are the same
            if not (data.iloc[:, kwh_column_idx] == data.iloc[:, kw_column_idx]).all():
                print("Warning: 8th and 9th columns do not match.")
            # Rename the columns as 'kwh' and 'kw'
            data.rename(columns={data.columns[kwh_column_idx]: 'kwh', data.columns[kw_column_idx]: 'kw'}, inplace=True)

    return data

def generate_energy_summary(data, datetime_column='datetime', kwh_column='kwh', kw_column='kw'):
    # Determine the frequency based on the time intervals in the datetime column
    interval_seconds = data[datetime_column].diff().dt.total_seconds().median()
    frequency = 12 if interval_seconds == 300 else 1  # 12 for 5 minutes, 1 for 1 hour

    # Group by supply period and aggregate the necessary columns
    energy_summary = data.groupby("supply period", sort=False).agg({
        "supply period": "count",
        kwh_column: "sum",
        kw_column: "max"
    })

    # Rename columns for readability
    energy_summary.columns = ["number of intervals", "kwh", "kw"]

    # Calculate 'number of hours' based on frequency and drop 'number of intervals'
    energy_summary["number of hours"] = energy_summary["number of intervals"] / frequency
    energy_summary.drop(columns=["number of intervals"], inplace=True)

    # Add a total row with the sum of kWh and the max of kW
    energy_summary.loc["Total"] = energy_summary.sum()
    energy_summary.loc["Total", "kw"] = energy_summary.iloc[:-1]["kw"].max()

    # Calculate the load factor
    energy_summary["load factor"] = (energy_summary["kwh"] / (energy_summary['kw'] * energy_summary["number of hours"])) * 100

    # Create a copy of the summary data without the Total row for statistics
    original_energy_summary = energy_summary.iloc[:-1].copy()

    # Add Average, Max, Min rows based on the original data (excluding 'Total')
    energy_summary.loc["Average"] = original_energy_summary.mean()
    energy_summary.loc["Max"] = original_energy_summary.max()
    energy_summary.loc["Min"] = original_energy_summary.min()

    # Reset index to remove 'supply period' from being the index
    energy_summary = energy_summary.reset_index()

    # Reorder columns as specified
    energy_summary = energy_summary[["supply period", "number of hours", "kwh", "kw", "load factor"]]

    # Format columns to display numbers with 2 decimal places and comma separators
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
  ax.spines['left'].set_visible(True)
  ax.spines['bottom'].set_visible(True)

  # Add gray horizontal gridlines
  ax.yaxis.grid(color='gray', linestyle='-', linewidth=0.25)

  # Remove y-axis ticks only (keep labels)
  ax.tick_params(axis='y', which='both', left=False)

  # Remove x-axis ticks only (keep labels)
  ax.tick_params(axis='x', which='both', bottom=False)

  plt.show()

def save_energy_consumption_plot(energy_summary):
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    # Filter out rows labeled 'Total', 'Average', 'Max', or 'Min'
    monthly_data = energy_summary[~energy_summary['supply period'].isin(['Total', 'Average', 'Max', 'Min'])]

    # Convert 'kwh' and 'kw' columns back to numeric since they're currently formatted as strings with commas
    monthly_data['kwh'] = monthly_data['kwh'].str.replace(',', '').astype(float)
    monthly_data['kw'] = monthly_data['kw'].str.replace(',', '').astype(float)

    # Find the highest values for setting axis limits
    max_kwh = monthly_data['kwh'].max()
    max_kw = monthly_data['kw'].max()
    
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Bar plot for 'kwh' with thinner bars
    bar_width = 0.4
    bars = ax1.bar(monthly_data['supply period'], monthly_data['kwh'], color='#F9A31C', label='kWh', width=bar_width)
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
    line, = ax2.plot(monthly_data['supply period'], monthly_data['kw'], color='#3E8E80', marker='o', label='kW')
    ax2.set_ylabel('kW', color='black')
    ax2.tick_params(axis='y', labelcolor='black')

    # Set kW axis limits and ticks
    ax2.set_ylim(100, max_kw + 100)
    ax2.set_yticks(np.arange(100, max_kw + 100, 100))

    # Add labels to each point for kW values with one decimal place
    for x, y in zip(monthly_data['supply period'], monthly_data['kw']):
        ax2.text(x, y + 10, f'{y:,.2f}', ha='center', va='bottom', color='black', fontsize=10)

    # Configure grid: only horizontal lines, no vertical ones
    plt.grid(axis='y', linestyle='-', linewidth=0.5)  # Retain only horizontal grid lines

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
    plt.show()

    # Save the plot as an image
    #plt.savefig('energy_consumption_plot.png', bbox_inches='tight')
    #plt.close(fig)  # Close the plot to free up memory
    #print(f"Energy consumption plot saved as {output_path}")

import pandas as pd

def loadfactor_table(energy_summary):
    """
    Prepares a transposed table of load factors with each supply period as a column.
    
    Parameters:
    - energy_summary (DataFrame): Original energy summary data containing columns 'supply period' and 'load factor'.
    
    Returns:
    - DataFrame: Transposed table with load factors as percentages for each supply period.
    """
    
    # Filter out rows with labels 'Total', 'Average', 'Max', or 'Min' in the 'supply period' column
    filtered_energy_summary = energy_summary[~energy_summary['supply period'].isin(['Total', 'Average', 'Max', 'Min'])]
    
    # Select relevant columns and set 'supply period' as the index
    months_load_factor = filtered_energy_summary[['supply period', 'load factor']].copy()
    months_load_factor.set_index('supply period', inplace=True)
    
    # Convert 'load factor' to numeric (float) if it's in string format, handle errors by coercion
    months_load_factor['load factor'] = pd.to_numeric(months_load_factor['load factor'], errors='coerce')
    
    # Remove any rows with NaN values in 'load factor'
    months_load_factor.dropna(subset=['load factor'], inplace=True)
    
    # Format the load factor as a percentage, rounding to two decimal places
    months_load_factor['load factor'] = months_load_factor['load factor'].round(2).astype(str) + '%'
    
    # Transpose the DataFrame so each supply period becomes a column
    transposed_table = months_load_factor.T
    
    return transposed_table

def energy_behavior_plot(data):
    """
    Plots the energy behavior (Demand in kW) over the supply period.
    
    Parameters:
        data (pd.DataFrame): DataFrame containing at least 'datetime' and 'kw' columns.
    """
    plt.figure(figsize=(14, 7))
    plt.plot(data['datetime'], data['kw'], linestyle='-', color='orange', label='Demand (kW)')
    
    # Set title based on the actual date range in 'datetime', with start date shifted by one month
    start_date = (data['datetime'].min() + pd.DateOffset(months=1)).strftime('%b-%y')
    end_date = data['datetime'].max().strftime('%b-%y')
    plt.title(f'Energy Behavior Over Supply Period: {start_date} to {end_date}')
    
    plt.xlabel('Date & Time')
    plt.ylabel('Demand (kW)')
    
    # Adjust the x-axis to show Month-Year format (e.g., May-24, Jun-24)
    plt.xticks(
        pd.date_range(start=data['datetime'].min(), end=data['datetime'].max(), freq='MS'),
        labels=pd.date_range(start=data['datetime'].min(), end=data['datetime'].max(), freq='MS').strftime('%b-%y')
    )

    # Configure grid: only horizontal lines, no vertical ones
    plt.grid(axis='y', linestyle='-', linewidth=0.5)  # Retain only horizontal grid lines
    
    # Remove all borders
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(True)
    plt.gca().spines['bottom'].set_visible(True)
    
    # Add legend
    plt.legend()
    
    # Display the plot
    plt.tight_layout()
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
 
    # Group by the 'hour' column and calculate the mean for 'kw', 'kwh', and 'wesm'
    hourly_data = data.groupby('hour')[['kw', 'kwh', 'wesm']].mean()
 
    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
 
    # First plot: Hourly Average Demand (kW) vs. WESM Average
    ax1.plot(hourly_data.index, hourly_data['kw'], color='orange', label='Hourly Average Demand (kW)')
    ax1.set_ylabel('Demand (kW)', color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.set_xticks(range(1, 25))  # Set x-axis ticks from 1 to 24
    ax1.set_xticklabels(range(1, 25))  # Label x-axis ticks from 1 to 24
 
    # Remove plot borders (spines) for the first plot
    for spine in ax1.spines.values():
        spine.set_visible(False)
 
    # Second y-axis for WESM on the right for the first plot
    ax1_twin = ax1.twinx()
    ax1_twin.plot(hourly_data.index, hourly_data['wesm'], color='blue', label='WESM Average')
    ax1_twin.set_ylabel('WESM', color='black')
    ax1_twin.tick_params(axis='y', labelcolor='black')
 
    # Remove the spines around the second y-axis as well
    for spine in ax1_twin.spines.values():
        spine.set_visible(False)
 
    # Title and legends for the first plot
    ax1.set_title('Hourly Average Demand vs. WESM Average')
    ax1.legend(loc="upper left")  # Add legend inside the first plot
    ax1_twin.legend(loc="upper right")  # Add legend inside the right y-axis for WESM
 
    # Enable only horizontal grid lines for the first plot
    ax1.grid(True, axis='y')
 
    # Second plot: Hourly Average Consumption (kWh) vs. WESM Average
    ax2.plot(hourly_data.index, hourly_data['kwh'], color='orange', label='Hourly Average Consumption (kWh)')
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
    ax2_twin.plot(hourly_data.index, hourly_data['wesm'], color='blue', label='WESM Average')
    ax2_twin.set_ylabel('WESM', color='black')
    ax2_twin.tick_params(axis='y', labelcolor='black')
 
    # Remove the spines around the second y-axis for the second plot
    for spine in ax2_twin.spines.values():
        spine.set_visible(False)
 
    # Title and legends for the second plot
    ax2.set_title('Hourly Average Consumption vs. WESM Average')
    ax2.legend(loc="upper left")  # Add legend inside the second plot
    ax2_twin.legend(loc="upper right")  # Add legend inside the right y-axis for WESM
 
    # Enable only horizontal grid lines for the second plot
    ax2.grid(True, axis='y')
 
    # Adjust layout to add spacing between the plots
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.5)  # Adjust vertical space between the two plots
 
    # Show the plots
    plt.show()  
    
def generate_daily_kw_report(data):
    """
    Generates a daily kW report with mean, max, min, sum, % of consumption, and WESM values,
    and styles it with a heatmap.

    Parameters:
    - data (DataFrame): DataFrame containing 'hour', 'kw', and 'wesm' columns.

    Returns:
    - styled_daily_kw_report (Styler): A styled pandas DataFrame with a heatmap.
    """
    
    # Define the value to calculate in the pivot table
    values = 'kw'  # Adjust this if you want a different column
    
    # Calculate the daily kW report
    daily_kw_report = pd.pivot_table(
        data,
        index='hour',
        values=values,
        aggfunc=['mean', 'max', 'min', 'sum'],
        sort=False,
        margins=True,
        margins_name='Grand Total'
    ).reset_index()
    
    # Drop the extra level in the columns and convert 'hour' to string
    daily_kw_report.columns = daily_kw_report.columns.droplevel(1)
    daily_kw_report['hour'] = daily_kw_report['hour'].astype(str)
    
    # Calculate the daily WESM report
    daily_wesm_report = pd.pivot_table(
        data,
        index='hour',
        values='wesm',
        aggfunc='mean',
        sort=False,
        margins=True,
        margins_name='Grand Total'
    ).reset_index()
    daily_wesm_report['hour'] = daily_wesm_report['hour'].astype(str)
    
    # Calculate % of consumption
    daily_kw_report['% of Consumption'] = daily_kw_report['sum'] / daily_kw_report.loc[
        daily_kw_report['hour'] == 'Grand Total', 'sum'
    ].values[0] * 100
    
    # Merge the reports
    daily_kw_report = daily_kw_report.merge(daily_wesm_report, on='hour', how='left')
    daily_kw_report.columns = ['Hour', 'Mean', 'Max', 'Min', 'Sum', '% of Consumption', 'WESM']
    
    # Ensure all relevant columns are numeric for the heatmap to work
    numeric_columns = ['Mean', 'Max', 'Sum', '% of Consumption', 'WESM']
    daily_kw_report[numeric_columns] = daily_kw_report[numeric_columns].apply(pd.to_numeric, errors='coerce')
    
    # Define a custom colormap for the heatmap
    cmap = mcolors.LinearSegmentedColormap.from_list("", ["#63BE7B", "#FFEB84", "#F8696B"])
    
    # Style the table and exclude the entire last row from the heatmap
    styled_daily_kw_report = daily_kw_report.style.background_gradient(
        cmap=cmap,
        subset=pd.IndexSlice[:23, ['Mean', 'Max', 'Sum', '% of Consumption', 'WESM']]
    ).format(
        formatter={
            'Mean': '{:,.4f}',
            'Min': '{:,.4f}',
            'Max': '{:,.4f}',
            'Sum': '{:,.4f}',
            '% of Consumption': '{:,.4f}%',
            'WESM': '{:,.4f}'
        }
    )
    
    return styled_daily_kw_report


