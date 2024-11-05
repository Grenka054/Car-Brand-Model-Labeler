import sys
import os
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QFileDialog, \
        QMessageBox, QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout,\
        QSizePolicy, QTextEdit, QDialog
from PyQt5.QtGui import QPixmap, QKeyEvent
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi


class CSVEditor(QMainWindow):
    def __init__(self):
        super(CSVEditor, self).__init__()
        loadUi('csv_editor.ui', self)

        self.csv_data = None
        self.current_id = None
        self.current_index = 0
        self.unsaved_changes = False
        self.csv_dir = ""  # Directory of the loaded CSV

        self.loadButton.clicked.connect(self.load_csv)
        self.saveButton.clicked.connect(self.save_csv)
        self.nextButton.clicked.connect(self.next_id)
        self.prevButton.clicked.connect(self.prev_id)
        self.deleteButton.clicked.connect(self.delete_current_image)

        self.copyButton.clicked.connect(self.copy_image_to_clipboard)
        self.actionCopy.triggered.connect(self.copy_image_to_clipboard)
        self.actionCopy.setShortcut('Ctrl+C')

        self.actionSave.triggered.connect(self.save_csv)
        self.actionSave.setShortcut('Ctrl+S')

        self.actionUndo.triggered.connect(self.undo)
        self.actionUndo.setShortcut('Ctrl+Z')
        
        self.actionRedo.triggered.connect(self.redo)
        self.actionRedo.setShortcut('Ctrl+Y')

        self.correctButton.clicked.connect(self.correct_data)
        self.imageList.itemClicked.connect(self.on_image_selected)
        self.imageList.itemSelectionChanged.connect(self.on_image_selection_changed)
        self.imageLabel.setScaledContents(False)  # Сохраняем пропорции изображения

        self.actionShowHelp.triggered.connect(self.show_help)
        
        self.undoStack = []  # Для хранения состояний до изменений
        self.redoStack = []  # Для хранения состояний после отмены изменений

        self.initUI()


    def save_last_directory(self, directory):
        with open('last_directory.txt', 'w') as f:
            f.write(directory)

    def load_last_directory(self):
        if os.path.exists('last_directory.txt'):
            with open('last_directory.txt', 'r') as f:
                last_directory = f.read()
                if os.path.isdir(last_directory):
                    return last_directory
        return ""  # Return an empty string if no saved directory is found or it's not valid
    
    def save_state(self):
        if self.csv_data is not None:
            if len(self.undoStack) > 30:
                self.undoStack.pop(0)
            self.undoStack.append(self.csv_data.copy())
            # Очистим redoStack при каждом новом действии
            self.redoStack.clear()

    def undo(self):
        if self.undoStack:
            self.redoStack.append(self.csv_data.copy())
            self.csv_data = self.undoStack.pop()
            self.update_image_list()
            self.update_view()

    def redo(self):
        if self.redoStack:
            self.undoStack.append(self.csv_data.copy())
            self.csv_data = self.redoStack.pop()
            self.update_image_list()
            self.update_view()

    def copy_image_to_clipboard(self):
        if self.imageLabel.pixmap():
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(self.imageLabel.pixmap())

    def show_help(self):
        try:
            with open('help.html', 'r', encoding='utf-8') as file:
                html = file.read()
                # Создаем окно с QTextEdit для отображения HTML
                help_dialog = QDialog(self)
                help_dialog.setWindowTitle("Справка")
                help_dialog.resize(800, 600)  # Устанавливаем размеры окна
                layout = QVBoxLayout()
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setHtml(html)
                layout.addWidget(text_edit)
                help_dialog.setLayout(layout)
                help_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл справки: {e}")

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Создаем виджет для горизонтального лэйаута и изображения
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # Создаем горизонтальный лэйаут для кнопок и изображения
        button_image_layout = QHBoxLayout()

        # Создаем вертикальный лэйаут для кнопок
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.loadButton)
        button_layout.addWidget(self.saveButton)
        button_layout.addWidget(self.prevButton)
        button_layout.addWidget(self.nextButton)
        button_layout.addWidget(self.deleteButton)

        # Устанавливаем политику размера для кнопок
        self.loadButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.saveButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.prevButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.nextButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Добавляем лэйаут кнопок в горизонтальный лэйаут
        button_image_layout.addLayout(button_layout)

        # Добавляем изображение в горизонтальный лэйаут
        self.imageLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setScaledContents(False)  # Сохраняем пропорции изображения
        button_image_layout.addWidget(self.imageLabel)

        # Добавляем горизонтальный лэйаут в вертикальный лэйаут
        top_layout.addLayout(button_image_layout)

        # Добавляем виджет в основной лэйаут
        main_layout.addWidget(top_widget)

        # Создаем вертикальный сплиттер
        v_splitter = QSplitter(Qt.Vertical)

        # Создаем виджет для метки и списка изображений
        label_widget = QWidget()
        label_layout = QVBoxLayout(label_widget)
        label_layout.addWidget(self.imageNameLabel)
        label_layout.addWidget(self.currentIDLabel)
        label_layout.addWidget(self.excludeNegativeIDCheckbox)
        label_layout.addWidget(self.imageList)

        # Добавляем виджет в вертикальный сплиттер
        v_splitter.addWidget(label_widget)

        # Добавляем таблицу в вертикальный сплиттер
        v_splitter.addWidget(self.tableWidget)

        # Создаем лэйаут для полей под таблицей
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.brandInput)
        input_layout.addWidget(self.modelInput)
        input_layout.addWidget(self.colorInput)
        input_layout.addWidget(self.correctButton)

        # Добавляем лэйаут полей в вертикальный сплиттер
        input_widget = QWidget()
        input_widget.setLayout(input_layout)
        v_splitter.addWidget(input_widget)

        # Добавляем вертикальный сплиттер в основной лэйаут
        main_layout.addWidget(v_splitter)

        self.setWindowTitle('CSV Editor for Car Barnd/Model/Color Classification')
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def on_image_selected(self, item):
        image_path = os.path.join(self.csv_dir, item.text())
        pixmap = QPixmap(image_path)
        self.imageLabel.setPixmap(pixmap.scaled(self.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        if self.imageLabel.pixmap():
            self.imageLabel.setPixmap(self.imageLabel.pixmap().scaled(self.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        super(CSVEditor, self).resizeEvent(event)

    def on_image_selection_changed(self):
        self.current_index = self.imageList.currentRow()
        self.update_image()

    def update_image_list(self):
        # Логика обновления imageList без кадров с id -9999
        self.imageList.clear()
        filtered_data = self.csv_data[self.csv_data['id'] >= 0]
        for image_name in filtered_data['image_name']:
            self.imageList.addItem(image_name)


    def load_csv(self):
        initial_dir = self.load_last_directory()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV", initial_dir, "CSV Files (*.csv)")
        if file_name:
            csv_dir = os.path.dirname(file_name)
            self.save_last_directory(csv_dir) 
            csv_data = pd.read_csv(file_name)
            if 'id' in csv_data.columns:
                self.csv_dir = csv_dir
                self.csv_data = csv_data
                self.csv_data.sort_values(by=['id'], inplace=True)
                self.csv_data.reset_index(drop=True, inplace=True)
                self.set_initial_id()
                self.update_view()
            else:
                QMessageBox.warning(self, "Ошибка загрузки", "В загружаемом CSV файле отсутствует столбец 'id'.")

    def set_initial_id(self):
        if self.excludeNegativeIDCheckbox.isChecked():
            self.current_id = self.csv_data[self.csv_data['id'] >= 0]['id'].iloc[0]
        else:
            self.current_id = self.csv_data['id'].iloc[0]

    def save_csv(self):
        if self.csv_data is not None:
            file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
            if file_name:
                self.csv_data.to_csv(file_name, index=False)
                self.unsaved_changes = False
                self.update_status()

    def update_view(self):
        if self.csv_data is not None:
            id_data = self.csv_data[self.csv_data['id'] == self.current_id]
            self.currentIDLabel.setText("Current ID: {}".format(self.current_id))

            self.imageList.clear()
            for image_name in sorted(id_data['image_name'].tolist()):
                self.imageList.addItem(image_name)
            self.current_index = 0
            self.imageList.setCurrentRow(self.current_index)  # Set the first image as selected
            self.update_image()
            self.update_table(id_data)

    def on_image_selected(self, item):
        self.current_index = self.imageList.row(item)
        self.update_image()

    def update_image(self):
        if self.imageList.count() > 0:
            image_name = self.imageList.item(self.current_index).text()
            image_path = os.path.join(self.csv_dir, image_name)
            try:
                pixmap = QPixmap(image_path)
                if pixmap.isNull():
                    raise FileNotFoundError
                self.imageLabel.setPixmap(pixmap.scaled(self.imageLabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.imageNameLabel.setText(image_name)
            except FileNotFoundError:
                QMessageBox.warning(self, "Image not found", f"Image '{image_path}' could not be loaded.")

    def update_table(self, id_data):
        self.tableWidget.setRowCount(len(id_data))
        for row, (index, data) in enumerate(id_data.iterrows()):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(data['brand']))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(data['model']))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(data['color']))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(str(data['conf'])))

    def get_unique_ids(self):
        if self.excludeNegativeIDCheckbox.isChecked():
            unique_ids = self.csv_data[self.csv_data['id'] >= 0]['id'].unique()
        else:
            unique_ids = self.csv_data['id'].unique()
        return unique_ids

    def adjust_current_id(self, unique_ids):
        unique_ids = self.csv_data['id'].unique()
        if self.current_id not in unique_ids:
            if unique_ids.size > 0:
                next_ids = unique_ids[unique_ids > self.current_id]
                prev_ids = unique_ids[unique_ids < self.current_id]
                if next_ids.size > 0:
                    self.current_id = next_ids[0]  # Устанавливаем следующий допустимый ID
                elif prev_ids.size > 0:
                    self.current_id = prev_ids[-1]  # Устанавливаем предыдущий допустимый ID
                else:
                    self.current_id = unique_ids[0]  # Если следующего допустимого нет, берем первый допустимый
            else:
                self.current_id = None  # Нет допустимых ID


    def next_id(self):
        if self.csv_data is not None:
            unique_ids = self.get_unique_ids()
            self.adjust_current_id(unique_ids)

            if self.current_id is not None and self.current_id in unique_ids:
                current_pos = list(unique_ids).index(self.current_id)
                if current_pos < len(unique_ids) - 1:
                    self.current_id = unique_ids[current_pos + 1]
            self.update_view()

    def prev_id(self):
        if self.csv_data is not None:
            unique_ids = self.get_unique_ids()
            self.adjust_current_id(unique_ids)

            if self.current_id is not None and self.current_id in unique_ids:
                current_pos = list(unique_ids).index(self.current_id)
                if current_pos > 0:
                    self.current_id = unique_ids[current_pos - 1]
            self.update_view()

    def update_current_id(self):
        if self.csv_data is not None:
            unique_ids = self.get_unique_ids()
            self.adjust_current_id(unique_ids)

            if self.current_id is not None and self.current_id in unique_ids:
                current_pos = list(unique_ids).index(self.current_id)
                if current_pos <= len(unique_ids) - 1:
                    self.current_id = unique_ids[current_pos]
            self.update_view()

    def delete_current_image(self):
        if self.csv_data is not None and self.current_id is not None:
            selected_items = self.imageList.selectedItems()
            if selected_items:
                self.save_state()  # Сохраняем текущее состояние перед изменением
                selected_image_name = selected_items[0].text()
                self.csv_data.loc[self.csv_data['image_name'] == selected_image_name, 'id'] = -9999
                self.update_image_list()
                self.update_view()
                if self.imageList.count() == 0:
                    self.update_current_id()


    def correct_data(self):
        if self.csv_data is not None:
            self.save_state()  # Сохраняем текущее состояние перед изменением
            brand = self.brandInput.text()
            model = self.modelInput.text()
            color = self.colorInput.text()
            self.csv_data.loc[self.csv_data['id'] == self.current_id, ['brand', 'model', 'color']] = [brand, model, color]
            self.unsaved_changes = True
            self.update_status()
            self.update_view()

    def update_status(self):
        if self.unsaved_changes:
            self.statusbar.showMessage("Unsaved changes")
            self.setWindowTitle("CSV Editor - Unsaved Changes")
        else:
            self.statusbar.clearMessage()
            self.setWindowTitle("CSV Editor")

    # Keyboard event handler for navigating ids and images
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Right:  # Move to next ID
            self.next_id()
            event.accept()
        elif event.key() == Qt.Key_Left:  # Move to previous ID
            self.prev_id()
            event.accept()
        elif event.key() == Qt.Key_Up:  # Move to previous image in the list
            if self.current_index > 0:
                self.current_index -= 1
                self.imageList.setCurrentRow(self.current_index)  # Highlight the new row
                self.update_image()
            event.accept()
        elif event.key() == Qt.Key_Down:  # Move to next image in the list
            if self.current_index < self.imageList.count() - 1:
                self.current_index += 1
                self.imageList.setCurrentRow(self.current_index)  # Highlight the new row
                self.update_image()
            event.accept()
        elif event.key() == Qt.Key_Delete:
            self.delete_current_image()
        else:
            super().keyPressEvent(event)  # Allow other key events to pass through


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVEditor()
    sys.exit(app.exec_())

