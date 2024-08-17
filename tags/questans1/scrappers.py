from logging import exception
from requests.exceptions import RequestException, InvalidSchema
import bs4
import logging
from requests_html import HTMLSession
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
import csv
from reportlab.pdfgen import canvas
import json
import requests
from os.path  import basename
import os
from django.shortcuts import render, redirect
import argparse
from django.contrib import messages
from django.db import connection
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper
import mimetypes
from django.http import HttpResponse, JsonResponse, HttpRequest
from rest_framework.decorators import api_view
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time



logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

house = []
house1 = []


def downloadImage(imgUrl,structure,num, exam_type,subject,exam_year):
    try:
        path = createNewDir(exam_type, structure,num,subject,exam_year)
        
        with open(os.path.join(path,basename(imgUrl)), "wb") as f:
            
            f.write(requests.get(imgUrl).content)
    except (OSError, RequestException, InvalidSchema) as e:
        print(f"Error downloading image: {str(e)}")  # Use str(e) to print the exception message

def downloadImage1(imgUrl,topic):
    try:
        path = createNewDir1(topic)
        
        with open(os.path.join(path,basename(imgUrl)), "wb") as f:
            
            f.write(requests.get(imgUrl).content)
    except OSError as e:
        print(e.message,e.args)
        
        
def createNewDir(exam_type, structure,num,subject,exam_year):
    try:
        path = os.path.join(exam_type,subject,structure,str(exam_year),str(num))
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    except (OSError, RequestException, InvalidSchema) as e:
        print(f"Error Creating directory: {str(e)}")  # Use str(e) to print the exception message



def createNewDir1(topic):
    path = os.path.join(topic)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def extract(soup,session,house,structure,exam_type,subject,exam_year,subtype):
    try:    
        if(soup != None and session != None):
            results = soup.find_all("div",class_="media question-item mb-4")
            questext = []
            correctAns = []
            quesopt = []
            form = []
            subt = []
            for item in results:
                question_details = {}
                correctAnswer,explanation = getCorrectAnswerExplanation(item)
                question_details["correctOption"] = correctAnswer
                question_details["explanation"] = {"text":explanation}
                question_Text = getQuestion(item)
                question_details["text"] = question_Text
                question_details["structure"] = structure
                number = getNumber(item)
                question_details["number"] = int(number)
                imageUrl = getImageUrl(item,number,structure,exam_type,subject,exam_year)
                question_details["imageUrl"] = imageUrl
                options = getOptions(item,structure,number,exam_type,subject,exam_year)
                question_details["options"] = options
                if exam_type == "WAEC":
                    question_details["subType"] = subtype
                else:
                     question_details["subType"] = subtype
                question_details["subject"] = subject
                question_details["type"] = exam_type
                question_details["year"] = exam_year
                print(question_details)
                house.append(question_details)
                print("\n\n")
                print(house)
                #return house
            if(soup != None and session != None):   
               results2 = soup.find("ul",class_= "pagination flex-wrap")
               links = results2.find_all("a")
               nextPage = None
               #for x in range(1,7):
               if links[-1].text.lower().strip() == "»":
                 for x in range(1,len(links)):
                  nextPage = links[x]["href"]
                  next,newSession1 = cookSoup(nextPage,session)
                  if(next != None and session != None):
                    results1 = next.find_all("div",class_="media question-item mb-4")
                    for item in results1:
                       question_details = {}
                       correctAnswer,explanation = getCorrectAnswerExplanation(item)
                       question_details["correctOption"] = correctAnswer
                       correctAns.append(question_details["correctOption"])
                       question_details["explanation"] = {"text":explanation}
                       question_Text = getQuestion(item)
                       question_details["text"] = question_Text
                       questext.append(question_details["text"])
                       question_details["structure"] = structure
                       form.append(question_details["structure"])
                       number = getNumber(item)
                       question_details["number"] = int(number) 
                       figures = int(number)
                       imageUrl = getImageUrl(item,structure,number,exam_type,subject,exam_year)
                       question_details["imageUrl"] = imageUrl
                       options = getOptions(item,structure,number,exam_type,subject,exam_year)
                       question_details["options"] = options
                       for item in question_details["options"]:
                           quesopt.append(item["text"][1:200])                       
                       if exam_type == "WAEC":
                           question_details["subType"] = subtype
                           subt.append(question_details["subType"])
                       else:
                            question_details["subType"] = subtype
                            subt.append(question_details["subType"])
                       question_details["subject"] = subject
                       question_details["type"] = exam_type
                       question_details["year"] = exam_year
                       print(question_details)
                       house.append(question_details)
                       #num = len(house)
                       print("\n\n")
                       print(house)
                       #return house                     
               else:
                 convertToJson(house,exam_type,subject,exam_year,structure)
                 print("End of site reached,thank you for tiffing questions")
           
                
    except exception as e:
        print(e.message,e.args)

