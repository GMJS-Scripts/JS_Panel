import sys
import requests
import subprocess
import zipfile
import os
import shutil
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QSize, QTimer
from PIL import Image
from io import BytesIO
import tempfile

import config

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(0)

    def enterEvent(self, event):
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRect(self.x() - 2, self.y() - 2, self.width() + 4, self.height() + 4))
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRect(self.x() + 2, self.y() + 2, self.width() - 4, self.height() - 4))
        self.animation.start()
        super().leaveEvent(event)

class UpdateDialog(QDialog):
    def __init__(self, parent=None, latest_version=None):
        super().__init__(parent)
        self.latest_version = latest_version  # Armazena a versão mais recente
        self.setWindowTitle("Atualização Disponível")
        self.setGeometry(100, 100, 300, 150)

        layout = QVBoxLayout()

        # Exibe a mensagem com a versão mais recente
        self.message_label = QLabel(f"Uma nova versão ({self.latest_version}) está disponível. Deseja atualizar?")
        self.message_label.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(self.message_label)

        self.yes_button = QPushButton("Sim")
        self.yes_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        self.yes_button.clicked.connect(self.accept)

        self.no_button = QPushButton("Não")
        self.no_button.setStyleSheet("background-color: #f44336; color: white; padding: 10px; border-radius: 5px;")
        self.no_button.clicked.connect(self.reject)

        layout.addWidget(self.yes_button)
        layout.addWidget(self.no_button)

        self.setLayout(layout)

