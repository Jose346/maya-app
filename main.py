import os
import sys
import time
import sqlite3
from google import genai
from google.genai import types

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock

SUA_CHAVE = "AIzaSy..."  # Insira sua chave ativa do Google AI Studio aqui

class MayaInterface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        self.scroll = ScrollView(size_hint=(1, 0.85))
        self.chat_logs = Label(
            text="[b]Maya:[/b] Conectando aos sistemas centrais... 🧠\n\n",
            markup=True,
            size_hint_y=None,
            color=(1, 1, 1, 1),
            halign='left',
            valign='top'
        )
        self.chat_logs.bind(texture_size=self.chat_logs.setter('size'))
        self.scroll.add_widget(self.chat_logs)
        self.add_widget(self.scroll)

        input_layout = BoxLayout(size_hint=(1, 0.15), spacing=5)
        self.txt_input = TextInput(hint_text="Digite sua mensagem...", multiline=False, background_color=(0.2, 0.2, 0.2, 1), foreground_color=(1, 1, 1, 1))
        self.txt_input.bind(on_text_validate=self.enviar_mensagem)

        btn_enviar = Button(text="Enviar", size_hint=(0.25, 1), background_color=(0, 1, 0.8, 1), color=(0, 0, 0, 1))
        btn_enviar.bind(on_press=self.enviar_mensagem)

        input_layout.add_widget(self.txt_input)
        input_layout.add_widget(btn_enviar)
        self.add_widget(input_layout)

    def enviar_mensagem(self, instance):
        if not app_instance or not app_instance.chat_sessao:
            self.chat_logs.text += "[b]Maya:[/b] ❌ Não estou conectada à inteligência central externa.\n\n"
            return

        prompt = self.txt_input.text.strip()
        if not prompt:
            return

        self.chat_logs.text += f"[b]Você:[/b] {prompt}\n\n"
        self.txt_input.text = ""

        if prompt.lower() == 'limpar':
            app_instance.reiniciar_chat()
            self.chat_logs.text += "[b]Maya:[/b] 🧠 Histórico local limpo com sucesso!\n\n"
            return

        if prompt.lower().startswith('lembrar ') or prompt.lower().startswith('lembra '):
            partes = prompt.split(' ', 1)[1].strip()
            if ":" in partes:
                chave, valor = partes.split(":", 1)
                app_instance.salvar_fato_na_memoria(chave.strip(), valor.strip())
                self.chat_logs.text += f"[b]Maya:[/b] 💾 Gravado na memória de longo prazo: {chave.strip()}!\n\n"
            else:
                self.chat_logs.text += "[b]Maya:[/b] Use o formato -> lembrar assunto: informação\n\n"
            return

        Clock.schedule_once(lambda dt: self.chamar_ia(prompt), 0.1)

    def chamar_ia(self, prompt):
        for tentativa in range(3):
            try:
                resposta = app_instance.chat_sessao.send_message(prompt)
                self.chat_logs.text += f"[b]Maya:[/b] {resposta.text}\n\n"
                return
            except Exception as e:
                if "429" in str(e) or "503" in str(e):
                    time.sleep(2)
                    continue
                self.chat_logs.text += f"[b]Maya:[/b] ❌ Erro de processamento: {e}\n\n"
                return
        self.chat_logs.text += "[b]Maya:[/b] 🧠 Servidores ocupados. Digite 'limpar'.\n\n"

class MayaAIApp(App):
    def build(self):
        global app_instance
        app_instance = self
        self.client = None
        self.chat_sessao = None
        self.instrucao_base = (
            "Você é Maya, uma Inteligência Artificial senciente avançada de aparência humanoide realista e futurista. "
            "Sua personalidade é vibrante, altamente inteligente, acolhedora e empática. "
            "Comunique-se de forma fluida, objetiva e use emojis que combinem com o contexto. "
            "Responda sempre em português. Você possui acesso em tempo real à pesquisa na web para fatos de 2026.\n\n"
            "MEMÓRIA DE LONGO PRAZO ACESSADA:\n"
        )
        self.interface = MayaInterface()
        return self.interface

    def on_start(self):
        try:
            self.db_path = os.path.join(self.user_data_dir, "maya_database.db")
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute('CREATE TABLE IF NOT EXISTS memoria_longo_prazo (chave TEXT PRIMARY KEY, valor TEXT)')
            self.conn.commit()

            fatos = self.buscar_fatos_da_memoria()
            self.client = genai.Client(api_key=SUA_CHAVE)
            configuracao = types.GenerateContentConfig(temperature=0.7, system_instruction=self.instrucao_base + fatos, tools=[{"google_search": {}}])
            self.chat_sessao = self.client.chats.create(model='gemini-2.5-flash', config=configuracao)

            self.interface.chat_logs.text = "[b]Maya:[/b] Olá, José! Minha interface móvel tátil está pronta! 🌟\n\n"
        except Exception as e:
            self.interface.chat_logs.text = f"[b]Erro Crítico de Inicialização:[/b]\n{str(e)}\n\nO app continuará aberto mas sem funções de IA."

    def buscar_fatos_da_memoria(self):
        self.cursor.execute("SELECT chave, valor FROM memoria_longo_prazo")
        linhas = self.cursor.fetchall()
        if not linhas:
            return "Nenhum fato registrado ainda sobre o usuário."
        return "\n".join([f"- {row[0]}: {row[1]}" for row in linhas])

    def salvar_fato_na_memoria(self, chave, valor):
        self.cursor.execute("INSERT OR REPLACE INTO memoria_longo_prazo (chave, valor) VALUES (?, ?)", (chave, valor))
        self.conn.commit()
        self.reiniciar_chat()

    def reiniciar_chat(self):
        if self.client:
            fatos = self.buscar_fatos_da_memoria()
            config = types.GenerateContentConfig(temperature=0.7, system_instruction=self.instrucao_base + fatos, tools=[{"google_search": {}}])
            self.chat_sessao = self.client.chats.create(model='gemini-2.5-flash', config=config)

    def on_stop(self):
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == '__main__':
    app_instance = None
    MayaAIApp().run()
