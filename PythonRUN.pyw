import platform
import socket
import os
import sys
import datetime
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, font

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False


class DarkThemeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PCInfo")
        self.root.geometry("950x750")
        self.root.minsize(800, 600)
        self.root.configure(bg="#1E1E1E")

        # Путь к папке, где лежит скрипт
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.info_file = os.path.join(self.script_dir, "info.txt")

        # Настройка стилей ttk
        self.setup_styles()

        # Верхняя панель
        self.create_header()

        # Основной фрейм с отступами
        main_frame = ttk.Frame(root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Текстовое поле с кастомным скроллбаром
        self.text_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#252526",
            fg="#D4D4D4",
            insertbackground="#D4D4D4",
            selectbackground="#264F78",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.tag_configure("header", font=("Segoe UI", 12, "bold"), foreground="#007ACC")
        self.text_area.tag_configure("section", font=("Segoe UI", 11, "bold"), foreground="#CCCCCC")
        self.text_area.tag_configure("info", font=("Consolas", 10), foreground="#D4D4D4")
        self.text_area.config(state=tk.DISABLED)

        # Панель с кнопками
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        self.refresh_btn = ttk.Button(
            btn_frame,
            text="🔄 Обновить",
            style="Accent.TButton",
            command=self.refresh_info
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        self.copy_btn = ttk.Button(
            btn_frame,
            text="📋 Копировать всё",
            style="Custom.TButton",
            command=self.copy_to_clipboard
        )
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        # Индикатор сохранения в файл
        self.save_label = ttk.Label(btn_frame, text="", font=("Segoe UI", 9))
        self.save_label.pack(side=tk.LEFT, padx=10)

        # Прогрессбар
        self.progress = ttk.Progressbar(
            btn_frame,
            style="Dark.Horizontal.TProgressbar",
            mode='indeterminate',
            length=200
        )
        self.progress.pack(side=tk.RIGHT, padx=10)

        # Загрузка данных при старте
        self.refresh_info()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg_dark = "#1E1E1E"
        bg_widget = "#2D2D30"
        fg_text = "#D4D4D4"
        accent = "#007ACC"
        accent_hover = "#1C97EA"

        style.configure(".", background=bg_dark, foreground=fg_text)
        style.configure("TFrame", background=bg_dark)
        style.configure("TLabel", background=bg_dark, foreground=fg_text)

        style.configure("Dark.Horizontal.TProgressbar",
                        background=accent,
                        troughcolor=bg_widget,
                        bordercolor=bg_dark,
                        lightcolor=accent,
                        darkcolor=accent)

        style.configure("Custom.TButton",
                        background=bg_widget,
                        foreground=fg_text,
                        borderwidth=1,
                        focusthickness=0,
                        focuscolor="none",
                        relief=tk.FLAT,
                        padding=8,
                        font=("Segoe UI", 9))
        style.map("Custom.TButton",
                  background=[("active", "#3E3E42"), ("pressed", "#4E4E50")],
                  foreground=[("active", "#FFFFFF")],
                  bordercolor=[("active", "#555555")])

        style.configure("Accent.TButton",
                        background=accent,
                        foreground="white",
                        borderwidth=0,
                        focusthickness=0,
                        focuscolor="none",
                        relief=tk.FLAT,
                        padding=8,
                        font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton",
                  background=[("active", accent_hover), ("pressed", "#005A9E")],
                  foreground=[("active", "white")])

        style.configure("Vertical.TScrollbar",
                        background=bg_widget,
                        troughcolor=bg_dark,
                        bordercolor=bg_dark,
                        arrowcolor=fg_text,
                        relief=tk.FLAT,
                        width=12)
        style.map("Vertical.TScrollbar",
                  background=[("active", "#3E3E42")])

    def create_header(self):
        header_frame = tk.Frame(self.root, bg="#007ACC", height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame,
            text="💻  PCInfo",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#007ACC",
            padx=20
        )
        title.pack(side=tk.LEFT, pady=10)

        py_ver = tk.Label(
            header_frame,
            text=f"Python {platform.python_version()}",
            font=("Segoe UI", 9),
            fg="#CCE4FF",
            bg="#007ACC",
            padx=20
        )
        py_ver.pack(side=tk.RIGHT, pady=10)

    def refresh_info(self):
        self.refresh_btn.config(state=tk.DISABLED)
        self.progress.start()
        threading.Thread(target=self._collect_and_display, daemon=True).start()

    def _collect_and_display(self):
        info_text = self.gather_all_info()
        # Сохраняем в файл
        self.save_to_file(info_text)
        # Отображаем в GUI (потокобезопасно)
        self.root.after(0, self._update_text, info_text)

    def save_to_file(self, text):
        """Запись в info.txt в папке со скриптом."""
        try:
            with open(self.info_file, "w", encoding="utf-8") as f:
                f.write(text)
            # Оповещение в GUI через after
            self.root.after(0, lambda: self.show_save_notification("✓ Сохранено в info.txt"))
        except Exception as e:
            self.root.after(0, lambda: self.show_save_notification(f"! Ошибка сохранения: {e}"))

    def show_save_notification(self, message):
        """Временно показывает сообщение рядом с кнопками."""
        self.save_label.config(text=message)
        self.root.after(5000, lambda: self.save_label.config(text=""))

    def _update_text(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)

        lines = text.split('\n')
        for line in lines:
            if line.startswith("=" * 30):
                self.text_area.insert(tk.END, line + "\n", "header")
            elif line.startswith("[") and line.endswith("]"):
                self.text_area.insert(tk.END, line + "\n", "section")
            else:
                self.text_area.insert(tk.END, line + "\n", "info")

        self.text_area.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.NORMAL)
        self.progress.stop()

    def copy_to_clipboard(self):
        content = self.text_area.get(1.0, tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()
        self.show_copy_notification()

    def show_copy_notification(self):
        orig_text = self.copy_btn.cget("text")
        self.copy_btn.config(text="✓ Скопировано!")
        self.root.after(2000, lambda: self.copy_btn.config(text=orig_text))

    # ----------------------------------------------------------------------
    # Сбор информации
    # ----------------------------------------------------------------------
    def gather_all_info(self) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("  🖥  ИНФОРМАЦИЯ О КОМПЬЮТЕРЕ И ОПЕРАЦИОННОЙ СИСТЕМЕ")
        lines.append("=" * 70)

        # 1. Общая информация
        lines.append("")
        lines.append("[ 📋 Основная информация ]")
        lines.append(f"  • Имя компьютера        : {socket.gethostname()}")
        lines.append(f"  • ОС                     : {platform.system()} {platform.release()}")
        lines.append(f"  • Версия ОС              : {platform.version()}")
        lines.append(f"  • Архитектура            : {platform.machine()}")
        lines.append(f"  • Платформа              : {platform.platform()}")
        lines.append(f"  • Пользователь           : {os.getlogin()}")
        lines.append(f"  • Домашняя папка         : {os.path.expanduser('~')}")
        lines.append(f"  • Версия Python          : {sys.version}")

        # 2. Процессор
        lines.append("")
        lines.append("[ ⚙ Процессор (CPU) ]")
        lines.append(f"  • Модель                 : {platform.processor() or 'Неизвестно'}")
        if PSUTIL_AVAILABLE:
            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    lines.append(f"  • Текущая частота        : {cpu_freq.current:.2f} МГц")
                    if cpu_freq.min:
                        lines.append(f"  • Минимальная частота    : {cpu_freq.min:.2f} МГц")
                    if cpu_freq.max:
                        lines.append(f"  • Максимальная частота   : {cpu_freq.max:.2f} МГц")
                cores_physical = psutil.cpu_count(logical=False)
                cores_logical = psutil.cpu_count(logical=True)
                lines.append(f"  • Физических ядер        : {cores_physical}")
                lines.append(f"  • Логических ядер        : {cores_logical}")
                cpu_percent = psutil.cpu_percent(interval=0.5, percpu=False)
                lines.append(f"  • Загрузка ЦП (средняя)  : {cpu_percent}%")
                per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
                lines.append(f"  • Загрузка по ядрам      : {', '.join([f'{i}: {p}%' for i, p in enumerate(per_cpu)])}")
            except Exception as e:
                lines.append(f"  ! Ошибка CPU: {e}")
        else:
            lines.append("  (psutil не установлен)")

        # 3. Память
        lines.append("")
        lines.append("[ 🧠 Оперативная память (RAM) ]")
        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                swap = psutil.swap_memory()
                lines.append(f"  • Всего RAM              : {self._bytes_to_human(mem.total)}")
                lines.append(f"  • Доступно               : {self._bytes_to_human(mem.available)}")
                lines.append(f"  • Использовано           : {self._bytes_to_human(mem.used)} ({mem.percent}%)")
                lines.append(f"  • Свободно               : {self._bytes_to_human(mem.free)}")
                lines.append(f"  • SWAP всего             : {self._bytes_to_human(swap.total)}")
                lines.append(f"  • SWAP использовано      : {self._bytes_to_human(swap.used)} ({swap.percent}%)")
                lines.append(f"  • SWAP свободно          : {self._bytes_to_human(swap.free)}")
            except Exception as e:
                lines.append(f"  ! Ошибка памяти: {e}")
        else:
            lines.append("  (psutil не установлен)")

        # 4. Диски
        lines.append("")
        lines.append("[ 💾 Диски и разделы ]")
        if PSUTIL_AVAILABLE:
            try:
                partitions = psutil.disk_partitions(all=False)
                for part in partitions:
                    lines.append(f"  📁 Устройство: {part.device}")
                    lines.append(f"     • Точка монтирования : {part.mountpoint}")
                    lines.append(f"     • Файловая система   : {part.fstype}")
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        lines.append(f"     • Общий объём        : {self._bytes_to_human(usage.total)}")
                        lines.append(f"     • Использовано       : {self._bytes_to_human(usage.used)} ({usage.percent}%)")
                        lines.append(f"     • Свободно           : {self._bytes_to_human(usage.free)}")
                    except PermissionError:
                        lines.append("     (нет прав)")
            except Exception as e:
                lines.append(f"  ! Ошибка разделов: {e}")
        else:
            lines.append("  (psutil не установлен)")

        # 5. Сеть
        lines.append("")
        lines.append("[ 🌐 Сетевые интерфейсы ]")
        if PSUTIL_AVAILABLE:
            try:
                net_if = psutil.net_if_addrs()
                for iface, addr_list in net_if.items():
                    lines.append(f"  🔌 {iface}")
                    for addr in addr_list:
                        lines.append(f"     • Семейство: {addr.family}, Адрес: {addr.address}")
                        if addr.netmask:
                            lines.append(f"       Маска: {addr.netmask}")
                        if addr.broadcast:
                            lines.append(f"       Broadcast: {addr.broadcast}")
                lines.append("")
                lines.append("  📊 Статистика трафика:")
                net_io = psutil.net_io_counters(pernic=True)
                for iface, io in net_io.items():
                    lines.append(f"    {iface}:")
                    lines.append(f"       Отправлено : {self._bytes_to_human(io.bytes_sent)}")
                    lines.append(f"       Получено   : {self._bytes_to_human(io.bytes_recv)}")
            except Exception as e:
                lines.append(f"  ! Ошибка сети: {e}")
        else:
            lines.append("  (psutil не установлен)")

        # 6. GPU
        lines.append("")
        lines.append("[ 🎮 Видеокарта (GPU) ]")
        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    for gpu in gpus:
                        lines.append(f"  • Название: {gpu.name}")
                        lines.append(f"  • Память всего: {gpu.memoryTotal} МБ")
                        lines.append(f"  • Загрузка: {gpu.load*100:.1f}%")
                        lines.append(f"  • Температура: {gpu.temperature}°C")
                else:
                    lines.append("  GPU не обнаружены.")
            except Exception as e:
                lines.append(f"  ! Ошибка GPU: {e}")
        elif PSUTIL_AVAILABLE and sys.platform == "win32":
            try:
                import wmi
                w = wmi.WMI()
                for gpu in w.Win32_VideoController():
                    lines.append(f"  • Название: {gpu.Name}")
                    lines.append(f"  • Производитель: {gpu.AdapterCompatibility or 'Н/Д'}")
                    lines.append(f"  • Видеопамять: {gpu.AdapterRAM or 'Н/Д'} байт")
                    if gpu.CurrentHorizontalResolution:
                        lines.append(f"  • Разрешение: {gpu.CurrentHorizontalResolution}x{gpu.CurrentVerticalResolution} @{gpu.CurrentRefreshRate} Гц")
            except ImportError:
                lines.append("  (Установите 'wmi' для данных GPU)")
            except Exception as e:
                lines.append(f"  ! Ошибка: {e}")
        else:
            lines.append("  (GPUtil не установлен)")

        # 7. Датчики
        lines.append("")
        lines.append("[ 🌡 Температурные датчики ]")
        if PSUTIL_AVAILABLE:
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for chip, entries in temps.items():
                        lines.append(f"  Чип: {chip}")
                        for entry in entries:
                            lines.append(f"    • {entry.label or 'Датчик'}: {entry.current}°C")
                else:
                    lines.append("  Датчики не найдены.")
            except:
                lines.append("  Нет доступа к датчикам.")
        else:
            lines.append("  (psutil не установлен)")

        # 8. Время работы
        lines.append("")
        lines.append("[ ⏱ Время работы ]")
        if PSUTIL_AVAILABLE:
            try:
                boot = datetime.datetime.fromtimestamp(psutil.boot_time())
                now = datetime.datetime.now()
                uptime = now - boot
                lines.append(f"  • Загрузка: {boot.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(f"  • Прошло: {str(uptime).split('.')[0]}")
            except:
                lines.append("  Не удалось определить.")
        else:
            lines.append("  (psutil не установлен)")

        lines.append("")
        lines.append("=" * 70)
        lines.append(f"  Отчёт создан: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(lines)

    @staticmethod
    def _bytes_to_human(num_bytes):
        for unit in ('Б', 'КБ', 'МБ', 'ГБ', 'ТБ'):
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:3.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} ПБ"


def main():
    if not PSUTIL_AVAILABLE:
        import tkinter.messagebox as mb
        root_temp = tk.Tk()
        root_temp.withdraw()
        mb.showwarning("Библиотека не найдена",
                       "Установите psutil: pip install psutil\n"
                       "Приложение запущено с ограниченной информацией.")
        root_temp.destroy()

    root = tk.Tk()
    app = DarkThemeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()