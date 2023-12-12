import subprocess
import os

directory_path = "/Users/markbaggett/metadata/wallace/cleaned-data/modsxml/compounds/real"
output_path = "/Users/markbaggett/metadata/wallace/cleaned-data/modsxml/compounds/real_dc"
transform = "/Users/markbaggett/PycharmProjects/dumptruck/transform.xsl"
saxon = "/Users/markbaggett/PycharmProjects/dumptruck/saxon.jar"
for filename in os.listdir(directory_path):
    if os.path.isfile(os.path.join(directory_path, filename)):
        # Build the full path to the file
        file_path = os.path.join(directory_path, filename)
        command = f"java -jar {saxon} {file_path} {transform} > {output_path}/{filename}"
        # Run the command on the file
        subprocess.run(f"{command}", shell=True)
        print(command)