def nextPage(soup,session,house,structure,exam_type,subject,exam_year,subtype):
    if(soup != "" and session != ""):
        results = soup.find("ul",class_= "pagination flex-wrap")
        
        links = results.find_all("a")
        nextPage = None
        if links[-1].text.lower().strip() == "»":
            nextPage = links[-1]["href"]
            next,newSession = cookSoup(nextPage,session)
            extract(next,session,house,structure,exam_type,subject,exam_year,subtype)
        else:
             convertToJson(house)
             print("End of site reached,thank you for tiffing questions")
    else:
       
        print("Soup burnt or session expired")
    

def convertToJson(data,exam_type,subject,exam_year,structure):
    filename = f"output_{exam_type}_{exam_year}_{subject}_{structure}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"JSON file created: {filename}")
    house.clear()
    return os.path.abspath(filename)

def convertToJsonT(data, exam_type, subject, exam_year, structure):
    try:
        filename = f"output_{exam_type}_{exam_year}_{subject}_{structure}.json"
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f"JSON file saved successfully at {filename}")
        return filename
    except Exception as e:
        print(f"Error converting to JSON: {e}")
        return None


def upload_json_to_api(file_path, api_url):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return
    with open(file_path, 'rb') as file:
        try:
            response = requests.post(api_url, files={'inputFile': (os.path.basename(file_path), file, 'application/json')}, data={'index': '0'})
            print(f"Response status code: {response.status_code}")
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            print("File uploaded successfully")
            print(f"Response JSON: {response.json()}")
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response content: {response.content.decode()}")
        except Exception as err:
            print(f"Other error occurred: {err}")
            
def convertToPdf(data):
    filename = "output_" + exam_type + "_" + str(exam_year) + "_"  + subject + ".pdf"
    buffer = BytesIO()
    with open(filename, 'a') as f:
           pisa.CreatePDF(data, dest=f, encoding='utf-8')
    house.clear()
             
def getOptions(item,structure,num,exam_type,subject,exam_year):
    try:
        options = []
        result = item.find("ul",class_="list-unstyled")
        optionsResult = result.find_all("li")
        for val in optionsResult:
            option = {}
            option["option"] = val.find("strong").text.replace(".","").strip()
            option["text"] = val.text.strip()[2:]
            #option_image = val.find("img")
            image_url = getImageUrl(item,structure,num,exam_type,subject,exam_year)
            if image_url != None:
                option["imageUrl"] = image_url
                #downloadImage(image_url,question_details["structure"],question_details["number"])
            else:
                option["imageUrl"] = None
            options.append(option)
        return options
    except exception as e:
        print(e.message,e.args)

def getOptions1(item,subject):
    try:
        options = []
        result = item.find("ul",class_="selected")
        optionsResult = result.find_all("li")
        for val in optionsResult:
            option = {}
            option["option"] = val.find("input",type_="radio",class_="semi-bold")
            option["text"] = val.find("label").text.strip()[2:]
            #option_image = val.find("img")
            image_url = getImageUrl1(item,subject)
            if image_url != None:
                option["imageUrl"] = image_url
                #downloadImage(image_url,question_details["structure"],question_details["number"])
            else:
                option["imageUrl"] = None
            options.append(option)
        return options
    except exception as e:
        print(e.message,e.args)


def getNumber(item):
    try:
        result = item.find("div",class_="question_sn bg-danger mr-3")
        number = result.text.strip()
        return number
    except exception as e:
        print(e.message,e.args)
        
def getImageUrl(item,structure,num,exam_type,subject,exam_year):
    image = item.find("img")
    if not image == None :
        url =image["src"]
        downloadImage(url,structure,num,exam_type,subject,exam_year)
        return url
    else:
        return None

def getQuestion(item):
    try:
        result = item.find("div",class_="question-desc mt-0 mb-3")
        question = result.find("p")
        if(question):
            text = question.text.replace('"',"").strip() 
        else:
            text = result.text.replace('"',"").strip() 
        return text
    except exception as e:
        print(e.message,e.args)
        
def getQuestion1(item):
    try:
        result = item.find("h3",class_="semi-bold")
        text = result.text.replace('"',"").strip()  
        return text
    except exception as e:
        print(e.message,e.args)

def getTheoryQuestion(item):
    try:
        texts = []
        result = item.find("div",class_="question-desc mt-0 mb-3")
        question = result.find_all("p")
        for val in question:
            text = val.text.strip()  
            texts.append(text)
        return texts
    except exception as e:
        print(e.message,e.args)
        
def getCorrectAnswerExplanation(item):
    try:
        if(item != None):
            answerLink = item.find("a")
            session = HTMLSession()
            base_url = answerLink['href']
            soup,newSession = cookSoup(base_url,session)
            if(soup != None and session != None):
                result =soup.select("div[class='mb-4']")
                answerResult = result[1].find("h5",class_="text-success mb-3")
                explationResult = result[1].text
                if not answerResult:
                    answerResult = result[0].find("h5",class_="text-success mb-3")
                    explationResult = result[0].text
                answer = answerResult.text.replace("Correct Answer: Option ","").strip()
                explanation = explationResult[explationResult.index("Explanation"):].strip()
                if explanation != None:
                    return answer,explanation
                else:
                    return answer,None
    except exception as e:
        print(e.message,e.args)

