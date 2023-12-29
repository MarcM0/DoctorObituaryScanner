import re
import csv
import os
import pandas as pd
import numpy as np
import json
import time
import shutil
import traceback

# professionsMissed = []
# commonCombos = dict()
checkingProfession = True
checkingYear = False
#valid: checkingProfession and checking year, checking year but not profession, not checking year but checking profession
assert(checkingProfession or checkingYear)

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
professionsSet = ['acoustics', 'acoustics surgery', 'addiction medicine', 'addiction medicine surgery', 'allergist', 'allergist surgery', 'allergy and clinical immunology', 'allergy and clinical immunology surgery', 'anesthesia', 'anesthesia surgery', 'anesthesiology', 'anesthesiology surgery', 'anesthetist', 'anesthetist surgery', 'audiology', 'audiology surgery', 'bacteriology', 'bacteriology surgery', 'cardiac surgery', 'cardiology', 'cardiology surgery', 'chronic pain', 'chronic pain surgery', 'critical care', 'critical care surgery', 'cytogenetics', 'cytogenetics surgery', 'dermatology', 'dermatology surgery', 'electroencephalography', 'electroencephalography surgery', 'emergency', 'emergency surgery', 'endocrinology', 'endocrinology surgery', 'ent', 'ent surgery', 'epidemiology', 'epidemiology surgery', 'family medicine', 'family medicine surgery', 'family practice', 'family practice surgery', 'gastroenterology', 'gastroenterology surgery', 'general practice', 'general practice surgery', 'geneticist', 'geneticist surgery', 'genetics', 'genetics surgery', 'geriatric medicine', 'geriatric medicine surgery', 'geriatrician', 'geriatrician surgery', 'geriatrics', 'geriatrics surgery', 'gynaecology', 'gynaecology surgery', 'gynecology', 'gynecology surgery', 'haematology', 'haematology surgery', 'head and neck surgery', 'hematology', 'hematology surgery', 'hospital medicine', 'hospital medicine surgery', 'hospitalist', 'hospitalist surgery', 'immunology', 'immunology surgery', 'infectious disease', 'infectious disease surgery', 'internal medicine', 'internal medicine surgery', 'internist', 'internist surgery', 'laboratory medicine', 'laboratory medicine surgery', 'long-term care', 'long-term care surgery', 'medical biochemistry', 'medical biochemistry surgery', 'microbiology', 'microbiology surgery', 'neonatology', 'neonatology surgery', 'nephrology', 'nephrology surgery', 'neuro-radiology', 'neuro-radiology surgery', 'neurology', 'neurology surgery', 'neuropathology', 'neuropathology surgery', 'neuroradiology', 'neuroradiology surgery', 'neurosurgery', 'nuclear medicine', 'nuclear medicine radiology', 'nuclear medicine radiology surgery', 'nuclear medicine surgery', 'obgyn', 'obgyn surgery', 'obstetrician', 'obstetrician surgery', 'obstetrics', 'obstetrics surgery', 'occupational and environmental medicine', 'occupational and environmental medicine surgery', 'oncology', 'oncology surgery', 'ophthalmology', 'ophthalmology surgery', 'opthalmology', 'opthalmology surgery', 'orthopedic', 'orthopedic surgery', 'orthopedics', 'orthopedics surgery', 'oto-rhino-laryngology', 'oto-rhino-laryngology surgery', 'otolaryngology', 'otolaryngology surgery', 'otoloryngology', 'otoloryngology surgery', 'otorhinolaryngology', 'otorhinolaryngology surgery', 'palliative medicine', 'palliative medicine surgery', 'pathobiology', 'pathobiology surgery', 'pathology', 'pathology surgery', 'pediatric', 'pediatric surgery', 'pediatrician', 'pediatrician surgery', 'pediatrics', 'pediatrics surgery', 'pharmacology', 'pharmacology surgery', 'physiatry', 'physiatry surgery', 'physical medicine and rehabilitation', 'physical medicine and rehabilitation surgery', 'physiology', 'physiology surgery', 'plastic surgery', 'pneumology', 'pneumology surgery', 'primary care mental health', 'primary care mental health surgery', 'psychiatrist', 'psychiatrist surgery', 'psychiatry', 'psychiatry surgery', 'psychology', 'psychology surgery', 'public health', 'public health surgery', 'radiology', 'radiology surgery', 'respiratory disease', 'respiratory disease surgery', 'respirology', 'respirology surgery', 'rheumatology', 'rheumatology surgery', 'rural medicine', 'rural medicine surgery', 'sport and exercise medicine', 'sport and exercise medicine surgery', 'surgery', 'syphilology', 'syphilology surgery', 'thoracic surgery', 'toxicology', 'toxicology surgery', 'urology', 'urology surgery', 'vascular surgery', 'virology', 'virology surgery']
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
        if(checkingProfession):
            self.profession = None
        if(checkingYear):
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
  
  professionReplaceDict = {
        'epidemiology': 'public health',
        'obstetrics': 'obgyn',
        'obstetrician': 'obgyn',
        'gynecology': 'obgyn',
        'gynaecology': 'obgyn',
        'psychiatrist': 'psychiatry',
        'anesthesiology': 'anesthesia',
        'anesthetist': 'anesthesia',
        'family practice': 'family medicine',
        'rural practice': 'family medicine',
        'rural medicine': 'family medicine',
        'general practice': 'family medicine',
        'orthopedic': 'orthopedics',
        'orthopedic surgery': 'orthopedics',
        'orthopedics surgery': 'orthopedics',
        'laboratory medicine': 'pathology',
        'microbiology': 'pathology',  
        'virology': 'pathology', 
        'bacteriology': 'pathology', 
        'pediatrics': 'pediatric',
        'pediatrician': 'pediatric',
        'otorhinolaryngology': 'otolaryngology',
        'otoloryngology': 'otolaryngology',
        'oto-rhino-laryngology': 'otolaryngology',
        'ent': 'otolaryngology',
        'audiologist': 'otolaryngology', 
        'internist': 'internal medicine',  
        'pneumology': 'respirology',
        'physiatry': 'physical medicine and rehabilitation',
        'geriatrics': 'geriatric',
        'geriatrics medicine': 'geriatric',
        'geriatric medicine': 'geriatric'
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
        assert(1999<=year<=2023)

        #age 
        age = diedText[-1]
        assert(age.isnumeric())
        if(self.age != None): raise Exception("Double populating age")
        self.age = int(age)
        assert(10<self.age<125)
        
        if(self.yearOfDeath != None): raise Exception("Double populating yearOfDeath")
        self.yearOfDeath = year

  def populateProfession(self,field):
      field = field.split()
      #-ologist -ology merge
      for i,item in enumerate(field):
          if item.endswith("ologist"):
              field[i] = item[0:-3]+"y"

      #-surgeon -surgery merge
      for i,item in enumerate(field):
          if item.endswith("surgeon"):
              field[i] = item[0:-3]+"ery"
      
      field = " ".join(field)

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
      
      #substitutions
      toAdd = []
      toRemove = []
      for item in professionsList:
        if item in self.professionReplaceDict:
            toRemove.append(item)
            toAdd.append(self.professionReplaceDict[item])
      for item in toAdd:
          professionsList.add(item)
      for item in toRemove:
          professionsList.remove(item)
      
      #remove substrings
      toRemove = []
      for item1 in professionsList:
          for item2 in professionsList:
            if item1!=item2 and re.search(r"(\b" + re.escape(item1) + r"\b)", item2):
                toRemove.append(item1)
      for item in toRemove:
          professionsList.remove(item)

      #specialties that are trumped by others
      trumped = ['family medicine','pediatric','emergency','surgery','internal medicine'] #in order of reverse priority (last is highest)
      for item in trumped:
        if(item in professionsList and len(professionsList)>1):
            professionsList.remove(item)
      

      #only accept 1 profession
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
          #age only
          if(not checkingYear and "aged" in field.split()):
              field = field.split()
              #age 
              age = field[field.index("aged")+1]
              assert(age.isnumeric())
              if(self.age != None): raise Exception("Double populating age")
              self.age = int(age)
              assert(10<self.age<125)

              break
              
          #date of death spread across fields
          if(checkingYear and diedText is not None):
              #get full died text
              
              diedText+=field.split()
              if(diedText[-2] != "aged"):
                  continue

              self.populateAgeAndDate(diedText)
              
              break #nothing useful after age, and it could cause confusion
              
          
          #get date of death
          if(checkingYear and field.startswith("died")):
              diedText = field.split()
              continue
          
          #get profession
          if(checkingProfession and self.populateProfession(field)):
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
        shutil.rmtree(outputDir)
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
    totalDeathKey = "allProfessions"
    infoDict[allYearsKey] = dict()
    infoDict[allYearsKey][totalDeathKey] = []
    numProfessions = 1
    numYears = 1
    for obituary in doctorInfoArray:
        if(checkingYear):
            currYearKey = str(obituary.yearOfDeath)

        if(checkingProfession):
            [currProfessionKey] = obituary.profession
        if(checkingYear and currYearKey not in infoDict):
            numYears +=1
            infoDict[currYearKey] = dict()
            infoDict[currYearKey][totalDeathKey] = []

        if(checkingYear and checkingProfession and currProfessionKey not in infoDict[currYearKey]):
            infoDict[currYearKey][currProfessionKey] = []
            
        if(checkingProfession and currProfessionKey not in infoDict[allYearsKey]):
            infoDict[allYearsKey][currProfessionKey] = []
            numProfessions+=1
        
        if(checkingProfession):
            infoDict[allYearsKey][currProfessionKey].append(obituary.age)
            if(checkingYear):
                infoDict[currYearKey][currProfessionKey].append(obituary.age)
        infoDict[allYearsKey][totalDeathKey].append(obituary.age)
        if(checkingYear):
            infoDict[currYearKey][totalDeathKey].append(obituary.age)
        
    if(checkingYear):
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
    else: #not checking year
        allDeathAges = infoDict[allYearsKey][totalDeathKey]
        colTitles = infoDict[allYearsKey].keys()
        rowNum = len(allDeathAges)+2
        colNum = len(colTitles)
        shape = (rowNum,colNum)
        output =np.full(shape, "", dtype="object", order='C')

        #output num errors vs valid
        output[0,0] = "Included: "+ str(len(doctorInfoArray))
        output[1,0] = "Ommitted due to error: "+ str(len(errorsArray))

        #get index for each profession and add titles
        #sorted by most deaths
        professionIndices = dict()
        for ind,(key,value) in enumerate(sorted(infoDict[allYearsKey].items(), key=lambda item: len(item[1]), reverse=True)):
            a = ind+1
            b = a+1
            output[0,a:b] = key
            professionIndices[key] = ind

        #populate array            
        for profession,deathsArray in infoDict[allYearsKey].items():
            ind = professionIndices[profession]
            a = ind+1
            b = a+1
            deathsArray.sort()
            output[1:len(deathsArray)+1,a:b] = np.transpose([deathsArray])

    if(checkingProfession and checkingYear):
        filename = "perProfessionPerYear.csv"
    elif(checkingProfession):
        filename = "noYear.csv"
    elif(checkingYear):
        filename = "noProfession.csv"
    else: 
        raise Exception("Invalid mode")
    
    #save the excel sheet with name of status
    with open(os.path.join(outputDir,filename), 'w', newline='', encoding="utf-8-sig") as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(output.tolist())
    
    print("Done:",time.time()-startTime)

if __name__ == "__main__":
    main()



