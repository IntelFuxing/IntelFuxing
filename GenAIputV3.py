import time
import os
import pandas as pd
import re
import json
import pyperclip
import html
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#pip install --upgrade -r requirements.txt to install all librairies

global prompt

def jsonfinder():
    file_pathJSON = f'bettersteve.json'
    fileJSON = open(file_pathJSON, 'r') 
    resultJSON = fileJSON.read()
    return(resultJSON)
def txtfinder():
    filepathtxt = f'PromptV2.txt'
    fileTXT = open(filepathtxt, 'r')
    # Read the entire content of the file
    resulttxt = fileTXT.read()
    return(resulttxt)

def outlookread():
    titles=[]
    sources=[]
    posted_ats=[]
    summaries=[]
    # Load the CSV file
    data = pd.read_csv(f'outlook.csv')
    array_data = data.values.tolist()
    body = [row[1] for row in array_data]

    for item in body :
        title_matches = re.findall(r'TITLE\[\|(.+?)\|\]', item,re.DOTALL)
        titles.extend(title_matches)
    
        sources_matches = re.findall(r'SOURCE\[\|(.+?)\|\]', item,re.DOTALL)
        sources.extend(sources_matches)

        posted_at_matches = re.findall(r'POSTED AT\[\|(.+?)\|\]', item,re.DOTALL)
        posted_ats.extend(posted_at_matches)
    
        summary_matches = re.findall(r'SUMMARY\[\|(.+?)\|\]', item,re.DOTALL)
        summaries.extend(summary_matches)
    return(titles,sources,posted_ats,summaries)

    

#opening personal chrome profile to allow SSO login 
def driver_setup():
    options = webdriver.ChromeOptions()
    options.add_argument(r'--profile-directory=Default')
    options.add_argument('ignore-certificate-errors')
    options.add_argument(f"--user-data-dir=C:\\Users\\{os.getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data")  
    driver = webdriver.Chrome(executable_path=f"{os.getcwd()}\\ressources\\chromedriver.exe",chrome_options=options)
    return driver

def action(driver,xpath,detect,action_type=None, value=None, timeout=10) :
    expected_conditions_dict = {
        1: EC.element_to_be_clickable,
        2: EC.presence_of_element_located
    } 
    try:
        element = WebDriverWait(driver, timeout).until(
            expected_conditions_dict[detect]((By.XPATH, xpath))
        )
        if action_type == 'click':
            element.click()    
        elif action_type == 'sk':
            element.send_keys(value)
    finally:
        return(time.sleep(1),print(f"action: {action_type}"))

def loading(driver):
    time.sleep(5)
    try:
        WebDriverWait(driver, 120).until_not(
            EC.presence_of_element_located((By.ID, 'stop-button'))
        )
    except Exception as e :
        print(f'not loadingd{e}')

def Typetext(driver,Input):
    action(driver,'//*[@id="chat-input"]',1)
    element = driver.find_element(By.XPATH, '//*[@id="chat-input"]')
    pyperclip.copy(Input)
    element.send_keys(Keys.CONTROL, 'v')
    action(driver,'//*[@id="root"]/div/div/div/div[2]/div[2]/div/div/div[2]/div[1]/div/div/div/div[2]/button',1,'click')
    loading(driver)

def driver_parse(driver):
    html_content = driver.page_source
    responsedivs = driver.find_elements(By.XPATH, '//div[@class="markdown-body"]')
    conversations = []
    for responsediv in responsedivs:
        raw_html = responsediv.get_attribute('innerHTML')
        conversations.append(raw_html)
    conversations.pop(0)    
    return conversations

def driver_path(prompt):
    driver = driver_setup()
    driver.get('https://val-chatbot.cartier.cn.rccad.net/')
    Typetext(driver,prompt)
    response = (driver_parse(driver))
    ('Prompt: ',response[0])
    ("Response: ",response[1])
    driver.close()
    return response

def IndexCat():
    titles, sources, posted_ats, summaries = outlookread()
    indices_dict = {}
    for index, value in enumerate(sources):
        if value not in indices_dict:
            indices_dict[value] = []
        indices_dict[value].append(index)
    return(indices_dict)

def getitems():
    final_output = []
    listetest = IndexCat()
    titles, sources, posted_ats, summaries = outlookread()
    
    # Process each key independently
    for key, value in listetest.items():
        current_block = f"Source: {key}\n"
        item_count = 0
        
        for i in value:
            if item_count >= 6:  # Break after 6 items for this key
                break
            
            # Add the details to current_block as a formatted string
            current_block += (
                f"Title: {titles[i]}\n"
                f"Posted At: {posted_ats[i]}\n"
                f"Summary: {summaries[i]}\n"
                f"One line Summary: \n"
                f"Relevance: \n\n"
            )
            
            item_count += 1
        
        # Append the block to final_output
        final_output.append(current_block)
    
    return final_output
