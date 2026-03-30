import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from RotorProtek_Visual import DataVisualizer, resource_path


def run() -> int:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("logo_app.ico")))
    window = DataVisualizer()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(run())
