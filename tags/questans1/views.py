from logging import exception
import logging
import bs4
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
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response 
from rest_framework import status 
from  .database import questions_collection
logger = logging.getLogger(__name__)
import requests_html
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time




# Create your views here.
from .scrappers import  cookSoup1, getImageUrl1, convertToJson1,  getOptions1, \
getCorrectAnswer, getQuestion1, convertToJson1, cookSoup, downloadImage1

def get_param(request):
    data = request.data
    logger.info(f"Inside get_param: {data}")  # Logging the data received in get_param

    topic = data.get('topic', '')
    quiz = data.get('quiz', '')
    house = data.get('house', [])

        # Log the raw values of topic and quiz
    logger.info(f"Raw values - Topic: {topic}, Quiz: {quiz}")
    if not isinstance(house, list):
        house = []
    
    if not isinstance(topic, str):
        topic = str(topic)
    
    if not isinstance(quiz, str):
        quiz = str(quiz)
        
    return topic, quiz, house

@csrf_exempt
@api_view(['GET','POST'])
def extract1_data_api(request):
    session = HTMLSession()
    logger.info(f"Request content type: {request.content_type}")

    if request.content_type != 'application/json':
        return Response({'error': 'Invalid content type. Expected application/json.'}, status=400)

    try:
        logger.info(f"Request data: {request.data}")
        
        topic, quiz, house = get_param(request)
        
        logger.info(f"Extracted parameters - Topic: {topic}, Quiz: {quiz}, House: {house}")

        if not topic or not quiz:
            return Response({'error': 'Topic and quiz parameters are required and must be non-empty strings.'}, status=400)
        
        additional_url = f"{topic}/{quiz}.html"
        url = f"https://www.shmoop.com/study-guides/{additional_url}"
        
        soup,newsession = cookSoup(url,session)
        
        if soup is not None and session is not None:            
            results = soup.find("div", class_="biology-content")
            
            if not results:
                return Response({'error': 'No content found on the page.'}, status=404)
            
            texts = []
            images_url = []
            question_details = {}
            question_Text = results.text.replace('"',"").strip() 
            q_head = results.find_all("h3")
            for val in q_head:
                text = val.text.strip()  
                texts.append(text)
            question_details["question_head"] = texts
            question_details["questions_&_answers"] = question_Text
            q_image = results.find_all("img")
            for image in q_image:
                if not image == None :
                   urli =image["src"]
                   downloadImage1(urli,topic)
                   images_url.append(urli)
            question_details["imageUrl"] = images_url
            question_details["topic"] = topic
            house.append(question_details)
            print(house)
            logger.info(f"Extracted question: {question_details}")
            convertToJson1(house, topic)
            logger.info("End of site reached, thank you for tiffing questions")

        return Response({'message': 'Results extracted successfully', 'results': house}, status=200)
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return Response({'error': str(e)}, status=500)
    
    
    