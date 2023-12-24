import re
import csv
import os
import pandas as pd
import numpy as np
import json
import time
import datetime
import traceback

# professionsMissed = []
# commonCombos = dict()

#Separate out fields
def getFields(text):
    #replace punctuation with tilde
    text = re.sub(r"""\ *[,.;/:?!]+\ *""","~",text)
    #fix strange formatting
    text = re.sub(r"""\ *[\r\n]+\ *"""," ",text)
    text = re.sub(r"""[\”\“\'\"]+"""," ",text)
    #lowercase
    text = text.lower()
    #split fields 
    text=text.split(sep="~")

    return text

#create regex
professionsSet = ['acoustics', 'addiction medicine', 'allergist', 'allergy and clinical immunology', 'anesthesia', 'anesthesiologist', 'anesthesiology', 'anesthetist', 'audiology', 'bacteriology', 'biologics', 'biophysics', 'biostatistics', 'cardiac surgeon', 'cardiac surgery', 'cardiologist', 'cardiology', 'chronic pain', 'critical care', 'cytogenetics', 'dermatologist', 'dermatology', 'electroencephalography', 'emergency medicine', 'endocrinologist', 'endocrinology', 'ent', 'epidemiology', 'family medicine', 'family practice', 'gastroenterologist', 'gastroenterology', 'general practice', 'general surgeon', 'general surgery', 'general thoracic surgery', 'geneticist', 'genetics', 'geriatric medicine', 'geriatrician', 'geriatrics', 'gynecologist', 'gynecology', 'haematologist', 'head and neck surgeon', 'head and neck surgery', 'hematologist', 'hematology', 'hospital medicine', 'hospitalist', 'immunologist', 'immunology', 'infectious disease', 'internal medicine', 'internist', 'laboratory medicine', 'long-term care', 'medical biochemistry', 'microbiology', 'neonatology', 'nephrologist', 'nephrology', 'neuro-radiology', 'neurologist', 'neurology', 'neuropathology', 'neuroradiologist', 'neuroradiology', 'neurosurgeon', 'neurosurgery', 'nuclear medicine', 'nuclear medicine radiologist', 'obgyn', 'obstetrician', 'obstetrics', 'occupational and environmental medicine', 'oncologist', 'oncology', 'ophthalmologist', 'ophthalmology', 'opthalmology', 'orthopedic surgeon', 'orthopedic surgery', 'orthopedics', 'oto-rhino-laryngology', 'otolaryngologist', 'otolaryngology', 'otoloryngology', 'otorhinolaryngology', 'palliative medicine', 'pathobiology', 'pathologist', 'pathology', 'pediatric', 'pediatrician', 'pediatrics', 'pharmacology', 'physiatry', 'physical medicine and rehabilitation', 'physiology', 'plastic surgeon', 'plastic surgery', 'pneumology', 'primary care mental health', 'psychiatrist', 'psychiatry', 'psychology', 'public health', 'radiologist', 'radiology', 'respiratory disease', 'respirologist', 'respirology', 'rheumatologist', 'rheumatology', 'rural medicine', 'sport and exercise medicine', 'surgery', 'syphilology', 'thoracic surgeon', 'toxicology', 'urologist', 'urology', 'vascular surgeon', 'vascular surgery', 'virology']
professionsSet = set([a.lower().strip() for a in professionsSet])
searchString = ""
for item in professionsSet:
    if searchString!="":
        searchString+=r"|"
    #\b is used to make sure its not part of another word
    searchString+= r"(\b" + re.escape(item) + r"\b)"
professionsRegex = re.compile(searchString)