# Modified prompt constructionz
titles, sources, posted_ats, summaries = outlookread()
items_data = getitems()

def execute():
    output = []
    items_data = getitems()  # Get the items once
    i=0
    for item in items_data:  # Iterate over the items
        analysis = driver_path(txtfinder()+item)[1]  # Pass the entire item string to driver_path
        output.append(analysis)
    result = '\n'.join(output)
    return output

def responseFormat(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = soup.find_all('p')

    # Extract the source from the first paragraph
    source_start = paragraphs[0].text.find("Source: ")
    if source_start != -1:
        source_end = min(paragraphs[0].text.find('\n'), paragraphs[0].text.find("Title: "))
        source = paragraphs[0].text[source_start + len("Source: "):source_end].strip()
    else:
        source = None

    articles = []
    for p in paragraphs:
        # Skip the first paragraph since we've already extracted the source from it
        if p == paragraphs[0]:
            continue

        # Extract the title
        title_start = p.text.find("Title: ")
        if title_start != -1:
            title_end = min(p.text.find('\n', title_start), p.text.find("Posted At: "))
            title = p.text[title_start + len("Title: "):title_end].strip()
            title = re.sub(r'https?://\S+', '', title)
        else:
            title = None

        # Extract the posted time
        posted_time_start = p.text.find("Posted at: ")
        if posted_time_start != -1:
            summary_phrases = ["One-line Summary:",'One line Summary:',"Summary:"]
            posted_time_end = min([p.text.find(phrase, posted_time_start) for phrase in summary_phrases if p.text.find(phrase, posted_time_start) != -1], default=None)
            if posted_time_end is not None:
                posted_time = p.text[posted_time_start + len("Posted at: "):posted_time_end].strip()
            else:
                posted_time = None
        else:
            posted_time = None

        # Extract the URL
        url = p.find('a')
        if url:
            url = url['href']
        else:
            url = None

        # Extract the summary
        summary_phrases = ["One-line Summary:",'One line Summary:',"Summary:"]
        summary_starts = [p.text.find(phrase) for phrase in summary_phrases]
        valid_summary_starts = [start for start in summary_starts if start != -1]

        # Determine the earliest valid start index
        if valid_summary_starts:
            summary_start = min(valid_summary_starts)
            # Find the end of the summary based on the next occurrence of '\n' or "Relevance Scores:"
            summary_end = min(p.text.find('\n', summary_start), p.text.find("Relevance Scores: "))
            summary = p.text[summary_start + len(summary_phrases[summary_starts.index(summary_start)]):summary_end].strip()
        else:
            summary = None

        ratings_match = re.search(r'Relevance Scores: (\d+) Market Research &amp; Technology Innovation, (\d+) General Interest', p.text)
        if ratings_match:
            market_research_rating = int(ratings_match.group(1))
            general_interest_rating = int(ratings_match.group(2))
        else:
            market_research_rating = None
            general_interest_rating = None

        # Add the extracted information to the articles list, including the source
        articles.append({
            "source": source,
            "title": title,
            "url": url,
            "summary": summary,
            "posted_time": posted_time,
            "market_research_rating": market_research_rating,
            "general_interest_rating": general_interest_rating
        })

    return articles

def create_styled_html_file_with_filter(filename, articles):
    # Generate the HTML content
    html_content = "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
    html_content += "    <meta charset='UTF-8'>\n"
    html_content += "    <style>\n"
    html_content += "        body {\n"
    html_content += "            font-family: Arial, sans-serif;\n"
    html_content += "            background-color: rgba(255, 255, 255, 0.5);\n"
    html_content += "            backdrop-filter: blur(10px);\n"
    html_content += "            -webkit-backdrop-filter: blur(10px);\n"
    html_content += "            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);\n"
    html_content += "        }\n"
    html_content += "        .container {\n"
    html_content += "            max-width: 800px;\n"
    html_content += "            margin: 0 auto;\n"
    html_content += "            padding: 20px;\n"
    html_content += "        }\n"
    html_content += "        .article {\n"
    html_content += "            background-color: rgba(255, 255, 255, 0.5);\n"
    html_content += "            backdrop-filter: blur(10px);\n"
    html_content += "            -webkit-backdrop-filter: blur(10px);\n"
    html_content += "            border-radius: 10px;\n"
    html_content += "            padding: 20px;\n"
    html_content += "            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);\n"
    html_content += "            margin-bottom: 20px;\n"
    html_content += "            transition: box-shadow 0.3s ease, background-color 0.3s ease;\n"
    html_content += "        }\n"
    html_content += "        .article:hover {\n"
    html_content += "            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);\n"
    html_content += "            background-color: rgba(255, 255, 255, 0.7);\n"
    html_content += "        }\n"
    html_content += "        h2 {\n"
    html_content += "            color: #004165;\n"
    html_content += "        }\n"
    html_content += "        .source {\n"
    html_content += "            color: #777;\n"
    html_content += "        }\n"
    html_content += "        .summary {\n"
    html_content += "            color: #555;\n"
    html_content += "        }\n"
    html_content += "        a {\n"
    html_content += "            color: #004165;\n"
    html_content += "            text-decoration: none;\n"
    html_content += "        }\n"
    html_content += "        a:hover {\n"
    html_content += "            text-decoration: underline;\n"
    html_content += "        }\n"
    html_content += "        select {\n"
    html_content += "            background-color: rgba(255, 255, 255, 0.5);\n"
    html_content += "            backdrop-filter: blur(10px);\n"
    html_content += "            -webkit-backdrop-filter: blur(10px);\n"
    html_content += "            border-radius: 10px;\n"
    html_content += "            padding: 10px;\n"
    html_content += "            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);\n"
    html_content += "        }\n"
    html_content += "    </style>\n"
    html_content += "    <script>\n"
    html_content += "        function filterBySource() {\n"
    html_content += "            var sourceFilter = document.getElementById('sourceFilter').value;\n"
    html_content += "            var articles = document.getElementsByClassName('article');\n"
    html_content += "            for (var i = 0; i < articles.length; i++) {\n"
    html_content += "                if (sourceFilter === '' || articles[i].querySelector('.source').innerText.includes(sourceFilter)) {\n"
    html_content += "                    articles[i].style.display = '';\n"
    html_content += "                } else {\n"
    html_content += "                    articles[i].style.display = 'none';\n"
    html_content += "                }\n"
    html_content += "            }\n"
    html_content += "        }\n"
    html_content += "        window.onload = function() {\n"
    html_content += "            filterBySource();\n"
    html_content += "        }\n"
    html_content += "    </script>\n"
    html_content += "</head>\n<body>\n"
    html_content += "<div class='container'>\n"
    # Add the source filter dropdown
    html_content += "<select id='sourceFilter' onchange='filterBySource()'>\n"
    html_content += "    <option value=''>Show All</option>\n"
    # Get unique sources
    sources = set([article['source'] for article in articles])
    for source in sources:
        html_content += f"    <option value='{source}'>{source}</option>\n"
    html_content += "</select>\n\n"

    # Add the articles to the HTML content
    for article in articles:
        html_content += f"<div class='article'>\n"
        html_content += f"    <h2><a href='{article['url']}' target='_blank'>{article['title']}</a></h2>\n"
        html_content += f"    <p class='source'>Source: {article['source']}</p>\n"
        html_content += f"    <p class='summary'>{article['summary']}</p>\n"
        html_content += "</div>\n"

    # Close the HTML tags
    html_content += "</div>\n"  # Close the .container div
    html_content += "</body>\n</html>\n"

    # Write the HTML to a file
    with open(filename, 'w') as f:
        f.write(html_content)

html_contents = execute()

all_articles = []
for html_content in html_contents:
    articles = responseFormat(html_content)
    all_articles.extend(articles)
print(all_articles)

create_styled_html_file_with_filter('index.html', all_articles)

#ajouter de la scoring justification 
#faire une proposition pour le style 
#fine-tune le prompt et les output fais par le BOT  

#titles, sources, posted_ats, summaries = outlookread()
#prompt = (jsonfinder() +'\n'+'here is the data :'+'\n'+ 'TITLE : '+titles[1] +'\n'+'SOURCE : '+sources[1] +'\n'+'POSTED AT : '+posted_ats[1] +'\n'+'SUMMARY : '+summaries[1])

#store string par categories et submit dans driver path a partir de get items 
# creer le preprompt avec les indicatifs donnes et dire d ignorer les liens et seulement compléter les empty case 
    # constuire plusieurs preprompt et faire des test pour mesurer l efficacité
    # peut sortir 8 reponses 
#recuperer le preprompt et reformer un mail ou trouver un moyen d'afficher les résultats correctement (faire un report dans une page HTML ou faire un report en plus du outlook ?)

#print(IndexCat())
#driver_path()
#automatic report 

#raw_html = responsediv.get_attribute('innerHTML')
#soup = BeautifulSoup(raw_html, 'html.parser')
#markdown_content = soup.get_text()
#conversations.append(markdown_content)

#for responsediv in responsedivs:
#        markdown_text = responsediv.text
#        conversations.append(markdown_text)
#    return conversations
##soup = BeautifulSoup(page_content, 'html.parser')

##//*[@id="step-106643d8-4754-407e-a29c-e4b92201a7c3"]/div/div
