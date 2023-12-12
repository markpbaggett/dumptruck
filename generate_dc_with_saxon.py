import subprocess
import os

directory_path = "/Users/markbaggett/metadata/delaney/cleaned_data/bookLevelRecords/mark_metadata"
output_path = "/Users/markbaggett/metadata/delaney/cleaned_data/bookLevelRecords/mark_dc"
transform = "/Users/markbaggett/PycharmProjects/dumptruck/transform.xsl"
saxon = "/Users/markbaggett/PycharmProjects/dumptruck/saxon.jar"

# Define the command you want to ru
# Example: command = "convert -resize 50% input.jpg output.jpg"

# Directory containing the files

# Loop through the files in the directory
for filename in os.listdir(directory_path):
    if os.path.isfile(os.path.join(directory_path, filename)):
        # Build the full path to the file
        file_path = os.path.join(directory_path, filename)
        command = f"java -jar {saxon} {file_path} {transform} > {output_path}/{filename}"
        # Run the command on the file
        subprocess.run(f"{command}", shell=True)
        print(command)