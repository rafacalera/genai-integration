import streamlit as st
from urllib.parse import urlparse
import streamlit as st
from app_service import AppService

app_service = AppService()

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

if "model" not in st.session_state:
    st.session_state["model"] = None
    
if "embeddings" not in st.session_state:
    st.session_state["embeddings"] = None

if "success" not in st.session_state:
    st.session_state["success"] = None

with st.form("link_form"):
    link = st.text_input("Digite o link de um site 🔮")
    submitted = st.form_submit_button("Enviar")
    if submitted and is_valid_url(link):
        scraped_data, st.session_state["success"] = app_service.limited_time_scraping(link, 3)

        if len(scraped_data) != 0:
            st.session_state["scraped_data"] = scraped_data

            st.session_state["model"], st.session_state["embeddings"] = app_service.create_embeddings(st.session_state["scraped_data"])

            if st.session_state["success"]:
                st.info(f"Agora que eu já sei TUDO sobre o site {link}, faça me uma pergunta")
            else:
                st.info(f"Agora que eu já sei sobre o site {link}, faça me uma pergunta")
        else:
            st.toast("Não foi possivel ler o conteúdo do site 😥, Tente novamente ou forneça-me outro link 😁", icon="🧙‍♂️")

    elif submitted and not is_valid_url(link):
        st.info("Por favor, me de um link válido para que possamos conversar", icon="🧙‍♂️")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "model",
        "parts": [
            f"Como eu posso te ajudar?"
        ],
    }]

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message(msg["role"], avatar="😎").write(msg["parts"][0])
    elif st.session_state.messages[0] == msg:
        st.chat_message(msg["role"], avatar="🔮").write(msg["parts"][0])
    elif msg["role"] == "model":
        st.chat_message(msg["role"], avatar="🧙‍♂️").write(msg["parts"][0])

if prompt := st.chat_input("Faça uma pergunta"):
    if not prompt.strip() or len(prompt) == 0:
        st.toast("Faça uma pergunta válida para que possamos conversar!", icon="🧙‍♂️")

    elif st.session_state.scraped_data is None:
        st.toast("Não consigo te responder pois não foi possivel ler o conteúdo do site, Tente outro link 😁", icon="🧙‍♂️")
        st.stop()

    elif is_valid_url(link):
        messages_history = st.session_state.messages

        st.session_state.messages.append({"role": "user", "parts": [prompt]})
        st.chat_message("user", avatar="😎").write(prompt)

        top_k_segments = app_service.search_with_embeddings(prompt, st.session_state["model"], st.session_state["embeddings"], st.session_state["scraped_data"])
        print(top_k_segments)

        try:
            chat_session = app_service.model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [
                            f"Use o seguinte conteúdo do site {link} para responder: {top_k_segments}"
                        ],
                    }
                ] + messages_history
            )

            print(app_service.model.count_tokens(chat_session.history))
            response = chat_session.send_message(prompt)

            st.session_state.messages.append({"role": "model", "parts": [response.text]})
            st.chat_message("model", avatar="🧙‍♂️").write(response.text)
        except:
            error_message = "Desculpa, mas não vai ser possivel responder essa pergunta 😓"
            st.session_state.messages.append({"role": "model", "parts": [error_message]})
            st.chat_message("model", avatar="🧙‍♂️").write(error_message)

    elif not is_valid_url(link):
        st.toast("Por favor, antes de conversarmos me de um link para que seja o tópico da nossa conversa", icon="🧙‍♂️")
        st.stop()