def getCorrectAnswer(item):
    try:
        result = item.find("li",class_="border-blue semi-bold true-answer")
        answer = result.find("label")
        if(answer):
            text = answer.text.replace('"',"").strip() 
        else:
            text = result.text.replace('"',"").strip() 
        return text
    except exception as e:
        print(e.message,e.args)
        

    
def cookSoup(url,session):
    try:
        resp = session.get(url)
        resp.raise_for_status()
        if(url != "" and session != ""):
            html = resp.html.html
            soup = bs4.BeautifulSoup(html, "html.parser")
            return soup,session
        else:
            print("Soup burnt or session expired")
    except Exception as e:
           logger.error(f"Error fetching the URL: {url} - {e}")
           return None

def cookSoup1(url,session):
    try:
        os.environ['WDM_LOCAL'] = '1'
        os.environ['WDM_CACHE_DIR'] = r'C:/Users/chint/web-tags'

        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.183 Safari/537.36")

        # Automatically download and use the correct version of ChromeDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        logger.debug("Opening the URL in the browser...")
        driver.get(url)

        # Wait until a specific element is loaded (example: 'quick-quiz-question')
        #WebDriverWait(driver, 20).until(
            #EC.presence_of_element_located((By.CLASS_NAME, "quick-quiz-question"))
        #)

        # Keep the browser open to manually inspect
        input("Press Enter to close the browser...")  # Keeps the browser open until you press Enter
        logger.debug("Fetching page source...")
        # Retrieve the page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = bs4.BeautifulSoup(page_source, 'html.parser')
        logger.debug("Closing the browser...")
        driver.quit()  # Close the browser after pressing Enter
        return soup, session
    
    except Exception as e:
        logger.error(f"Error fetching the URL: {url} - {e}")
        return None, None

  
def getImageUrl1(item,topic):
    image = item.find("img")
    if not image == None :
        url =image["src"]
        downloadImage1(url,topic)
        return url
    else:
        return None

#save objects as json        
def convertToJson1(data, topic):
    with open(f'{topic}_questions.json', 'w') as f:
        json.dump(data, f)
        
def convertToPdf1(data):
    filename = "output_" + et + "_" + str(ey) + "_"  + su + ".pdf"
    buffer = BytesIO()
    with open(filename, 'a') as f:
           pisa.CreatePDF(data, dest=f, encoding='utf-8')
    house.clear()
            
#get the html of the page

def writeToFile(text):
    with open("/Neco/Questions.txt",'a') as f:
        f.write(text+ "\n")
  
def result(request):
    """""global subject, exam_type, structure, exam_year, subtype
    print()
    subject = "BIOLOGY"
    exam_type = "JAMB"
    structure = "OBJECTIVE"
    if structure == "OBJECTIVE":
        url_Struc = "obj"
    subtype = None
    exam_year = 2020
    additional_url = subject.lower().replace(" ","-") + "?exam_type=" + exam_type.lower() + "&" + "exam_year=" + str(exam_year) + "&" + "type=" + url_Struc
    session = HTMLSession()
    base_url = "https://myschool.ng/classroom/" + additional_url
    soup,newSession = cookSoup(base_url,session)
    tran = extract(soup,newSession)"""""
    return render(request, 'questans/home.html')

#def share_questions(subject, exam_type, structure, exam_year, subtype):
    
def show_filters(request):
    return render(request, 'questans/filters.html')

def show_filters1(request):
    return render(request, 'questans/filters1.html')

