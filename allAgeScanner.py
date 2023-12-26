import re
import csv
import os
import pandas as pd
import numpy as np
import time
import shutil
import traceback

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
  
    #count statistics
    infoDict = dict()
    allYearsKey="allYears"
    totalDeathKey = "allProfessions"
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
    with open(os.path.join(outputDir,'noProfession.csv'), 'w', newline='', encoding="utf-8-sig") as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(output.tolist())
    
    print("Done:",time.time()-startTime)

if __name__ == "__main__":
    main()



