import sys
import traceback
import datetime
import shutil
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from functions import tau, M, sig, plot

class MainWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # готовим отдельный поток для вычислений
        self.threadpool = QtCore.QThreadPool()

        # лимиты для ввода чисел -- от 1 до 2 миллиардов
        limits = (1, 2*1000*1000*1000)

        self.last_data = None

        # заголовок окна
        self.setWindowTitle('Программная система')

        # панели для компоновки
        self.layout = QtWidgets.QVBoxLayout(self)
        self.data_input_layout = QtWidgets.QHBoxLayout()
        self.result_layout = QtWidgets.QVBoxLayout()

        # вкладываем дочерние панели в родительскую
        self.layout.addLayout(self.data_input_layout)
        self.layout.addLayout(self.result_layout)

        # элементы управления для ввода данных
        # текст
        self.label_from = QtWidgets.QLabel("От")
        self.label_to = QtWidgets.QLabel("До")
        # отдельный текст для отображения прогресса
        self.label_progress = QtWidgets.QLabel("Жду ввода")

        # ввод чисел
        self.spin_from = QtWidgets.QSpinBox()
        self.spin_from.setMinimum(limits[0])
        self.spin_from.setMaximum(limits[1])
        self.spin_from.setValue(1)

        # 5.06: запретить менять начальное число
        self.spin_from.setEnabled(False)

        self.spin_to = QtWidgets.QSpinBox()
        self.spin_to.setMinimum(limits[0])
        self.spin_to.setMaximum(limits[1])
        self.spin_to.setValue(10)

        # кнопка для запуска вычислений
        self.button_run = QtWidgets.QPushButton("Вычислить")
        # кнопка для остановки вычислений
        self.button_stop = QtWidgets.QPushButton("Остановить")
        # скрываем и выключаем кнопку для остановки
        self.button_stop.setEnabled(False)
        self.button_stop.setHidden(True)

        # добавляем элементы в компоновку data_input_layout
        self.data_input_layout.addWidget(self.label_from)
        self.data_input_layout.addWidget(self.spin_from)
        self.data_input_layout.addWidget(self.label_to)
        self.data_input_layout.addWidget(self.spin_to)
        self.data_input_layout.addStretch() # растягивающееся пустое место
        self.data_input_layout.addWidget(self.label_progress)
        self.data_input_layout.addWidget(self.button_run)
        self.data_input_layout.addWidget(self.button_stop)

        # на событие 'clicked' кнопки "Вычислить" вешаем обработчик run()
        self.button_run.clicked.connect(self.run)
        # аналогично для второй кнопки
        self.button_stop.clicked.connect(self.stop)

        # загрузка шрифта
        self.font = QtGui.QFont("Courier New")
        self.font.setStyleHint(QtGui.QFont.Monospace)

        # загрузка картинки
        # self.pic = QtGui.QImage('600x300.png')
        # self.pixmap = QtGui.QPixmap(self.pic)

        # создание метки, где будет картинка
        self.label_plot = QtWidgets.QLabel()
        # self.label_plot.setPixmap(self.pixmap)

        # создание текстового поля
        self.text_box = QtWidgets.QPlainTextEdit('') # с пустым текстом
        self.text_box.setReadOnly(True) # только для чтения (запретить ввод)
        self.text_box.setFont(self.font) # установить шрифт, который загрузили

        # создание кнопки для сохранения отчёта
        self.button_save_report = QtWidgets.QPushButton('Сохранить отчёт')
        self.button_save_report.clicked.connect(self.save_report)
        self.layout_button_save = QtWidgets.QHBoxLayout()
        self.layout_button_save.addStretch()
        self.layout_button_save.addWidget(self.button_save_report)

        # добавление элементов в компоновку result_layout
        self.result_layout.addWidget(self.label_plot)
        self.result_layout.addWidget(self.text_box)
        self.result_layout.addLayout(self.layout_button_save)
    
    @QtCore.Slot()
    def run(self):
        # обрабатываем нажатие кнопки

        # получаем значения из числовых полей
        start = self.spin_from.value()
        end = self.spin_to.value()

        # проверка данных
        if start >= end:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', 'Начальное значение должно быть строго меньше конечного.')
            return
        
        # выключаем и скрываем кнопку для запуска, чтобы не нажимали, пока всё не посчиталось
        self.button_run.setEnabled(False)
        self.button_run.setHidden(True)
        # включаем и показываем кнопку для остановки
        self.button_stop.setEnabled(True)
        self.button_stop.setHidden(False)
        
        # выносим вычисления в отдельный поток, чтобы окно не зависло
        self.worker = worker = CalculationWorker(start, end)
        # вешаем события
        worker.signals.finished.connect(self.calculations_finished)
        worker.signals.progress.connect(self.calculations_progressed)
        worker.signals.result.connect(self.calculations_resulted)
        worker.signals.error.connect(self.calculations_failed)
        self.threadpool.start(worker)
    
    @QtCore.Slot()
    def save_report(self):
        stats, values, m, s, plot_filename, forced_stop = self.last_data

        now = datetime.datetime.now()

        report_folder = Path('Отчеты')
        report_folder.mkdir(exist_ok=True)
        report_filename_template = (
            f'{now.isoformat(sep=" ", timespec="seconds")}'
            .replace(':', '.')
        )

        report_plot = report_folder / Path(report_filename_template + '.png')
        report_file = report_folder / Path(report_filename_template + '.html')
        old_plot = Path(plot_filename)

        shutil.copy(old_plot, report_plot)

        forced_stop_notice = f'<p>Вычисления были остановлены после {forced_stop}</p>' if forced_stop else ''

        values_texts = []

        for number in range(min(values.keys()), max(values.keys()) + 1):
            tau = f'τ({number})'
            values_texts.append(
                f'{tau:>12} = {values[number]:<8}'
            )
            if number % 5 == 0:
                values_texts.append('\n')
        
        values_text = ''.join(values_texts)

        text = (
            f"<html><head><title>Отчёт {now.strftime('%d %b, %Y')}</title></head>"
            f"<body style='display: flex; flex-direction: column; align-items: center;'><img src='{report_plot.name}' />"
            f"<p>Математическое ожидание: {m}</p>"
            f"<p>Дисперсия: {s}</p>"
            f"{forced_stop_notice}"
            f"<pre>"
            f"{values_text}"
            f"</pre></body></html>"
        )

        with open(report_file, 'wt', encoding="utf-8") as report:
            print(text, file=report)

        QtWidgets.QMessageBox.information(self, 'Отчёт сохранён', f'Отчёт сохранён в папку "Отчёты", в файл "{str(report_file)}".')


    @QtCore.Slot()
    def stop(self):
        self.worker.stop_flag = True

    @QtCore.Slot()
    def calculations_finished(self):
        # вычисления закончились, с ошибкой или без
        # надо вернуть кнопки, как было
        self.button_run.setEnabled(True)
        self.button_run.setHidden(False)
        self.button_stop.setEnabled(False)
        self.button_stop.setHidden(True)
        # и обновить прогресс
        self.label_progress.setText('Жду ввода')
    
    @QtCore.Slot()
    def calculations_progressed(self, name):
        # вычисления ещё идут, есть прогресс
        # отобразим прогресс на форме
        self.label_progress.setText('Считаю: ' + name)

    @QtCore.Slot()
    def calculations_resulted(self, results):
        # вычисления закончились, есть результат
        stats, values, m, s, plot_filename, forced_stop = self.last_data = results
        text = ""

        if forced_stop:
            text += f'Вычисления были остановлены после {forced_stop}\n'

        text += (
            f'Мат. ожидание: {m}\n' +
            f'Дисперсия: {s}\n'
        )

        # меняем текст в поле
        self.text_box.setPlainText(text)
        # загружаем график в виде картинки
        self.pic = QtGui.QImage(plot_filename)
        self.pixmap = QtGui.QPixmap(self.pic)
        self.label_plot.setPixmap(self.pixmap)

    @QtCore.Slot()
    def calculations_failed(self, error):
        # вычисления закончились с ошибкой
        # показываем окно с ошибкой
        QtWidgets.QMessageBox.critical(self, 'Ошибка', f'Произошла необработанная ошибка! Вот техническая информация:\n\n{error[0]}')

class CalculationWorker(QtCore.QRunnable):
    def __init__(self, start, end):
        super().__init__()
        self.range = range(start, end + 1)
        self.signals = CalculationSignals()
        self.stop_flag = False
        self.stopped_at = None

    @QtCore.Slot()
    def run(self):
        try:
            stats = dict()
            values = dict()

            for number in self.range:
                if self.stop_flag:
                    self.stopped_at = number - 1
                    break

                if number > 10000000 or number % 2048 == 0:
                    self.signals.progress.emit(str(number))

                values[number] = value = tau(number)

                if value in stats.keys():
                    stats[value] += 1
                else:
                    stats[value] = 1

            self.signals.progress.emit('итоги')
            
            m = M(stats)
            s = sig(stats)
            plot_filename = plot(stats)

            self.signals.result.emit((stats, values, m, s, plot_filename, self.stopped_at))

        except Exception as e:
            traceback.print_exc()
            self.signals.error.emit((traceback.format_exc(),))
        finally:
            self.signals.finished.emit()

class CalculationSignals(QtCore.QObject):
    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    progress = QtCore.Signal(str)
    result = QtCore.Signal(tuple)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWidget()
    widget.resize(600, 600)
    widget.show()

    sys.exit(app.exec())