def fetch_questions(request):
    global subject, exam_type, structure, exam_year, subtype
    print()
    if request.method == 'POST':
        we = request.POST['we']
        et = request.POST['et']
        su = request.POST['su']
        ey = request.POST['ey']
        st = request.POST['st']
        qt = request.POST['qt'] 
        house = [] 
        
        if we == 'ms':
           subject = su
           exam_type = et
           structure = qt
           subtype = st

           if subtype == "MAY/JUNE" or subtype == "MAR":
              subtype = st
           if exam_type == "ALL":
               messages.error(request, 'Error ---> please select appropriate exam type')
               return render(request, 'questans/filters.html') 
           if structure == "OBJECTIVE":
               url_Struc = "obj"
           elif structure == "THEORY":
               url_Struc = "theory"
           else:
               messages.error(request, 'Error ---> please select appropriate exam structure')
               return render(request, 'questans/filters.html') 
           subtype = None
           exam_year = int(ey)
           title = subject +  "_" + exam_type +  "_" + str(exam_year)
           additional_url = subject.lower().replace(" ","-") + "?exam_type=" + exam_type.lower() + "&" + "exam_year=" + str(exam_year) + "&" + "type=" + url_Struc
           session = HTMLSession()
           base_url = "https://myschool.ng/classroom/" + additional_url
           soup,newSession = cookSoup(base_url,session)    
           if(soup != None and newSession != None):
              results = soup.find_all("div",class_="media question-item mb-4")
              questext = []
              correctAns = []
              quesopt = []
              form = []
              subt = []
              for item in results:
                question_details = {}
                correctAnswer,explanation = getCorrectAnswerExplanation(item)
                question_details["correctOption"] = correctAnswer
                correctAns.append(question_details["correctOption"])
                question_details["explanation"] = {"text":explanation}
                question_Text = getQuestion(item)
                question_details["text"] = question_Text
                questext.append(question_details["text"])
                question_details["structure"] = structure
                form.append(question_details["structure"])
                number = getNumber(item)
                question_details["number"] = int(number)
                imageUrl = getImageUrl(item,number)
                question_details["imageUrl"] = imageUrl
                options = getOptions(item,number)
                question_details["options"] = options
                for item in question_details["options"]:
                    quesopt.append(item["text"][1:200])
                if exam_type == "WAEC":
                    question_details["subType"] = subtype
                    subt.append(question_details["subType"])
                else:
                     question_details["subType"] = subtype
                     subt.append(question_details["subType"])
                question_details["subject"] = subject
                question_details["type"] = exam_type
                question_details["year"] = exam_year
                print(question_details)
                house.append(question_details)
                print("\n\n")
                print(house)
                #return house
              if(soup != None and newSession != None):   
               results2 = soup.find("ul",class_= "pagination flex-wrap")
               links = results2.find_all("a")
               nextPage = None
               #for x in range(1,7):
               if links[-1].text.lower().strip() == "»":
                 for x in range(1,len(links)):
                  nextPage = links[x]["href"]
                  next,newSession1 = cookSoup(nextPage,newSession)
                  if(next != None and newSession != None):
                    results1 = next.find_all("div",class_="media question-item mb-4")
                    for item in results1:
                       question_details = {}
                       correctAnswer,explanation = getCorrectAnswerExplanation(item)
                       question_details["correctOption"] = correctAnswer
                       correctAns.append(question_details["correctOption"])
                       question_details["explanation"] = {"text":explanation}
                       question_Text = getQuestion(item)
                       question_details["text"] = question_Text
                       questext.append(question_details["text"])
                       question_details["structure"] = structure
                       form.append(question_details["structure"])
                       number = getNumber(item)
                       question_details["number"] = int(number) 
                       figures = int(number)
                       imageUrl = getImageUrl(item,number)
                       question_details["imageUrl"] = imageUrl
                       options = getOptions(item,number)
                       question_details["options"] = options
                       for item in question_details["options"]:
                           quesopt.append(item["text"][1:200])                       
                       if exam_type == "WAEC":
                           question_details["subType"] = subtype
                           subt.append(question_details["subType"])
                       else:
                            question_details["subType"] = subtype
                            subt.append(question_details["subType"])
                       question_details["subject"] = subject
                       question_details["type"] = exam_type
                       question_details["year"] = exam_year
                       print(question_details)
                       house.append(question_details)
                       num = len(house)
                       print("\n\n")
                       print(house)
                    

                        
               else:
                 convertToJson(house)
                 print("End of site reached,thank you for tiffing questions")
              
          
        context = {
            'house':house,
            'title':title,
            'num':num,
            'options':options,
            'text':questext,
            'ans':correctAns,
            'opt':quesopt,
            'form':form,
            'subt':subt,
        }
        
        request.session['scraped_data'] = context
        return render(request, 'questans/result.html', context)
    return render(request, 'questans/filters.html')

