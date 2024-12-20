import sys
import os


import shutil
import random
import numpy as np
import pandas as pd
from datetime import date


import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import pandas.plotting as pd_plotting


from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from database import fetch_client_load_profile
from processing import (generate_ppt,
                        process_data_and_generate_summary)  # Importing the function from utils.py
from utils import (energy_consumption_plot,
                   energy_behavior_plot,
                   generate_hourly_load_curve,
                   generate_hourly_load_heatmap,
                   plot_demand_and_consumption_WESM,
                   generate_daily_report)


# Define the template path
template_path = 'solx.pptx'

# Define the folder where the generated PowerPoint files will be stored
PPT_FOLDER = "generated_ppts"

# Create PPT_FOLDER if it doesn't exist
if not os.path.exists(PPT_FOLDER):
  os.makedirs(PPT_FOLDER)

folder_path = 'image'  # Global folder path

if not os.path.exists(folder_path):
  os.makedirs(folder_path)

app = FastAPI()


@app.get("/plots/energy_consumption/{client_name}")
async def plot_energy_consumption(client_name: str):
  """
  Generate and return the energy consumption plot for a specific client.
  """
  try:
    # Fetch and process data
    processed_data, _ = process_data_and_generate_summary(client_name)

    # Generate plot
    path = energy_consumption_plot(processed_data, folder_path)
    if not os.path.exists(path):
      raise HTTPException(status_code=500, detail="Failed to generate energy consumption plot.")

    # Return the saved image as a response
    return FileResponse(path, media_type="image/png")

  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))  # Specific client not found
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/plots/energy_behavior/{client_name}")
async def plot_energy_behavior(client_name: str):
  """
  Generate and return the energy consumption plot for a specific client.
  """
  try:
    # Fetch and process data
    processed_data, _ = process_data_and_generate_summary(client_name)

    # Generate plot
    path = energy_behavior_plot(processed_data, folder_path)
    if not os.path.exists(path):
      raise HTTPException(status_code=500, detail="Failed to generate energy consumption plot.")

    # Return the saved image as a response
    return FileResponse(path, media_type="image/png")

  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))  # Specific client not found
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/plots/hour_load_curve/{client_name}")
async def plot_hourly_load_curve(client_name: str):
  """
  Generate and return the energy consumption plot for a specific client.
  """
  try:
    # Fetch and process data
    processed_data, _ = process_data_and_generate_summary(client_name)

    # Generate plot
    path = generate_hourly_load_curve(processed_data, folder_path, column_name='max',
                                      unit='kW', ylabel='Peak Demand', ylim=None)
    if not os.path.exists(path):
      raise HTTPException(status_code=500, detail="Failed to generate energy hourly load curve.")

    # Return the saved image as a response
    return FileResponse(path, media_type="image/png")

  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))  # Specific client not found
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/plots/hour_load_heatmap/{client_name}")
async def plot_hourly_load_heatmap(client_name: str):
  """
  Generate and return the energy consumption plot for a specific client.
  """
  try:
    # Fetch and process data
    processed_data, _ = process_data_and_generate_summary(client_name)

    # Generate plot
    path = generate_hourly_load_heatmap(processed_data, folder_path='image')
    if not os.path.exists(path):
      raise HTTPException(status_code=500, detail="Failed to generate hourly load heatmap.")

    # Return the saved image as a response
    return FileResponse(path, media_type="image/png")

  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))  # Specific client not found
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/plots/generate_demand_and_consumption_WESM/{client_name}")
async def generate_demand_and_consumption_WESM(client_name: str):
  """
  Generate and return the energy consumption plot for a specific client.
  """
  try:
    # Fetch and process data
    client_data = fetch_client_load_profile(client_name)

    # Generate plot
    path = plot_demand_and_consumption_WESM(client_data, folder_path='image')
    if not os.path.exists(path):
      raise HTTPException(status_code=500, detail="Failed to plot_demand_and_consumption_WESM.")

    # Return the saved image as a response
    return FileResponse(path, media_type="image/png")

  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))  # Specific client not found
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/plots/plot_daily_report/{client_name}")
async def plot_daily_report(client_name: str):
  """
  Generate and return the energy consumption plot for a specific client.
  """
  try:
    # Fetch and process data
    client_data = fetch_client_load_profile(client_name)

    # Generate plot
    path = generate_daily_report(
       client_data,        # Your input DataFrame
       values_column='kw',             # Column name for kW values
       wesm_column='wesm',
        folder_path='image'        # Column name for WESM values
    )

    if not os.path.exists(path):
      raise HTTPException(status_code=500, detail="Failed to generate daily report.")

    # Return the saved image as a response
    return FileResponse(path, media_type="image/png")

  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))  # Specific client not found
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/generate_ppt/{client_name}")
async def generate_ppt_endpoint(client_name: str):
  client_name = str(client_name).strip()

  if not client_name:
    raise HTTPException(status_code=400, detail="Client name cannot be empty")

  try:
    # Generate PowerPoint report
    ppt_path = generate_ppt(client_name, folder_path='image', template_path='solx.pptx')

    # Ensure the generated PowerPoint file exists before moving it
    if not os.path.exists(ppt_path):
      raise HTTPException(status_code=500, detail="Generated PowerPoint file does not exist.")

    # Move the generated PPT to the designated folder
    final_ppt_path = os.path.join(PPT_FOLDER, os.path.basename(ppt_path))
    os.rename(ppt_path, final_ppt_path)

    # Return the PowerPoint file as a response
    return FileResponse(final_ppt_path,
                        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        filename=os.path.basename(final_ppt_path))

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
