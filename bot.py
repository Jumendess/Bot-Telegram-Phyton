from flask import Flask, request, jsonify
import aiohttp
import asyncio
import json
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Substitua pelo token armazenado na variável de ambiente
TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
TELEGRAM_API_URL_FILE = f'https://api.telegram.org/bot{TOKEN}/sendDocument'
TELEGRAM_API_URL_CALLBACK = f'https://api.telegram.org/bot{TOKEN}/answerCallbackQuery'

async def send_message(chat_id, text, reply_markup=None):
    async with aiohttp.ClientSession() as session:
        payload = {
            'chat_id': chat_id,
            'text': text,
            'reply_markup': reply_markup
        }
        async with session.post(TELEGRAM_API_URL, json=payload) as response:
            return await response.text()

async def send_document(chat_id, document_path):
    async with aiohttp.ClientSession() as session:
        with open(document_path, 'rb') as file:
            payload = {
                'chat_id': chat_id,
            }
            files = {'document': file}
            async with session.post(TELEGRAM_API_URL_FILE, data=payload, files=files) as response:
                return await response.text()

async def answer_callback_query(callback_query_id, text):
    async with aiohttp.ClientSession() as session:
        payload = {
            'callback_query_id': callback_query_id,
            'text': text
        }
        async with session.post(TELEGRAM_API_URL_CALLBACK, json=payload) as response:
            return await response.text()

@app.route('/')
def home():
    return "Servidor Flask está funcionando!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Obtém o corpo da requisição como JSON
        json_str = request.get_data(as_text=True)

        # Converte a string JSON para um dicionário Python
        update = json.loads(json_str)

        # Debug: Print the incoming update
        app.logger.info(f'Update received: {update}')

        # Verifica se a mensagem está presente
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message']['text']

            # Debug: Print chat_id and text
            app.logger.info(f'Received message from chat_id: {chat_id}, text: {text}')

            if text.lower() == 'oi':
                response_text = (
                    "Olá! Seja bem-vindo. Sou assistente do Julio. Como posso ajudar? "
                    "Escolha uma das opções abaixo:"
                )
                reply_markup = {
                    'keyboard': [
                        [{'text': 'Experiências Profissionais'}],
                        [{'text': 'Contato'}],
                        [{'text': 'Currículo'}]
                    ],
                    'resize_keyboard': True,
                    'one_time_keyboard': True
                }
                # Envia a mensagem ao chat com a informação desejada e o teclado
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_message(chat_id, response_text, json.dumps(reply_markup)))
            else:
                response_text = get_response_for_query(text)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_message(chat_id, response_text))

            return jsonify({'status': 'ok'}), 200

        elif 'callback_query' in update:
            callback_query_id = update['callback_query']['id']
            chat_id = update['callback_query']['message']['chat']['id']
            callback_data = update['callback_query']['data']

            # Debug: Print callback_query_id and callback_data
            app.logger.info(f'Callback query received: id={callback_query_id}, data={callback_data}')

            if callback_data == 'contato':
                response_text = "Você pode me contatar pelo número: (11) 99884-2630 ou pelo e-mail: julio.mendess608@gmail.com"
            elif callback_data == 'experiencia':
                response_text = (
                    "Aqui estão algumas informações sobre minha experiência profissional:\n\n"
                    "- **Desenvolvedor Chatbot / Curadoria na ADIN (Oracle CX)**\n"
                    "  Outubro de 2023 - Presente\n"
                    "- **Estagiário de Tecnologia**\n"
                    "  Outubro de 2022 - Outubro de 2023\n"
                    "- **Supervisor na RD**\n"
                    "  Agosto de 2015 - Agosto de 2022"
                )
            elif callback_data == 'curriculo':
                # Caminho para o arquivo do currículo na pasta 'cv'
                document_path = 'cv/profile.pdf'
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_document(chat_id, document_path))
                response_text = "Enviando o currículo em anexo..."
                loop.run_until_complete(send_message(chat_id, response_text))
            else:
                response_text = "Opção não reconhecida."

            # Confirma a callback query
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(answer_callback_query(callback_query_id, response_text))

            # Envia a resposta ao chat com a informação desejada
            loop.run_until_complete(send_message(chat_id, response_text))

            return jsonify({'status': 'ok'}), 200

        else:
            app.logger.error('No message or callback_query found in update')
            return jsonify({'error': 'No message or callback_query found'}), 400

    except Exception as e:
        # Em caso de erro, registre o erro e retorne uma mensagem de erro
        app.logger.error(f'Error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

def get_response_for_query(query):
    query = query.lower()
    if 'currículo' in query or 'cv' in query:
        return (
            "Aqui estão as informações do meu currículo:\n\n"
            "*Contato:*\n"
            "- E-mail: julio.mendess608@gmail.com\n"
            "- LinkedIn: https://www.linkedin.com/in/juliomendess\n"
            "- Portfólio: jumendess.github.io/reactportifolio/\n"
            "- Instagram: www.instagram.com/_juliomendes/\n\n"
            "*Principais Competências:*\n"
            "- Liderança de equipe\n"
            "- Desenvolvimento de conteúdo\n"
            "- Desenvolvimento de chatbot\n\n"
            "*Languages:*\n"
            "- Inglês (Elementary)\n\n"
            "*Certifications:*\n"
            "- Algoritmos e Lógica de Programação\n"
            "- Oracle Digital Assistant for Service\n"
            "- Inteligência Artificial\n"
            "- Primeiros Passos com o Microsoft 365 Copilot\n"
            "- Criando chatbots com a plataforma BLiP\n\n"
            "*Resumo:*\n"
            "À frente de soluções inovadoras como Analista de CRM na ADIN, foco na criação de chatbots inteligentes e na melhoria contínua das interações digitais. Com conclusão prevista em Tecnologia da Informação pela Universidade Paulista para junho de 2024, estou comprometido com o avanço e a aplicação de conhecimentos em um campo que está sempre evoluindo.\n\n"
            "*Experiência:*\n"
            "- ADIN - Oracle CX\n"
            "Desenvolvedor Chatbot / Curadoria\n"
            "outubro de 2023 - Present\n"
            "- Estagiário de tecnologia\n"
            "outubro de 2022 - outubro de 2023\n"
            "- RD\n"
            "Supervisor\n"
            "agosto de 2015 - agosto de 2022\n\n"
            "*Formação Acadêmica:*\n"
            "- Universidade Paulista\n"
            "Análise e desenvolvimento de sistemas, Tecnologia da Informação\n"
            "fevereiro de 2022 - junho de 2024"
        )
    elif 'contato' in query:
        return "Você pode me contatar pelo número: (11) 99884-2630 ou pelo e-mail: julio.mendess608@gmail.com"
    elif 'linkedin' in query:
        return "Aqui está o link do LinkedIn: https://www.linkedin.com/in/juliomendess/"
    elif 'portfólio' in query or 'site' in query:
        return "Aqui está o link do meu portfólio: jumendess.github.io/reactportifolio/"
    else:
        return "Desculpe, não entendi sua pergunta. Por favor, pergunte novamente ou escolha uma das opções abaixo."

if __name__ == '__main__':
    app.run(port=5000, debug=True)
