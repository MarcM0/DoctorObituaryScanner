# Doctor Obituary Scanner
Script to obituaries of doctors in different specialties in the PMC https://www.ncbi.nlm.nih.gov/pmc database. The search query was ```(("deaths"[Title] OR obituaries[Title])) AND ("CMAJ"[Journal])```. 
Input data not provided due to copyright.
If you wish to rerun the program, follow the instructions below.

To run:
- Delete the "Output" folder
- Gather the necessary data in a "Data" folder full of csv's
- Install python 3.11 (https://www.python.org/downloads/release/python-3110/). 
- Then, in the terminal, run
```
cd <path where you checked out this repository>
python -m pip install pandas==1.5.2 numpy==1.24.1
python specialtyAgeScanner.py
```
The results will appear in a folder called "Output"

You can also get some extra data needed for the study using different combinations of values in the first few lines of specialtyAgeScanner.py
```
checkingProfession = True
checkingYear = True
```

