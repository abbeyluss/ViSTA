import google.generativeai as genai
import os
import PIL.Image
import re
import time
import csv
from google.generativeai import upload_file

"""
Processes a given image (if tif formatted, converts it to jpg), and uploads it to the Gemini API as a JPEG
Inputs:
    - file_path: name of the folder where the tif_img resides, as well as where you want the images to be saved
    - tif_img: name of the individual tif file to be processed
Outputs:
    - img: variable that holds the processed image ready to be inputted into the model
    - 
"""
def process_image(file_path,tif_img):
    with PIL.Image.open(f"../{file_path}/{tif_img}") as img:
        img.save(f"../{file_path}/Test.jpeg", 'JPEG', quality=50)
    file_path = f"../{file_path}/Test.jpeg"
    return genai.upload_file(file_path)


"""
Extracts the photographer name, dates and the raw transcription from the given text 
Inputs:
    - text: text from the transcribed back
Outputs:
    - name: photographer name
    - dates: date(s) 
    - raw_text: raw transcription
"""
def extract_details(text):

    name_match = re.search(r'Name:(.*)', text)
    name = name_match.group(1).strip() if name_match else None


    dates_match = re.search(r'Date:\[(.*?)\]', text)
    dates = dates_match.group(1).split(', ') if dates_match else []

    raw_match = re.search(r'Raw:(.*)', text, re.DOTALL)
    raw_text = raw_match.group(1).strip() if raw_match else None

    return name, dates, raw_text


"""
Compiles all of the data generated from the script to be appended to a csv file
Inputs:
    - image_title: The images file name aka UASC Identifier
    - title: title for the image generated by Gemini
    - abstract: abstract for the image generated by Gemini
    - photographer_name: name of the photographer (if processed from transcription)
    - dates: list of the dates provided (if processed from transcription)
    - transcription: raw transcription
Outputs:
"""
def compile_data(image_title,title,abstract,photographer_name="",dates=[""],transcription=""):
    secondary_date = ""
    if len(dates)>1:
        secondary_date = dates[1]
        primary_date = dates[0]
    elif len(dates) == 0:
        primary_date = "No Date was able to be transcribed"
    else:
        primary_date = dates[0]
    return [image_title,title,abstract,photographer_name,primary_date,secondary_date,transcription]

#Configure the Gemini Model API
GOOG_KEY =   os.environ.get("GOOG_KEY")
genai.configure(api_key = GOOG_KEY)
generation_config= genai.GenerationConfig(temperature=0)
model = genai.GenerativeModel("gemini-1.5-pro",generation_config=generation_config)

img_file_path = "Test_Images"
image_front = "Test_11.jpg"


image_back = "Test_10Back.jpg"

#Process the back of the photo
img = process_image(img_file_path,image_back)

prompt = ""
with open("../transcription_prompt.txt", "r") as file:
    prompt = file.read()

#Make request to transcribe the image
response = model.generate_content(contents=[prompt,img])
transcription = response.text

name, dates, raw_text = extract_details(transcription)
time.sleep(4) #To mitigate concurrent request issues
#TODO : - Replace Commas within raw_text with something of Drew's choosing.


img = process_image(img_file_path,image_front)
with open("../title_prompt.txt", "r") as file:
    prompt = file.read()

title_prompt = prompt #+ raw_text

#Make request to generate the title
response = model.generate_content(contents=[title_prompt,img])
title = response.text
print(title)
time.sleep(4)

#Make request to generate the abstract
with open("../abstract_prompt.txt", "r") as file:  # Load up the prompt from the abstract_prompt.txt file
    prompt = file.read()

#Add raw context to the general prompt
abstract_prompt = prompt #+ raw_text

#Generate the abstract
response = model.generate_content(contents=[abstract_prompt,img])
abstract = response.text
print(abstract)

#Add the generated title and abstract + photographer name, dates, and transcription to the csv file
#with open("A|B_Test.csv", mode='a', newline='') as file:
    #writer = csv.writer(file)
    #title[7:] and abstract[10:] signify removing the Title portion of the "Title: 'actual title contents'"
    #data = compile_data(image_front,title[7:],abstract[10:],name,dates,raw_text)
    #writer.writerow(data)