class DoctorInfo:
  def __init__(self, text):
        #initialize
        self.age = None 
        self.yearOfDeath = None
        self.isError = False

        #separate out info in array
        self.fields = getFields(text)

        try:
            #populate fields in object
            self.populate()

            #make sure all fields are populated
            assert(self.fullyPopulated())
        except Exception as e: 
            print(traceback.format_exc())
            print(e)
            self.isError = True

  monthDictionary = {
                    'jan': 1,
                    'feb': 2,
                    'mar': 3,
                    'apr':4,
                    'may':5,
                    'jun':6,
                    'jul':7,
                    'aug':8,
                    'sep':9,
                    'sept':9,
                    'oct':10,
                    'nov':11,
                    'dec':12,
                    'january': 1,
                    'february': 2,
                    'march': 3,
                    'april':4,
                    'may':5,
                    'june':6,
                    'july':7,
                    'august':8,
                    'september':9,
                    'october':10,
                    'november':11,
                    'december':12
                    }
  

  def populateAgeAndDate(self,diedText):
        #month (Here to make sure date is valid)
        month = self.monthDictionary[diedText[-5]]
        
        #day (Here to make sure date is valid)
        day = diedText[-4]
        assert(day.isnumeric())
        day = int(day)
        assert(0<day<40)

        #year
        year = diedText[-3]
        assert(year.isnumeric())
        year = int(year)
        assert(2000<=year<=2023)

        #age 
        age = diedText[-1]
        assert(age.isnumeric())
        if(self.age != None): raise Exception("Double populating age")
        self.age = int(age)
        assert(10<self.age<125)
        
        if(self.yearOfDeath != None): raise Exception("Double populating yearOfDeath")
        self.yearOfDeath = year

  def populateProfession(self,field):
      #check if profession word here
      professionsList = professionsRegex.findall(field)
      if(len(professionsList)<1):
          return False
      
      #findall formatting is strange
      if(isinstance(professionsList[0],tuple)):
        professionsList = set(["".join(x) for x in professionsList])
      
      if("" in professionsList):
        professionsList.remove("")

    #   #find common profession name pattern to add to our list
    #   for word in field.split(): 
    #     if (word.endswith(("ology","ologics","ologist","ics","ist","surgery")) and word not in professionsSet):
    #         professionsMissed.append(word)

      #add any previously found jobs
      if(self.profession != None):
        for item in self.profession:
            professionsList.add(item)
      
      #-ologist -ology merge
      toRemove = []
      for item in professionsList:
          if item.endswith("ologist"):
              toRemove.append(item)
      for item in toRemove:
          professionsList.remove(item)
          professionsList.add(item[0:-3]+"y")

      #-surgeon -surgery merge
      toRemove = []
      for item in professionsList:
          if item.endswith("surgeon"):
              toRemove.append(item) 
      for item in toRemove:
          professionsList.remove(item)
          professionsList.add(item[0:-3]+"ery")
      
      #remove common combos
      if('obstetrics' in professionsList and 'gynecology' in professionsList):
          professionsList.remove('obstetrics')
          professionsList.remove('gynecology')
          professionsList.add('obgyn')
      if('obstetrics' in professionsList and 'obgyn' in professionsList):
          professionsList.remove('obstetrics')
      if('gynecology' in professionsList and 'obgyn' in professionsList):
          professionsList.remove('gynecology')
      if('psychiatrist' in professionsList):
          professionsList.remove('psychiatrist')
          professionsList.add("psychiatry")
      if('anesthesiology' in professionsList):
          professionsList.remove('anesthesiology')
          professionsList.add("anesthesia")
      if('anesthetist' in professionsList):
          professionsList.remove('anesthetist')
          professionsList.add("anesthesia")
      if('family practice' in professionsList):
          professionsList.remove('family practice')
          professionsList.add("family medicine")
      if('rural medicine' in professionsList):
          professionsList.remove('rural medicine')
          professionsList.add("family medicine")
      if('general practice' in professionsList):
          professionsList.remove('general practice')
          professionsList.add("family medicine")
      if('orthopedics' in professionsList and 'orthopedic surgery' in professionsList):
          professionsList.remove('orthopedics')
      if("pediatrics" in professionsList):
          professionsList.remove('pediatrics')
          professionsList.add("pediatric")
      if("pediatrician" in professionsList):
          professionsList.remove('pediatrician')
          professionsList.add("pediatric")
      if('laboratory medicine' in professionsList and 'pathology' in professionsList):
          professionsList.remove('laboratory medicine')
      
      #specialties that trumped or are trumped by any others
      if('family medicine' in professionsList and len(professionsList)>1):
          professionsList.remove('family medicine')
      if('pediatric' in professionsList and len(professionsList)>1):
          professionsList.remove('pediatric')
      if('internal medicine' in professionsList and len(professionsList)>1):
          professionsList.remove('internal medicine')
      
      #remove substrings
      toRemove = []
      for item1 in professionsList:
          for item2 in professionsList:
            if item1!=item2 and re.search(r"(\b" + re.escape(item1) + r"\b)", item2):
                toRemove.append(item1)
      for item in toRemove:
          professionsList.remove(item)

      sizeOfProfessionsList = len(professionsList)
      if sizeOfProfessionsList == 1:
        self.profession = professionsList
        return True
      elif(sizeOfProfessionsList == 0):
        return False 
      
      #keep track of common combos
    #   key = str(professionsList)
    #   if key in commonCombos:
    #     commonCombos[key] += 1
    #   else:
    #     commonCombos[key] = 1
      raise Exception("Invalid interestion size"+str(professionsList))
          
      
      

  def populate(self):
      diedText = None
      
      for ind,field in enumerate(self.fields):          
          #date of death spread across fields
          if(diedText is not None):
              #get full died text
              
              diedText+=field.split()
              if(diedText[-2] != "aged"):
                  continue

              self.populateAgeAndDate(diedText)
              
              break #nothing useful after age, and it could cause confusion
              
          
          #get date of death
          if(field.startswith("died")):
              diedText = field.split()
              continue

         
              
  #make sure all fields are populated
  def fullyPopulated(self):
      variables = [getattr(self, a) for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
      return not (None in variables)

def main():
    #change directory to current file path
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    startTime = time.time()
    print("Starting")

    #check for old output and create output folder
    outputDir = os.path.abspath("./Output")
    if(os.path.exists(outputDir)):
        if(len(os.listdir(outputDir))>0): #can delete empty folder
            userInput = input("Are you sure you want to delete old outputs? y/n\n") #ask permission to delete full folder
            if(userInput != "y"):
                print("Operation cancelled, exiting")
                exit()
        os.rmdir(outputDir)
    os.makedirs(outputDir, exist_ok = False)

    #read original csvs
    doctorInfoArray = []
    errorsArray = []
    dataFolder = os.path.abspath("Data")
    for file in os.listdir(dataFolder):
        if file.endswith(".csv"):
            print("Processing " + file)
            file = os.path.join(dataFolder,file)
            inputDF = pd.read_csv(file, engine='python').dropna(how="all")
            for index, row in inputDF.iterrows():
                info = DoctorInfo(row["Obituaries"])
                if(info.isError):
                    errorsArray.append(info)
                else:
                    doctorInfoArray.append(info)

    
    print("Starting Finalization:",time.time()-startTime)
            
    print("Errors", len(errorsArray))
    print("Valid", len(doctorInfoArray))
    # print("Possible professions missed in professionsSet", set(professionsMissed))
    # print("Possible missed combos", json.dumps({k: v for k, v in sorted(commonCombos.items(), key=lambda item: item[1])},indent=4))

    #count statistics
    infoDict = dict()
    allYearsKey="allYears"
    totalDeathKey = "totalDeaths"
    infoDict[allYearsKey] = dict()
    infoDict[allYearsKey][totalDeathKey] = []
    numProfessions = 1
    numYears = 1
    for obituary in doctorInfoArray:
        currYearKey = str(obituary.yearOfDeath)
        if(currYearKey not in infoDict):
            numYears +=1
            infoDict[currYearKey] = dict()
            infoDict[currYearKey][totalDeathKey] = []
            
        infoDict[allYearsKey][totalDeathKey].append(obituary.age)
        infoDict[currYearKey][totalDeathKey].append(obituary.age)
        
    
    #format data
    colTitles = ["deaths","avg age","median death","Q3 death","Q1 death","IQR death",""]
    colsPerProfession = len(colTitles)
    
    shape = (numYears+2,numProfessions*colsPerProfession+1)
    output =np.full(shape, "", dtype="object", order='C')

    #output num errors vs valid
    output[numYears+1,0] = "Included: "+ str(len(doctorInfoArray))
    output[numYears+1,1] = "Ommitted due to error: "+ str(len(errorsArray))

    #get index for each profession and add titles
    #sorted by most deaths
    professionIndices = dict()
    for ind,(key,value) in enumerate(sorted(infoDict[allYearsKey].items(), key=lambda item: len(item[1]), reverse=True)):
        a = 1+ind*colsPerProfession
        b = a+colsPerProfession
        output[0,a:b] = [key+" "+title for title in colTitles]
        professionIndices[key] = ind

    #titles for full array
    output[0,0] = "year"

    #loop through years in order
    sortedYears = sorted(infoDict.items(), key=lambda item: int(item[0]) if item[0].isdecimal() else 99999999)
    for yearInd,(year,yearDict) in enumerate(sortedYears):
        currRow = yearInd+1
        output[currRow,0] = str(year)
        
        for profession,deathsArray in yearDict.items():
            ind = professionIndices[profession]
            deaths = len(deathsArray)
            avg = np.average(deathsArray)
            median = np.median(deathsArray)
            Q3, Q1 = np.percentile(deathsArray, [75 ,25])
            iqr = Q3 - Q1
            a = 1+ind*colsPerProfession
            b = a+colsPerProfession
            output[currRow,a:b] = [
                deaths,avg,median,Q3,Q1,iqr,""
            ]

        
    #save the excel sheet with name of status
    with open(os.path.join(outputDir,'output.csv'), 'w', newline='', encoding="utf-8-sig") as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(output.tolist())
    
    print("Done:",time.time()-startTime)

if __name__ == "__main__":
    main()