def fetch_questions1(request):
    global su, et, qt, ey, st, question_details 
    print()
    if request.method == 'POST':
        we = request.POST['we']
        et = request.POST['et']
        su = request.POST['su']
        ey = request.POST['ey']
        st = request.POST['st']
        qt = request.POST['qt'] 
        
        if we == 'ns':
           title = su + "_" + et + "_" + str(ey)
           additional_url = su.lower().replace(" ","-") + "/" + et.lower() + "/" + "year" + "/" + ey
           session = HTMLSession()
           house1.clear()
           base_url = "https://nigerianscholars.com/past-questions/" + additional_url
           resp = session.get(base_url)
           if(base_url != "" and session != ""):
               html = resp.html.html
               soup = bs4.BeautifulSoup(html, "html.parser")
               if(soup != "" and session != ""):
                 results = soup.find_all("div", class_="question_block")
                 for question in results:
                     question_details = {}
                     question_details["subType"] = None
                     question_details["structure"] = "OBJECTIVE"
                     number =  question.find("h3")
            
                     question_details["number"] = int(number.text.strip().split(" ")[1])
                     correct_option  = question.find(id="ans-label")
                     question_details["correctOption"] = correct_option.text[0:1]
                     question_text = question.find("div",class_="question_text")
                     #get image url
                     image_url = getImageUrl1(question_text)
                     if image_url != None:
                         question_details["imageUrl"] = image_url
                         downloadImage1(image_url,question_details["structure"],question_details["number"])
                     else:
                         question_details["imageUrl"] = None

            

                     question_details["text"] = question_text.get_text("\n")
            
                     explanation_div = question.find("div",class_="q_explanation")
                     explanation = explanation_div.find("div",class_="q_explanation_text table-responsive")
                     if(explanation != None):
                         question_details["explanation"] = explanation.text
                     else:
                         question_details["explanation"] = None

            
                     #find all  options
                     soup_options_parent = question.find(class_="question_content table-responsive")
                     #soup_options = soup_options_parent.find_all("p")
            
                     options = []
                     #special format
                     soup_options = soup_options_parent.find_all("div",class_="q_option")
                     for paragraph in soup_options:
                          opt, txt = paragraph.find("span").text[0:1], paragraph.find("div").text
                          option = {}
                          option["option"] = opt
                          option["text"] = txt
                          option_image = paragraph.find("img")
                          option["imageUrl"] = None
                          image_url = getImageUrl1(paragraph)
                          if image_url != None:
                              option["imageUrl"] = image_url
                              downloadImage1(image_url,question_details["structure"],question_details["number"])
                          else:
                              option["imageUrl"] = None

                          if(option_image != None ):
                              if (str(option_image).find("class=") == -1):
                                  #option["imageUrl"] = option_image["src"] to e worked upon
                                  option["imageUrl"] = None
                          else:
                              option["imageUrl"] = None

                    
                          options.append(option)
            
                     question_details["options"] = options
            
                     question_details["subject"] = su
                     question_details["type"] = et
                     question_details["year"] = ey 
                     print(question_details)
                     house1.append(question_details)
                     #writeToFile(question_details)
                     print("\n\n")
                     print(house1)
                 if(soup != "" and session != ""):
                   results = soup.find("ul",class_= "mg-0 pl-0")
        
                   links = results.find_all("a")
                   nextPage = None
                   if links[-1].text.lower().strip() == "Next »":
                     for x in range(1,len(links)):
                       nextPage = links[x]["href"]
                       resp = session.get(nextPage)
                       if(nextPage != "" and session != ""):
                         html = resp.html.html
                         soup = bs4.BeautifulSoup(html, "html.parser")
                         if(soup != "" and session != ""):
                           results = soup.find_all("div", class_="question_block")
                           for question in results:
                               question_details = {}
                               question_details["subType"] = None
                               question_details["structure"] = "OBJECTIVE"
                               number =  question.find("h3")
            
                               question_details["number"] = int(number.text.strip().split(" ")[1])
                               correct_option  = question.find(id="ans-label")
                               question_details["correctOption"] = correct_option.text[0:1]
                               question_text = question.find("div",class_="question_text")
                               #get image url
                               image_url = getImageUrl1(question_text)
                               if image_url != None:
                                   question_details["imageUrl"] = image_url
                                   downloadImage1(image_url,question_details["structure"],question_details["number"])
                               else:
                                   question_details["imageUrl"] = None

            

                               question_details["text"] = question_text.get_text("\n")
            
                               explanation_div = question.find("div",class_="q_explanation")
                               explanation = explanation_div.find("div",class_="q_explanation_text table-responsive")
                               if(explanation != None):
                                   question_details["explanation"] = explanation.text
                               else:
                                   question_details["explanation"] = None

            
                               #find all  options
                               soup_options_parent = question.find(class_="question_content table-responsive")
                               #soup_options = soup_options_parent.find_all("p")
            
                               options = []
                               #special format
                               soup_options = soup_options_parent.find_all("div",class_="q_option")
                               for paragraph in soup_options:
                                    opt, txt = paragraph.find("span").text[0:1], paragraph.find("div").text
                                    option = {}
                                    option["option"] = opt
                                    option["text"] = txt
                                    option_image = paragraph.find("img")
                                    option["imageUrl"] = None
                                    image_url = getImageUrl1(paragraph)
                                    if image_url != None:
                                        option["imageUrl"] = image_url
                                        downloadImage1(image_url,question_details["structure"],question_details["number"])
                                    else:
                                        option["imageUrl"] = None

                                    if(option_image != None ):
                                        if (str(option_image).find("class=") == -1):
                                            #option["imageUrl"] = option_image["src"] to e worked upon
                                            option["imageUrl"] = None
                                    else:
                                        option["imageUrl"] = None

                    
                                    options.append(option)
            
                               question_details["options"] = options
            
                               question_details["subject"] = su
                               question_details["type"] = et
                               question_details["year"] = ey 
                               print(question_details)
                               house1.append(question_details)
                               num = len(house1)
                               #writeToFile(question_details)
                               print("\n\n")
                               print(house1)
                   else:
                        convertToJson(house)
                        print("End of site reached,thank you for doing the lords work")
                 else:
                    print("Soup burnt or session expired")
       
                     #convertToJson(house)
    
           else:
               print("Soup burnt or session expired")

        
        elif et == 'ALL':
               messages.error(request, 'Error ---> please select appropriate exam type')
               return render(request, 'questans/filters1.html') 
        else:
               messages.error(request, 'Error ---> please select all appropriate options to get your PQ')
               return render(request, 'questans/filters1.html') 
           
        context = {
                'house':house,
                'title':title,
                'num':num,
                'options':options,
        }
        request.session['scraped_data'] = context
        return render(request, 'questans/result.html', context)    
    
    return render(request, 'questans/filters1.html')

