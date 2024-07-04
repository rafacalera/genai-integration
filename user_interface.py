import streamlit as st
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import time

# def get_all_links(base_url, timeout=1):
#     start_time = time.time()
#     visited_urls = set()
#     urls_to_visit = [base_url]

#     try: 
#         while urls_to_visit:
#             if time.time() - start_time > timeout:
#                 return list(visited_urls.union(urls_to_visit))
        
#             url = urls_to_visit.pop(0)
        
#             if url in visited_urls:
#                 continue
        
#             visited_urls.add(url)

#             response = requests.get(url)
            
#             if response.status_code == 200:
#                 soup = BeautifulSoup(response.text, 'html.parser')
                
#                 for link in soup.find_all('a', href=True):
#                     full_url = urljoin(base_url, link['href'])
                    
#                     if urlparse(full_url).netloc == urlparse(base_url).netloc and full_url not in visited_urls:
#                         print(full_url)
#                         urls_to_visit.append(full_url)
#     except Exception:
#         return list(visited_urls.union(urls_to_visit))
    
#     return visited_urls

# def scrape_site(base_url):
#     all_links = get_all_links(base_url)
#     content_of_links = ''
    
#     for link in all_links:
#         try:
#             response = requests.get(link)
#             if response.status_code == 200:
#                 soup = BeautifulSoup(response.text, 'html.parser')
            
#                 title = soup.find('title').text if soup.find('title') else 'No title'
#                 content = soup.get_text()
                
#                 content_of_links += f"Title: {title}\nContent: {content}\n\n"
#                 print(content_of_links)
#         except Exception as e:
#             print(f"Error scraping {link}: {e}")

#     return content_of_links


# Interface
st.title("Website Sage 🧙‍♂️")

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
with st.sidebar:
    link = st.text_input("Website que eu serei sábio 🧙‍♂️🔮")

if is_valid_url(link):
    response = requests.get(link)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
            
        title = soup.find('title').text if soup.find('title') else 'Sem tiltulo'
        content = soup.get_text()
                
        content_of_links = f"Titulo: {title}\nConteúdo: {content}\n\n"

        st.info(f"Agora que eu já sei sobre o site {link}, faça me uma pergunta")


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Como eu posso te ajudar?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if is_valid_url(link):
        load_dotenv()

        client = AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = os.getenv("AZURE_API_VERSION") ,
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        messages = [{"role": "assistant", "content": f"Você é um Sábio (como um mago mesmo) sobre o conteúdo do site {link} que seu contéudo esta abaixo: {content_of_links} \n\nSabendo disso responda as perguntas a seguir, em um tom sábio e autêntico"}] + st.session_state.messages

        response = client.chat.completions.create(model=os.getenv("AZURE_DEPLOYMENT_NAME"), messages=messages)

        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
    elif not is_valid_url(link):
        st.toast("Por favor, antes de conversarmos me de um link para que seja o tópico da nossa conversa", icon="🧙‍♂️")
        st.stop()