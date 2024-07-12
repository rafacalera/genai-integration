import os
from dotenv import load_dotenv
import threading
import google.generativeai as genai
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import requests
import tldextract
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class AppService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_KEY")
        genai.configure(api_key=self.api_key)
        
        self.model_config = genai.GenerationConfig(
            temperature=0.7,
            top_k=1000,
            max_output_tokens=1000,
            top_p=1
        )

        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=(
                "Seu nome é WebSage, você é um Guia de turismo 'Web' treinado para responder perguntas sobre conteúdos de sites fornecidos,"
                "**utilizando apenas o conteúdo fornecido**, **sem inventar informações**. "
                "**Você não deve, em hipótese alguma, responder perguntas que não sejam referente ao conteúdo do site**, "
                "pois você não tem autoridade para responder perguntas sobre outros assuntos que não sejam do site"
            ),
            generation_config=self.model_config
        )

    def create_embeddings(self, content):
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(content)
        return model, embeddings

    def search_with_embeddings(self, prompt, model, embeddings, content, top_k=2):
        query_vec = model.encode([prompt])
        similarities = cosine_similarity(query_vec, embeddings).flatten()
        top_k_indices = similarities.argsort()[-top_k:][::-1]
        top_k_segments = [(index, content[index], similarities[index]) for index in top_k_indices]
        return top_k_segments

    def scrape_site(self, url, data_collected, stop_event):
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
                    content = soup.get_text().replace("\\n", "")

                    data_collected.append(f"{url} - {title}: {content}")

                    base_domain = tldextract.extract(url).registered_domain
                    for link in soup.find_all('a', href=True):
                        full_url = urljoin(url, link['href'])
                        extracted_domain = tldextract.extract(full_url).registered_domain
                        if extracted_domain == base_domain and full_url not in visited_urls:
                            urls_to_visit.append(full_url)
        except Exception as e:
            print(f"Erro processando o site {url}: {e}")

    def limited_time_scraping(self, url, timeout):
        data_collected = []
        stop_event = threading.Event()
        scraping_thread = threading.Thread(target=self.scrape_site, args=(url, data_collected, stop_event))
        scraping_thread.start()
        scraping_thread.join(timeout=timeout)

        if scraping_thread.is_alive():
            stop_event.set()
            scraping_thread.join()
            return data_collected, False
        else:
            return data_collected, True