def downloadpq(request):
    global subject, exam_type, structure, exam_year, subtype
    if 'scraped_data' in request.session:
        context = request.session['scraped_data']
        response = HttpResponse(content_type='')
    
        if request.POST['download_type'] == 'pdf':
            template_path = 'questans/result.html'
            template = get_template(template_path)
            html = template.render(context)
            response = HttpResponse(content_type='application/pdf')
            filename = f"{context['title']}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html, dest=response, encoding='utf-8')
            if pisa_status.err:
                return HttpResponse('PDF generation failed')
        elif request.POST['download_type'] == 'csv':
            response = HttpResponse(content_type='text/csv')
            filename = f"{context['title']}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            writer = csv.writer(response)
            writer.writerow(['Title','Questions','CorrectOption',
                             ['Option A','Option B','Option C','Option D','Option E'], 'Structure', 'Subtype'])
            rows = zip([context['title']],context['text'],context['ans'],
                context['opt'],context['form'],context['subt'])
            for row in rows:
                writer.writerow(row)
        elif request.POST['download_type'] == 'json':
            response = HttpResponse(content_type='application/json')
            filename = f"{context['title']}.json"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            json.dump(context, response, indent=4)
        return response
    else:
        return render(request, 'questans/filters.html')
    
def fetch_me_soup(request):
    global subject, exam_type, structure, exam_year, subtype
    print()
    if request.method == 'POST':
        we = request.POST['we']
        et = request.POST['et']
        su = request.POST['su']
        ey = request.POST['ey']
        st = request.POST['st']
        qt = request.POST['qt'] 
        house = [] 
        
        if we == 'ms':
           subject = su
           exam_type = et
           structure = qt
           subtype = st

           if subtype == "MAY/JUNE" or subtype == "MAR":
              subtype = st
           if exam_type == "ALL":
               messages.error(request, 'Error ---> please select appropriate exam type')
           if structure == "OBJECTIVE":
               url_Struc = "obj"
           elif structure == "THEORY":
               url_Struc = "theory"
           else:
               messages.error(request, 'Error ---> please select appropriate exam structure')
           subtype = None
           exam_year = int(ey)
           title = subject +  "_" + exam_type +  "_" + str(exam_year)
           additional_url = subject.lower().replace(" ","-") + "?exam_type=" + exam_type.lower() + "&" + "exam_year=" + str(exam_year) + "&" + "type=" + url_Struc
           session = HTMLSession()
           base_url = "https://myschool.ng/classroom/" + additional_url
           soup,newSession = cookSoup(base_url,session)    
           if(soup != None and newSession != None):
              results = soup.find_all("div",class_="media question-item mb-4")
              questext = []
              correctAns = []
              quesopt = []
              form = []
              subt = []
              for item in results:
                question_details = {}
                correctAnswer,explanation = getCorrectAnswerExplanation(item)
                question_details["correctOption"] = correctAnswer
                correctAns.append(question_details["correctOption"])
                question_details["explanation"] = {"text":explanation}
                question_Text = getQuestion(item)
                question_details["text"] = question_Text
                questext.append(question_details["text"])
                question_details["structure"] = structure
                form.append(question_details["structure"])
                number = getNumber(item)
                question_details["number"] = int(number)
                imageUrl = getImageUrl(item,number)
                question_details["imageUrl"] = imageUrl
                options = getOptions(item,number)
                question_details["options"] = options
                for item in question_details["options"]:
                    quesopt.append(item["text"][1:200])
                if exam_type == "WAEC":
                    question_details["subType"] = subtype
                    subt.append(question_details["subType"])
                else:
                     question_details["subType"] = subtype
                     subt.append(question_details["subType"])
                question_details["subject"] = subject
                question_details["type"] = exam_type
                question_details["year"] = exam_year
                print(question_details)
                house.append(question_details)
                print("\n\n")
                print(house)
                #return house
              if(soup != None and newSession != None):   
               results2 = soup.find("ul",class_= "pagination flex-wrap")
               links = results2.find_all("a")
               nextPage = None
               #for x in range(1,7):
               if links[-1].text.lower().strip() == "»":
                 for x in range(1,len(links)):
                  nextPage = links[x]["href"]
                  next,newSession1 = cookSoup(nextPage,newSession)
                  if(next != None and newSession != None):
                    results1 = next.find_all("div",class_="media question-item mb-4")
                    for item in results1:
                       question_details = {}
                       correctAnswer,explanation = getCorrectAnswerExplanation(item)
                       question_details["correctOption"] = correctAnswer
                       correctAns.append(question_details["correctOption"])
                       question_details["explanation"] = {"text":explanation}
                       question_Text = getQuestion(item)
                       question_details["text"] = question_Text
                       questext.append(question_details["text"])
                       question_details["structure"] = structure
                       form.append(question_details["structure"])
                       number = getNumber(item)
                       question_details["number"] = int(number) 
                       figures = int(number)
                       imageUrl = getImageUrl(item,number)
                       question_details["imageUrl"] = imageUrl
                       options = getOptions(item,number)
                       question_details["options"] = options
                       for item in question_details["options"]:
                           quesopt.append(item["text"][1:200])                       
                       if exam_type == "WAEC":
                           question_details["subType"] = subtype
                           subt.append(question_details["subType"])
                       else:
                            question_details["subType"] = subtype
                            subt.append(question_details["subType"])
                       question_details["subject"] = subject
                       question_details["type"] = exam_type
                       question_details["year"] = exam_year
                       print(question_details)
                       house.append(question_details)
                       num = len(house)
                       print("\n\n")
                       print(house)
                    

                        
               else:
                 convertToJson(house)
                 print("End of site reached,thank you for tiffing questions")
              
          
        context = {
            'house':house,
            'title':title,
            'num':num,
            'options':options,
            'text':questext,
            'ans':correctAns,
            'opt':quesopt,
            'form':form,
            'subt':subt,
        }
        
        request.session['scraped_data'] = context
        return context

