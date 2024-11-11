import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QPainter, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect

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

class MainPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAINEL JS")
        self.setGeometry(100, 100, 350, 500)
        self.setStyleSheet("background-color: #7b4db0; color: #b300ff; font-family: Fantasy, sans-serif;")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.layout = QVBoxLayout()
        
        self.title_label = QLabel("Escolha uma aplicação:", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 22px; padding: 5px 24px; border-radius: 8px; font-weight: bold; color: #000000; background-color: transparent;")
        self.title_label.setFixedHeight(50)

        # JS-Follow Checker
        self.follower_checker_button = AnimatedButton("JS-Follow Checker", self)
        self.follower_checker_button.setStyleSheet("""
            QPushButton {
                background-color: #5e00c9; 
                padding: 12px 24px; 
                border-radius: 8px; 
                color: white;
                font: bold 16px 'Fantasy';
                border: 2px solid transparent;
                text-align: center;
            }
            QPushButton:pressed {
                background-color: #360073;
            }
        """)
        self.follower_checker_button.clicked.connect(self.open_follower_checker)

        # Adiciona as Ui no Layout
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.follower_checker_button)
        # Define o Layout Final
        self.setLayout(self.layout)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Cria um gradiente linear que não gira
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 0, 0))  # Vermelho
        gradient.setColorAt(1, QColor(0, 0, 255))  # Azul

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)  # Remove a borda
        painter.drawRect(self.rect())  # Desenha o retângulo que cobre todo o widget

    def open_follower_checker(self):
        try:
            subprocess.Popen(["python", "JS_Roblox/JS_FollowChecker/main.py"])  # Executa o script do verificador de seguidores
            self.close()  # fecha o painel
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir a aplicação: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_panel = MainPanel()
    main_panel.show()
    sys.exit(app.exec_())