from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget

from hew.util import Scheme


scheme = Scheme()


@scheme
def window(app, body):
    w = QMainWindow()
    w.setCentralWidget(body)
    w.show()
    return w


@scheme
def body(app, layout):
    w = QWidget()
    w.setLayout(layout)
    return w


@scheme
def layout(app, player, button):
    vbox = QVBoxLayout()
    vbox.addWidget(player)
    vbox.addWidget(button)
    return vbox


@scheme
def player(app, player_default_size):
    w = QWidget()
    w.setFixedSize(*player_default_size)
    return w


@scheme
def button(app):
    w = QPushButton()
    return w