class RobloxFollowerChecker(QWidget):
    def __init__(self):
        super().__init__()
        
        # URLs base para as APIs
        self.base_follow_url = "https://friends.roblox.com/v1/users/{}/followings?limit=100&sortOrder=Asc"
        self.base_user_id_url = "https://users.roblox.com/v1/usernames/users"
        self.base_thumbnail_url = "https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={}&size=150x150&format=Png&isCircular=true&thumbnailType=HeadShot"

        # Inicializando variáveis para armazenar IDs
        self.header_id = None
        self.header_username = ""
        self.header_diplayname = ""
        self.user_id = None
        self.user_username = ""
        self.user_diplayname = ""
        
        # Chama a função de configuração da interface
        self.init_ui()
        self.check_version()

    def init_ui(self):
        # Configurações da janela principal
        self.setWindowTitle("JS - Follow Checker")
        self.setGeometry(100, 100, 350, 600)  # Tamanho da janela
        self.setStyleSheet("background-color: #020202; color: #b300ff; font-family: Arial, sans-serif;")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout()  # Layout vertical para organizar os componentes

        # Seção para definir o usuário 'Header'
        header_label = QLabel("Definir Usuário Header", self)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 22px; padding: 10px; font-weight: bold; color: white;")

        # Caixa de entrada para o nome de usuário do header
        self.header_entry = QLineEdit("tiogad1", self)
        self.header_entry.setStyleSheet("font-size: 18px; background-color: #444444; padding: 10px; border-radius: 8px; color: white; text-align: center;")
        self.header_entry.setAlignment(Qt.AlignmentFlag.AlignCenter);
        # Botão para definir o header
        self.header_button = AnimatedButton("Definir Header", self)
        self.header_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                padding: 12px 24px; 
                border-radius: 8px; 
                color: white;
                font: bold 16px 'Arial';
                border: 2px solid transparent;
                text-align: center;
            }
            QPushButton:pressed {
                background-color: #45a049;
            }
        """)
        self.header_button.clicked.connect(self.set_header)  # Conecta o clique do botão à função set_header

        # Label para mostrar o status do header
        self.header_status_label = QLabel("", self)
        self.header_status_label.setAlignment(Qt.AlignCenter)
        self.header_status_label.setStyleSheet("font-size: 18px; font-weight: bold; font-size: 18px;")

        # Label para exibir a imagem do usuário header
        self.header_image_label = QLabel(self)
        self.header_image_label.resize(QSize(150, 150))  # Redimensiona a imagem para o tamanho adequado

        # Seção para buscar dados do usuário
        user_label = QLabel("Buscar Usuário", self)
        user_label.setAlignment(Qt.AlignCenter)
        user_label.setStyleSheet("color: white; font-size: 18px; padding: 10px; font-weight: bold;")

        # Caixa de entrada para o nome de usuário a ser buscado
        self.username_entry = QLineEdit(self)
        self.username_entry.setStyleSheet("font-size: 18px; background-color: #444444; padding: 10px; border-radius: 8px; color: white; text-align: center;")
        self.username_entry.setAlignment(Qt.AlignmentFlag.AlignCenter);
        # Botão para buscar o usuário
        self.search_button = AnimatedButton("Buscar", self)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4; 
                padding: 12px 24px; 
                border-radius: 8px; 
                color: white;
                font: bold 16px 'Arial';
                border: 2px solid transparent;
                text-align: center;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
        """)
        self.search_button.clicked.connect(self.fetch_user_data)  # Conecta o clique do botão à função fetch_user_data

        # Label para exibir a imagem do usuário pesquisado
        self.user_image_label = QLabel(self)
        self.user_image_label.resize(QSize(150, 150))  # Redimensiona a imagem para o tamanho adequado

        # Label para mostrar o status do usuário
        self.User_status_label = QLabel("", self)
        self.User_status_label.setAlignment(Qt.AlignCenter)
        self.User_status_label.setStyleSheet("font-size: 18px; font-weight: bold; font-size: 18px;")

        # Botão para verificar se o usuário segue o header
        self.verify_button = AnimatedButton("Verificar", self)
        self.verify_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4081; 
                padding: 12px 24px; 
                border-radius: 8px; 
                color: white;
                font: bold 16px 'Arial';
                border: 2px solid transparent;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #ff79b0;
            }
            QPushButton:pressed {
                background-color: #c73368;
            }
            QPushButton:disabled {
                background-color: #c73368;
                color: #666666;      
                border: 2px solid #aaaaaa;               
            }
        """)
        self.verify_button.clicked.connect(self.verify_follows)  # Conecta o clique do botão à função verify_follows
        
        # Label para mostrar o resultado da verificação
        self.result_label = QLabel("", self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-weight: bold; font-size: 18px;")

        # Adicionando Opções
        self.AlwaysOnTopOption = True
        self.AlwaysOnTopButton = AnimatedButton("Always Top: ON", self)
        self.AlwaysOnTopButton.setStyleSheet("""
            QPushButton {
                background-color: green; 
                padding: 4px 5px; 
                border-radius: 8px; 
                color: white;
                font: bold 16px 'Arial';
                border: 2px solid transparent;
                text-align: center;
            }
            QPushButton:pressed {
                background-color: darkgreen;
            }
        """)
        self.AlwaysOnTopButton.clicked.connect(self.ChangeAlways)
        # Adicionando todos os componentes ao layout
        layout.addWidget(header_label)
        layout.addWidget(self.header_entry)
        layout.addWidget(self.header_button)
        layout.addWidget(self.header_status_label)
        layout.addWidget(self.header_image_label)
        
        layout.addWidget(user_label)
        layout.addWidget(self.username_entry)
        layout.addWidget(self.search_button)
        layout.addWidget(self.User_status_label)
        layout.addWidget(self.user_image_label)
        layout.addWidget(self.verify_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.AlwaysOnTopButton)
        self.setLayout(layout)

    def show_error(self, Message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Error#34")
        msg_box.setText(Message)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setStyleSheet("background-color: #4a4a4a; color: #ffffff")
        msg_box.exec_()

    # Change Always On Top
    def ChangeAlways(self):
        if self.AlwaysOnTopOption == True:
            self.AlwaysOnTopOption = False
            self.AlwaysOnTopButton.setText("Always Top: OFF")
            self.AlwaysOnTopButton.setStyleSheet("""
            QPushButton {
                background-color: red; 
                padding: 4px 5px; 
                border-radius: 8px; 
                color: white;
                font: bold 16px 'Arial';
                border: 2px solid transparent;
                text-align: center;
            }
            QPushButton:pressed {
                background-color: darkred;
            }
        """)
            self.setWindowFlags(Qt.Window)
        else:
            self.AlwaysOnTopOption = True
            self.AlwaysOnTopButton.setText("Always Top: ON")
            self.AlwaysOnTopButton.setStyleSheet("""
            QPushButton {
                background-color: green; 
                padding: 4px 5px; 
                border-radius: 8px; 
                color: white;
                font: bold 16px 'Arial';
                border: 2px solid transparent;
                text-align: center;
            }
            QPushButton:pressed {
                background-color: darkgreen;
            }
        """)
            self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.show()
    # Função para definir o usuário 'Header' e exibir sua imagem
    def set_header(self):
        def StartSetHeader():
            username = self.header_entry.text()  # Obtém o nome de usuário do header
            self.header_id, self.header_username, self.header_diplayname = self.get_user_information(username)  # Obtém o ID do usuário
            if self.header_id:
                header_image = self.get_user_thumbnail(self.header_id)  # Obtém a imagem do usuário header
                self.show_image(header_image, self.header_image_label)  # Exibe a imagem
                self.header_status_label.setText("Header: {}@({})".format(self.header_diplayname, self.header_username))  # Exibe sucesso
                self.header_status_label.setStyleSheet("font-size: 18px; color: green; font-weight: bold;")
            else:
                self.header_status_label.setText("Erro ao definir Header.")  # Exibe erro
                self.header_status_label.setStyleSheet("color: red; font-weight: bold;")
        self.header_status_label.setText("Buscando Header...")
        self.header_status_label.setStyleSheet("font-size: 18px; color: orange; font-weight: bold;")
        QTimer.singleShot(5, StartSetHeader)

    # Função para buscar os dados do usuário
    def fetch_user_data(self):
        def FetchStart():
            username = self.username_entry.text()  # Obtém o nome de usuário
            self.user_id, self.user_username, self.user_diplayname = self.get_user_information(username)  # Obtém o ID do usuário
            if self.user_id:
                user_image = self.get_user_thumbnail(self.user_id)  # Obtém a imagem do usuário
                self.show_image(user_image, self.user_image_label)  # Exibe a imagem
                self.User_status_label.setText("{}@({})".format(self.user_diplayname, self.user_username))  # Exibe sucesso
                self.User_status_label.setStyleSheet("font-size: 18px; color: blue; font-weight: bold;")
                self.result_label.setText("")  # Limpa a mensagem de erro
                self.verify_follows()
            else:
                self.result_label.setText("Erro: Usuário não Encontrado ou Banido.")  # Exibe erro
                self.User_status_label.setText("")  # Limpa o name anterior
                self.result_label.setStyleSheet("font-size: 18px; color: orange; font-weight: bold;")
        self.result_label.setText("Buscando Player...")
        self.result_label.setStyleSheet("font-size: 18px; color: orange; font-weight: bold;")
        QTimer.singleShot(5, FetchStart)

    # Função para obter o ID do usuário a partir do nome de usuário
    def get_user_information(self, username):
        response = requests.post(self.base_user_id_url, json={"usernames": [username], "excludeBannedUsers": True})
        if response.status_code == 200:
            data = response.json().get("data")
            if data:
                return data[0].get("id"), data[0].get("name"), data[0].get("displayName")
        return None, "", ""

    # Função para obter a miniatura do usuário (imagem de perfil)
    def get_user_thumbnail(self, user_id):
        response = requests.get(self.base_thumbnail_url.format(user_id))
        if response.status_code == 200:
            image_url = response.json()["data"][0]["imageUrl"]
            image_response = requests.get(image_url)
            return Image.open(BytesIO(image_response.content))  # Converte a imagem para um objeto PIL
        return None

    # Função para exibir a imagem no label
    def show_image(self, image, label):
        if image:
            img_bytes = BytesIO()
            image.save(img_bytes, format="PNG")  # Salva a imagem em um buffer de bytes
            img_bytes.seek(0)  # Reseta a posição do buffer

            qimage = QImage()  # Inicializa o QImage
            if qimage.loadFromData(img_bytes.read()):  # Tenta carregar a imagem diretamente
                pixmap = QPixmap.fromImage(qimage)  # Converte QImage para QPixmap
                label.setPixmap(pixmap)  # Exibe a imagem no label
                label.setAlignment(Qt.AlignCenter)  # Alinha a imagem horizontalmente ao centro
            else:
                label.setText("Erro ao carregar imagem.")  # Exibe erro caso a imagem não seja carregada corretamente
        else:
            label.setText("Imagem não disponível.")  # Caso a imagem não exista

    def verify_follows(self):
        def startVerify():
            if self.user_id and self.header_id:
                follows = self.get_followings(self.user_id)
                if self.header_id in follows:
                    self.result_label.setText("Usuário segue o Header!")
                    self.result_label.setStyleSheet("font-size: 18px; color: green; font-weight: bold;")
                else:
                    self.result_label.setText("Usuário NÃO segue o Header.")
                    self.result_label.setStyleSheet("font-size: 18px; color: red; font-weight: bold;")
            else:
                self.result_label.setText("Erro: Usuário ou Header não definido.")
                self.result_label.setStyleSheet("font-size: 18px; color: orange; font-weight: bold;")
        self.result_label.setText("Verificando...")
        self.result_label.setStyleSheet("font-size: 18px; color: #FFA07A; font-weight: bold;")
        QTimer.singleShot(200, startVerify)

    def get_followings(self, user_id):
        follows = []
        page = 1
        while True:
            response = requests.get(self.base_follow_url.format(user_id) + "&page={}".format(page))
            if response.status_code == 200:
                data = response.json().get("data")
                follows.extend([user["id"] for user in data])
                if len(data) < 100:
                    break
                page += 1
            else:
                break
        return follows

    def check_version(self):
        """Verifica a versão mais recente do GitHub"""
        try:
            response = requests.get("https://api.github.com/repos/GMJS-Scripts/JS_Panel/releases/latest")
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name']
                zipball_url = release_data['zipball_url']  # Usa o zipball_url para o download

                # Verifica a versão atual
                current_version = config.Version  # Aqui você define a versão atual do seu aplicativo

                if latest_version != current_version:
                    self.show_update_dialog(latest_version, zipball_url)
                else:
                    QMessageBox.information(self, "Sem Atualizações", "Você já está utilizando a versão mais recente!")
            else:
                self.show_error("Erro ao verificar a versão.")
        except Exception as e:
            print(e)
            self.show_error(f"Erro ao verificar a versão: {e}")

    def show_update_dialog(self, latest_version, zipball_url):
        """Exibe um diálogo perguntando ao usuário se deseja atualizar"""
        dialog = UpdateDialog(self, latest_version)
        if dialog.exec_():
            self.download_and_install_update(zipball_url)

    def download_and_install_update(self, zipball_url):
        """Baixa e instala a atualização"""
        try:
            # Baixa o arquivo de atualização
            response = requests.get(zipball_url)
            if response.status_code == 200:
                # Salva o arquivo em um diretório temporário
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_file.close()

                    # Descompacta o arquivo zip
                    with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                        update_dir = os.path.join(os.path.dirname(temp_file.name), "update")
                        zip_ref.extractall(update_dir)

                    # Substitui os arquivos antigos pelo novo
                    self.replace_old_files(update_dir)

                    # Reinicia o aplicativo
                    self.restart_application()
            else:
                self.show_error("Erro ao baixar a atualização.")
        except Exception as e:
            self.show_error(f"Erro durante a atualização: {e}")

    def replace_old_files(self, update_dir):
        """Substitui os arquivos antigos pelos novos"""
        try:
            # O diretório onde os arquivos do aplicativo estão
            app_dir = os.path.dirname(sys.argv[0])

            # Substitui todos os arquivos da versão antiga com os arquivos da versão atualizada
            for filename in os.listdir(update_dir):
                file_path = os.path.join(update_dir, filename)
                if os.path.isdir(file_path):
                    shutil.copytree(file_path, os.path.join(app_dir, filename), dirs_exist_ok=True)
                else:
                    shutil.copy(file_path, os.path.join(app_dir, filename))

            # Remove o diretório temporário após a substituição
            shutil.rmtree(update_dir)
        except Exception as e:
            self.show_error(f"Erro ao substituir os arquivos: {e}")

    def restart_application(self):
        """Reinicia o aplicativo após a atualização"""
        try:
            # Reinicia o aplicativo
            subprocess.Popen([sys.executable] + sys.argv)
            QApplication.quit()
        except Exception as e:
            self.show_error(f"Erro ao reiniciar o aplicativo: {e}")
        """Reinicia o aplicativo após a atualização"""
        try:
            # Reinicia o aplicativo
            subprocess.Popen([sys.executable] + sys.argv)
            QApplication.quit()
        except Exception as e:
            self.show_error(f"Erro ao reiniciar o aplicativo: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RobloxFollowerChecker()
    window.show()
    sys.exit(app.exec_())
