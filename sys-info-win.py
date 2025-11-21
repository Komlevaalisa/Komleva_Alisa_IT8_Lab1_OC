import platform
import socket
import psutil
import os


def get_windows_version():
    """
    Получение информации о версии Windows
    Использует комбинацию platform и проверку версий
    """
    try:
        # Проверяем, что система действительно Windows
        if platform.system() == "Windows":
            version = platform.version()  # Получаем детальную версию
            release = platform.release()  # Получаем основной релиз (7, 8, 10, 11)

            # Сопоставляем номер релиза с человеко-читаемым названием
            version_map = {
                '10': 'Windows 10 or Greater',  # Windows 10 и 11 используют релиз '10'
                '8': 'Windows 8',
                '7': 'Windows 7',
                'vista': 'Windows Vista'
            }

            # Ищем соответствие в словаре версий
            for key, value in version_map.items():
                if key in release.lower():
                    return value

            # Если не нашли в словаре, возвращаем сырую информацию
            return f"Windows {release} ({version})"
        return "Not Windows"  # Если система не Windows
    except (OSError, ValueError, AttributeError) as e:
        # Обработка конкретных ошибок с выводом информации об ошибке
        return f"Unknown (Error: {e})"


def get_computer_name():
    """Получение имени компьютера через стандартную библиотеку socket"""
    try:
        return socket.gethostname()  # Стандартная функция получения имени хоста
    except (socket.error, OSError):
        return "Unknown"  # Возвращаем по умолчанию при ошибке


def get_username():
    """Получение имени текущего пользователя системы"""
    try:
        return os.getlogin()  # Функция возвращает имя пользователя, запустившего процесс
    except (OSError, FileNotFoundError, PermissionError):
        return "Unknown"


def get_processor_architecture():
    """Получение архитектуры процессора через platform"""
    try:
        return platform.machine()  # Возвращает архитектуру (AMD64, x86, ARM64)
    except (AttributeError, OSError):
        return "Unknown"


def get_memory_info():
    """
    Получение информации о физической памяти (RAM)
    Использует psutil для кросс-платформенности и простоты
    """
    try:
        # psutil.virtual_memory() возвращает именованный кортеж с информацией о памяти
        memory = psutil.virtual_memory()
        total_phys_mb = memory.total // (1024 * 1024)  # Конвертируем байты в мегабайты
        avail_phys_mb = memory.available // (1024 * 1024)  # Доступная память
        memory_load = memory.percent  # Процент использования памяти (0-100)

        return total_phys_mb, avail_phys_mb, memory_load
    except (OSError, AttributeError, NotImplementedError) as e:
        print(f"Error getting memory info: {e}")  # Вывод ошибки в консоль
        return 0, 0, 0  # Возвращаем нули при ошибке


def get_pagefile_info():
    """
    Получение информации о файле подкачки (swap memory)
    Файл подкачки - это виртуальная память на диске
    """
    try:
        # psutil.swap_memory() возвращает информацию о swap-файле
        swap = psutil.swap_memory()
        used_mb = swap.used // (1024 * 1024)  # Используемый swap в МБ
        total_mb = swap.total // (1024 * 1024)  # Общий размер swap в МБ
        return used_mb, total_mb
    except (OSError, AttributeError, NotImplementedError) as e:
        print(f"Error getting pagefile info: {e}")
        return 0, 0


def get_processor_count():
    """Получение количества физических ядер процессора"""
    try:
        # logical=False возвращает только физические ядра (без hyper-threading)
        return psutil.cpu_count(logical=False) or 0
    except (OSError, AttributeError, NotImplementedError):
        try:
            # Резервный метод через стандартную библиотеку
            return os.cpu_count() or 0
        except (OSError, AttributeError):
            return 0  # Если все методы не сработали


def get_drives_info():
    """
    Получение информации о всех логических дисках системы
    Возвращает список словарей с информацией о каждом диске
    """
    drives = []  # Создаем пустой список для хранения информации о дисках
    try:
        # psutil.disk_partitions() возвращает список всех разделов диска
        for partition in psutil.disk_partitions():
            # Пропускаем CD-ROM и пустые устройства
            if 'cdrom' in partition.opts or not partition.device:
                continue

            try:
                # Получаем информацию об использовании диска
                usage = psutil.disk_usage(partition.mountpoint)
                total_gb = usage.total // (1024 ** 3)  # Конвертируем в гигабайты
                free_gb = usage.free // (1024 ** 3)  # Свободное место в ГБ

                # Добавляем информацию о диске в список
                drives.append({
                    'drive': partition.device,  # Буква диска (C:\, D:\)
                    'fs_type': partition.fstype,  # Файловая система (NTFS, FAT32)
                    'total_gb': total_gb,  # Общий размер
                    'free_gb': free_gb  # Свободное место
                })
            except (OSError, PermissionError, FileNotFoundError) as e:
                # Если не удалось прочитать диск (например, нет прав доступа)
                print(f"Error reading drive {partition.device}: {e}")
                continue  # Переходим к следующему диску

    except (OSError, AttributeError) as e:
        print(f"Error getting drives info: {e}")

    return drives  # Возвращаем список дисков


def get_virtual_memory_size():
    """
    Расчет общего размера виртуальной памяти
    Виртуальная память = физическая память + файл подкачки
    """
    try:
        memory = psutil.virtual_memory()  # Физическая память
        swap = psutil.swap_memory()  # Файл подкачки
        # Суммируем и конвертируем в МБ
        total_virtual_mb = (memory.total + swap.total) // (1024 * 1024)
        return total_virtual_mb
    except (OSError, AttributeError, NotImplementedError):
        return 0  # Возвращаем 0 при ошибке


def main():
    """
    Основная функция программы
    Координирует получение и вывод всей системной информации
    """

    # Получение всей системной информации путем вызова соответствующих функций
    windows_version = get_windows_version()
    computer_name = get_computer_name()
    username = get_username()
    architecture = get_processor_architecture()

    # Распаковка возвращаемых значений из get_memory_info()
    total_phys_mb, avail_phys_mb, memory_load = get_memory_info()
    used_phys_mb = total_phys_mb - avail_phys_mb  # Расчет используемой памяти
    pagefile_used, pagefile_total = get_pagefile_info()
    processor_count = get_processor_count()
    virtual_memory_mb = get_virtual_memory_size()
    drives = get_drives_info()  # Получаем список дисков

    # Форматированный вывод всей собранной информации
    print(f"OS: {windows_version}")
    print(f"Computer Name: {computer_name}")
    print(f"User: {username}")
    print(f"Architecture: {architecture}")
    print(f"RAM: {used_phys_mb}MB / {total_phys_mb}MB")  # Использовано / Всего
    print(f"Virtual Memory: {virtual_memory_mb}MB")
    print(f"Memory Load: {memory_load}%")
    print(f"Pagefile: {pagefile_used}MB / {pagefile_total}MB")  # Использовано / Всего

    print(f"\nProcessors: {processor_count}")
    # Вывод информации о дисках
    print("Drives:")
    if drives:  # Если список дисков не пустой
        for drive in drives:
            print(
                f"  - {drive['drive']}  ({drive['fs_type']}): {drive['free_gb']} GB free / {drive['total_gb']} GB total")
    else:
        print("  No drives found")  # Сообщение, если диски не найдены


if __name__ == "__main__":
    main()