def fetch_me_stew(request):
    global su, et, qt, ey, st, question_details 
    print()
    if request.method == 'POST':
        we = request.POST['we']
        et = request.POST['et']
        su = request.POST['su']
        ey = request.POST['ey']
        st = request.POST['st']
        qt = request.POST['qt'] 
        
        if we == 'ns':
           title = su + "_" + et + "_" + str(ey)
           additional_url = su.lower().replace(" ","-") + "/" + et.lower() + "/" + "year" + "/" + ey
           session = HTMLSession()
           house1.clear()
           base_url = "https://nigerianscholars.com/past-questions/" + additional_url
           resp = session.get(base_url)
           if(base_url != "" and session != ""):
               html = resp.html.html
               soup = bs4.BeautifulSoup(html, "html.parser")
               if(soup != "" and session != ""):
                 results = soup.find_all("div", class_="question_block")
                 for question in results:
                     question_details = {}
                     question_details["subType"] = None
                     question_details["structure"] = "OBJECTIVE"
                     number =  question.find("h3")
            
                     question_details["number"] = int(number.text.strip().split(" ")[1])
                     correct_option  = question.find(id="ans-label")
                     question_details["correctOption"] = correct_option.text[0:1]
                     question_text = question.find("div",class_="question_text")
                     #get image url
                     image_url = getImageUrl1(question_text)
                     if image_url != None:
                         question_details["imageUrl"] = image_url
                         downloadImage1(image_url,question_details["structure"],question_details["number"])
                     else:
                         question_details["imageUrl"] = None

            

                     question_details["text"] = question_text.get_text("\n")
            
                     explanation_div = question.find("div",class_="q_explanation")
                     explanation = explanation_div.find("div",class_="q_explanation_text table-responsive")
                     if(explanation != None):
                         question_details["explanation"] = explanation.text
                     else:
                         question_details["explanation"] = None

            
                     #find all  options
                     soup_options_parent = question.find(class_="question_content table-responsive")
                     #soup_options = soup_options_parent.find_all("p")
            
                     options = []
                     #special format
                     soup_options = soup_options_parent.find_all("div",class_="q_option")
                     for paragraph in soup_options:
                          opt, txt = paragraph.find("span").text[0:1], paragraph.find("div").text
                          option = {}
                          option["option"] = opt
                          option["text"] = txt
                          option_image = paragraph.find("img")
                          option["imageUrl"] = None
                          image_url = getImageUrl1(paragraph)
                          if image_url != None:
                              option["imageUrl"] = image_url
                              downloadImage1(image_url,question_details["structure"],question_details["number"])
                          else:
                              option["imageUrl"] = None

                          if(option_image != None ):
                              if (str(option_image).find("class=") == -1):
                                  #option["imageUrl"] = option_image["src"] to e worked upon
                                  option["imageUrl"] = None
                          else:
                              option["imageUrl"] = None

                    
                          options.append(option)
            
                     question_details["options"] = options
            
                     question_details["subject"] = su
                     question_details["type"] = et
                     question_details["year"] = ey 
                     print(question_details)
                     house1.append(question_details)
                     #writeToFile(question_details)
                     print("\n\n")
                     print(house1)
                 if(soup != "" and session != ""):
                   results = soup.find("ul",class_= "mg-0 pl-0")
        
                   links = results.find_all("a")
                   nextPage = None
                   if links[-1].text.lower().strip() == "Next »":
                     for x in range(1,len(links)):
                       nextPage = links[x]["href"]
                       resp = session.get(nextPage)
                       if(nextPage != "" and session != ""):
                         html = resp.html.html
                         soup = bs4.BeautifulSoup(html, "html.parser")
                         if(soup != "" and session != ""):
                           results = soup.find_all("div", class_="question_block")
                           for question in results:
                               question_details = {}
                               question_details["subType"] = None
                               question_details["structure"] = "OBJECTIVE"
                               number =  question.find("h3")
            
                               question_details["number"] = int(number.text.strip().split(" ")[1])
                               correct_option  = question.find(id="ans-label")
                               question_details["correctOption"] = correct_option.text[0:1]
                               question_text = question.find("div",class_="question_text")
                               #get image url
                               image_url = getImageUrl1(question_text)
                               if image_url != None:
                                   question_details["imageUrl"] = image_url
                                   downloadImage1(image_url,question_details["structure"],question_details["number"])
                               else:
                                   question_details["imageUrl"] = None

            

                               question_details["text"] = question_text.get_text("\n")
            
                               explanation_div = question.find("div",class_="q_explanation")
                               explanation = explanation_div.find("div",class_="q_explanation_text table-responsive")
                               if(explanation != None):
                                   question_details["explanation"] = explanation.text
                               else:
                                   question_details["explanation"] = None

            
                               #find all  options
                               soup_options_parent = question.find(class_="question_content table-responsive")
                               #soup_options = soup_options_parent.find_all("p")
            
                               options = []
                               #special format
                               soup_options = soup_options_parent.find_all("div",class_="q_option")
                               for paragraph in soup_options:
                                    opt, txt = paragraph.find("span").text[0:1], paragraph.find("div").text
                                    option = {}
                                    option["option"] = opt
                                    option["text"] = txt
                                    option_image = paragraph.find("img")
                                    option["imageUrl"] = None
                                    image_url = getImageUrl1(paragraph)
                                    if image_url != None:
                                        option["imageUrl"] = image_url
                                        downloadImage1(image_url,question_details["structure"],question_details["number"])
                                    else:
                                        option["imageUrl"] = None

                                    if(option_image != None ):
                                        if (str(option_image).find("class=") == -1):
                                            #option["imageUrl"] = option_image["src"] to e worked upon
                                            option["imageUrl"] = None
                                    else:
                                        option["imageUrl"] = None

                    
                                    options.append(option)
            
                               question_details["options"] = options
            
                               question_details["subject"] = su
                               question_details["type"] = et
                               question_details["year"] = ey 
                               print(question_details)
                               house1.append(question_details)
                               num = len(house1)
                               #writeToFile(question_details)
                               print("\n\n")
                               print(house1)
                   else:
                        convertToJson(house)
                        print("End of site reached,thank you for doing the lords work")
                 else:
                    print("Soup burnt or session expired")
       
                     #convertToJson(house)
    
           else:
               print("Soup burnt or session expired")

        
        elif et == 'ALL':
               messages.error(request, 'Error ---> please select appropriate exam type')
        else:
               messages.error(request, 'Error ---> please select all appropriate options to get your PQ')
           
        context = {
                'house':house,
                'title':title,
                'num':num,
                'options':options,
        }
        request.session['scraped_data'] = context
        return context

def eat_sweet_soup(request):
    global subject, exam_type, structure, exam_year, subtype
    if 'scraped_data' in request.session:
        context = request.session['scraped_data']
        response = HttpResponse(content_type='')
    
        if request.POST['download_type'] == 'pdf':
            template_path = 'questans/result.html'
            template = get_template(template_path)
            html = template.render(context)
            response = HttpResponse(content_type='application/pdf')
            filename = f"{context['title']}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html, dest=response, encoding='utf-8')
            if pisa_status.err:
                return HttpResponse('PDF generation failed')
        elif request.POST['download_type'] == 'csv':
            response = HttpResponse(content_type='text/csv')
            filename = f"{context['title']}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            writer = csv.writer(response)
            writer.writerow(['Title','Questions','CorrectOption',
                             ['Option A','Option B','Option C','Option D','Option E'], 'Structure', 'Subtype'])
            rows = zip([context['title']],context['text'],context['ans'],
                context['opt'],context['form'],context['subt'])
            for row in rows:
                writer.writerow(row)
        elif request.POST['download_type'] == 'json':
            response = HttpResponse(content_type='application/json')
            filename = f"{context['title']}.json"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            json.dump(context, response, indent=4)
        return response