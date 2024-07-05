import streamlit as st
import os
import threading
from openai import AzureOpenAI
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse
import tldextract
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

            if url in visited_urls:
                continue
        
            visited_urls.add(url)

            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                    
                title = soup.find('title').text if soup.find('title') else 'No title'
                content = soup.get_text()
                data_collected.append({"url": url, "title": title, "content": content.replace(" ", "")[:2000]})
                    
                base_domain = tldextract.extract(url).registered_domain
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(url, link['href'])
                    extracted_domain = tldextract.extract(full_url).registered_domain
                    if extracted_domain == base_domain and full_url not in visited_urls:
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
st.set_page_config(page_title="WebSage 🧙‍♂️", page_icon="🔮", layout="centered", initial_sidebar_state="auto", menu_items=None)

st.title("WebSage 🧙‍♂️")

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
if "scraped_data" not in st.session_state:
    st.session_state["scraped_data"] = None

if "success" not in st.session_state:
    st.session_state["success"] = None
    
with st.form("link_form"):
    link = st.text_input("Digite o link de um site 🔮")
    submitted = st.form_submit_button("Enviar")
    if submitted and is_valid_url(link):
        st.session_state["scraped_data"], st.session_state["success"] = limited_time_scraping(link, 3)

        if st.session_state["success"]:
            st.info(f"Agora que eu já sei TUDO sobre o site {link}, faça me uma pergunta")
        else:
            st.info(f"Agora que eu já sei sobre o site {link}, faça me uma pergunta")
    elif submitted and not is_valid_url(link):
        st.info("Por favor, me de um link válido para que possamos conversar", icon="🧙‍♂️")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Como eu posso te ajudar?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"], avatar="🔮" ).write(msg["content"])

if prompt := st.chat_input("Faça uma pergunta"):
    if is_valid_url(link):
        load_dotenv()

        client = AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = os.getenv("AZURE_API_VERSION") ,
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user", avatar="🤯").write(prompt)

        messages = [{"role": "assistant", "content": f"Você é um GRANDE compreensor (como um sábio) sobre o site {link} que seu contéudo esta fornecido abaixo: {st.session_state.scraped_data[0:7]} \n\nSabendo disso responda as perguntas a seguir (que serão em grande maioria voltadas ao conteudo fornecido), em um tom autêncico e filosofo engajando o usuário a fazer mais perguntas e se o conteúdo nao foi o suficiente para responder a pergunte, forneça um caminho provável para pesquisa para encontrar a resposta"}] + st.session_state.messages

        response = client.chat.completions.create(
            model=os.getenv("AZURE_DEPLOYMENT_NAME"), 
            messages=messages, 
            n=1,
            temperature=0.7,
            max_tokens=250
        )

        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant", avatar="🧙‍♂️").write(msg)
    elif not is_valid_url(link):
        st.toast("Por favor, antes de conversarmos me de um link para que seja o tópico da nossa conversa", icon="🧙‍♂️")
        st.stop()