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
from processing import generate_ppt  # Importing the function from utils.py


# Get the current working directory where the Jupyter notebook is running
current_dir = os.getcwd()

# Define the relative paths for images
image_folder = os.path.join(current_dir, 'image')

# Define the image folder and template path
template_path = 'solx.pptx'

# Define the folder where the generated PowerPoint files will be stored
PPT_FOLDER = "generated_ppts"

# Create PPT_FOLDER if it doesn't exist
if not os.path.exists(PPT_FOLDER):
  os.makedirs(PPT_FOLDER)

app = FastAPI()

# Define the API route to generate the PowerPoint


@app.get("/generate_ppt/{client_name}")
async def generate_ppt_endpoint(client_name: str):
  client_name = str(client_name).strip()

  if not client_name:
    raise HTTPException(status_code=400, detail="Client name cannot be empty")

  try:
    # Generate PowerPoint report
    ppt_path = generate_ppt(client_name, image_folder='image', template_path='solx.pptx')

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
