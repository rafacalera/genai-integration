import streamlit as st
import os
import threading
from openai import AzureOpenAI
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

def scrape_site(url, data_collected, stop_event):
    visited_urls = set()
    urls_to_visit = [url]

    try:
        while urls_to_visit:
            if stop_event.is_set():
                return
    
            url = urls_to_visit.pop(0)
            print(url)
        
            if url in visited_urls:
                continue
        
            visited_urls.add(url)

            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                    
                title = soup.find('title').text if soup.find('title') else 'No title'
                content = soup.get_text()
                data_collected.append({"url": url, "title": title, "content": content})
                    
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(url, link['href'])
                    if urlparse(full_url).netloc == urlparse(url).netloc and full_url not in visited_urls:
                        urls_to_visit.append(full_url)

    except Exception as e:
        print(f"Error processing the site {url}: {e}")
    
            
def limited_time_scraping(url, timeout):
    data_collected = []
    stop_event = threading.Event()
    scraping_thread = threading.Thread(target=scrape_site, args=(url, data_collected, stop_event))
    scraping_thread.start()
    scraping_thread.join(timeout=timeout)

    if scraping_thread.is_alive():
        stop_event.set()
        scraping_thread.join()
        return data_collected, False
    else:
        return data_collected, True


# Interface
st.title("Website Sage 🧙‍♂️")

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
with st.sidebar:
    link = st.text_input("Digite o link de um site 🧙‍♂️🔮")

if is_valid_url(link):
    data, success = limited_time_scraping(link, 1)

    if success:
        st.info(f"Agora que eu já sei TUDO sobre o site {link}, faça me uma pergunta")
    else:
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

        messages = [{"role": "assistant", "content": f"Você é um Sábio (como um mago mesmo) sobre o conteúdo do site {link} que seu contéudo esta abaixo: {data[0:2]} \n\nSabendo disso responda as perguntas a seguir, em um tom sábio e autêntico"}] + st.session_state.messages

        response = client.chat.completions.create(model=os.getenv("AZURE_DEPLOYMENT_NAME"), messages=messages)

        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
    elif not is_valid_url(link):
        st.toast("Por favor, antes de conversarmos me de um link para que seja o tópico da nossa conversa", icon="🧙‍♂️")
        st.stop()