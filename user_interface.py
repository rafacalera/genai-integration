import streamlit as st
import os
from dotenv import load_dotenv
import threading
import numpy as np
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import tldextract
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_KEY"))

model_config = genai.GenerationConfig(
    temperature=0.7,
    top_k=1000,
    max_output_tokens=1000,
    top_p=1
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=model_config
)
 
def create_embeddings(content):
    vectorizer = TfidfVectorizer()
    embeddings = vectorizer.fit_transform(content)
    return vectorizer, embeddings
 
def search_with_embeddings(prompt, vectorizer, embeddings, content):
    query_vec = vectorizer.transform([prompt])
    similarities = cosine_similarity(query_vec, embeddings).flatten()
    best_match_index = np.argmax(similarities)
    best_match_segment = content[best_match_index]
    return best_match_index, best_match_segment

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
                data_collected.append({"url": url, "title": title, "content": content})
                    
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

# Initialize proprerties that will be stored
if "scraped_data" not in st.session_state:
    st.session_state["scraped_data"] = None

if "vectorizer" not in st.session_state:
    st.session_state["vectorizer"] = None
    
if "embeddings" not in st.session_state:
    st.session_state["embeddings"] = None

if "success" not in st.session_state:
    st.session_state["success"] = None


with st.form("link_form"):
    link = st.text_input("Digite o link de um site 🔮")
    submitted = st.form_submit_button("Enviar")
    if submitted and is_valid_url(link):
        scraped_data , st.session_state["success"] = limited_time_scraping(link, 5)

        if len(scraped_data) != 0: 
            st.session_state["scraped_data"] = scraped_data

            content = [item["url"] + " - " + item["title"] + ": "  + item["content"] for item in st.session_state.scraped_data]
            st.session_state["vectorizer"], st.session_state["embeddings"] = create_embeddings(content)

            if st.session_state["success"]:
                st.info(f"Agora que eu já sei TUDO sobre o site {link}, faça me uma pergunta")
            else:
                st.info(f"Agora que eu já sei sobre o site {link}, faça me uma pergunta")
        else:
            st.toast("Não foi possivel ler o conteúdo do site 😥, Tente novamente ou forneça-me outro link 😁", icon="🧙‍♂️")

    elif submitted and not is_valid_url(link):
        st.info("Por favor, me de um link válido para que possamos conversar", icon="🧙‍♂️")


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Como eu posso te ajudar?"}]

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message(msg["role"], avatar="😎").write(msg["content"])
    elif st.session_state.messages[0] == msg:
        st.chat_message(msg["role"], avatar="🔮").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message(msg["role"], avatar="🧙‍♂️").write(msg["content"])


if prompt := st.chat_input("Faça uma pergunta"):
    if not prompt.strip() or len(prompt) == 0:
        st.toast("Faça uma pergunta válida para que possamos conversar!", icon="🧙‍♂️")

    elif st.session_state.scraped_data == None:
        st.toast("Não consigo te responder pois não foi possivel ler o conteúdo do site, Tente outro link 😁", icon="🧙‍♂️")
        st.stop()

    elif is_valid_url(link):
        history = []
        for msg in st.session_state.messages:
            role = ""

            if msg["role"] == "assistant":
                role = "model"
            elif msg["role"] == "user":
                role = "user"

            history.append({
                "role": role,
                "parts": [
                    msg["content"]
                ],
            })

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user", avatar="😎").write(prompt)

        best_match_index, best_match_segment = search_with_embeddings(prompt, st.session_state["vectorizer"], st.session_state["embeddings"], st.session_state["scraped_data"])
        
        try:
            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [
                            "Seu nome é WebSage, você é um Guia de turismo 'Web' treinado para responder perguntas sobre conteúdos de sites forncedidos," + 
                            "**utilizando apenas o conteúdo fornecido**, **sem inventar informações**. " +
                            "**Você não deve, em hipotese alguma, responder perguntas que não sejam referente ao conteudo site**," +
                            "pois voce não tem autoridade para responder perguntas sobre outros assuntos que não sejam do site"
                        ],
                    },
                    {
                        "role": "user",
                        "parts": [
                            f"Use o seguinte conteúdo do site {link} para responder: {best_match_segment}"
                        ],
                    }
                ] + history
            )
            
            response = chat_session.send_message(prompt)

            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant", avatar="🧙‍♂️").write(response.text)
        except:
            error_message = "Desculpa, mas não vai ser possivel responder essa pergunta 😓"
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            st.chat_message("assistant", avatar="🧙‍♂️").write(error_message)

    elif not is_valid_url(link):
        st.toast("Por favor, antes de conversarmos me de um link para que seja o tópico da nossa conversa", icon="🧙‍♂️")
        st.stop()