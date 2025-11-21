#!/usr/bin/env python3

import os           # для работы с операционной системой
import platform     # для получения информации о платформе
import getpass      # для получения имени текущего пользователя
import subprocess   # для запуска внешних команд
from pathlib import Path  # для удобной работы с путями файлов


def get_os_info():
    """Получение информации о дистрибутиве Linux"""
    try:
        # Пробуем прочитать /etc/os-release - стандартный файл с информацией о дистрибутиве
        if Path('/etc/os-release').exists():
            with open('/etc/os-release', 'r') as f:
                content = f.read()

            os_info = {}
            # Парсим файл построчно
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"')  # Убираем кавычки вокруг значений
                    os_info[key] = value

            # Сначала пытаемся получить красивое имя
            if 'PRETTY_NAME' in os_info:
                return os_info['PRETTY_NAME']
            # Если нет, то комбинируем имя и версию
            elif 'NAME' in os_info and 'VERSION' in os_info:
                return f"{os_info['NAME']} {os_info['VERSION']}"

        # Запасной вариант: используем команду lsb_release
        result = subprocess.run(['lsb_release', '-d'], capture_output=True, text=True)
        if result.returncode == 0:
            # Извлекаем описание из вывода команды
            return result.stdout.split(':', 1)[1].strip()
    except Exception:
        # В случае любой ошибки возвращаем "Unknown"
        pass

    return "Unknown"


def get_memory_info():
    """Получение информации о памяти из /proc/meminfo"""
    mem_info = {}
    try:
        # Читаем виртуальный файл /proc/meminfo с информацией о памяти
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    # Извлекаем числовое значение (убираем ' kB')
                    num_value = value.strip().split()[0]
                    mem_info[key.strip()] = int(num_value)  # Сохраняем как число
    except Exception:
        # Если файл недоступен, возвращаем пустой словарь
        pass

    return mem_info


def get_load_average():
    """Получение средней загрузки системы за 1, 5 и 15 минут"""
    try:
        # Читаем файл /proc/loadavg с информацией о загрузке системы
        with open('/proc/loadavg', 'r') as f:
            load_avg = f.read().strip().split()
            # Возвращаем первые три значения (1, 5, 15 минут)
            return [float(x) for x in load_avg[:3]]
    except Exception:
        # В случае ошибки возвращаем нулевые значения
        return [0.0, 0.0, 0.0]


def get_disk_info():
    """Получение информации о подключенных дисках и их использовании"""
    drives = []
    try:
        # Читаем файл /proc/mounts со списком смонтированных файловых систем
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    # Разбираем строку на компоненты
                    device, mount_point, fs_type, options = parts[0], parts[1], parts[2], parts[3]

                    # Пропускаем специальные файловые системы (виртуальные, системные)
                    special_fs = [
                        'proc', 'sysfs', 'devtmpfs', 'devpts', 'tmpfs', 'cgroup',
                        'securityfs', 'configfs', 'debugfs', 'tracefs', 'pstore',
                        'efivarfs', 'mqueue', 'hugetlbfs', 'fusectl', 'fuse.gvfsd-fuse',
                        'autofs', 'binfmt_misc', 'nsfs', 'bpf', 'iso9660'
                    ]

                    if fs_type in special_fs:
                        continue  # Пропускаем специальные ФС

                    # Пропускаем виртуальные устройства
                    if device.startswith(('/dev/loop', 'udev', 'none')):
                        continue

                    try:
                        # Получаем статистику файловой системы
                        stat = os.statvfs(mount_point)
                        # Вычисляем общий размер в GB
                        total_gb = (stat.f_blocks * stat.f_frsize) / (1024 ** 3)
                        # Вычисляем свободное место в GB
                        free_gb = (stat.f_bfree * stat.f_frsize) / (1024 ** 3)

                        # Пропускаем диски с нулевым размером или меньше 0.1GB
                        if total_gb < 0.1:
                            continue

                        # Добавляем информацию о диске в список
                        drives.append({
                            'mount_point': mount_point,  # Точка монтирования
                            'fs_type': fs_type,          # Тип файловой системы
                            'total_gb': round(total_gb, 1),  # Общий размер
                            'free_gb': round(free_gb, 1)     # Свободное место
                        })
                    except Exception:
                        # Если не удалось получить статистику, пропускаем этот диск
                        continue
    except Exception:
        # Если не удалось прочитать /proc/mounts, возвращаем пустой список
        pass

    return drives


def get_swap_info():
    """Получение информации о swap-памяти"""
    try:
        # Читаем файл /proc/swaps с информацией о swap-разделах
        with open('/proc/swaps', 'r') as f:
            lines = f.readlines()[1:]  # Пропускаем первую строку (заголовок)
            total_swap = 0
            free_swap = 0

            # Суммируем размер всех swap-разделов
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    total_swap += int(parts[2])  # Размер в килобайтах (третий столбец)

            # Получаем информацию о свободной swap-памяти из meminfo
            mem_info = get_memory_info()
            free_swap = mem_info.get('SwapFree', 0)

            return total_swap, free_swap
    except Exception:
        # Если файл недоступен, возвращаем нулевые значения
        return 0, 0


def main():
    """Основная функция - собирает и выводит всю системную информацию"""
    # Получаем базовую системную информацию
    uname = platform.uname()      # Информация о системе через uname
    mem_info = get_memory_info()  # Информация о памяти
    load_avg = get_load_average() # Средняя загрузка системы

    # Выводим информацию об ОС и дистрибутиве
    os_info = get_os_info()
    print(f"OS: {os_info}")

    # Выводим информацию о ядре Linux
    print(f"Kernel: {uname.system} {uname.release}")

    # Выводим архитектуру процессора
    print(f"Architecture: {uname.machine}")

    # Выводим имя хоста (компьютера)
    print(f"Hostname: {uname.node}")

    # Выводим имя текущего пользователя
    print(f"User: {getpass.getuser()}")

    # Выводим информацию об оперативной памяти (в МБ)
    mem_total = mem_info.get('MemTotal', 0)
    mem_available = mem_info.get('MemAvailable', mem_info.get('MemFree', 0))

    if mem_total > 0:
        # Конвертируем из KB в MB (делим на 1024)
        print(f"RAM: {mem_available // 1024}MB free / {mem_total // 1024}MB total")
    else:
        # Fallback: используем psutil если /proc/meminfo недоступен
        try:
            import psutil
            memory = psutil.virtual_memory()
            # Конвертируем из байт в MB (делим на 1024^2)
            print(f"RAM: {memory.available // (1024 ** 2)}MB free / {memory.total // (1024 ** 2)}MB total")
        except ImportError:
            print("RAM: Information not available")

    # Выводим информацию о swap-памяти
    swap_total, swap_free = get_swap_info()
    if swap_total > 0:
        print(f"Swap: {swap_total // 1024}MB total / {swap_free // 1024}MB free")
    else:
        try:
            import psutil
            swap = psutil.swap_memory()
            print(f"Swap: {swap.total // (1024 ** 2)}MB total / {swap.free // (1024 ** 2)}MB free")
        except ImportError:
            print("Swap: Information not available")

    # Выводим информацию о виртуальной памяти
    vmalloc_total = mem_info.get('VmallocTotal', 0)
    if vmalloc_total > 0:
        print(f"Virtual memory: {vmalloc_total // 1024} MB")
    else:
        print("Virtual memory: information not available")

    # Выводим количество логических процессоров
    try:
        processors = os.cpu_count()
        print(f"Processors: {processors}")
    except Exception:
        print("Processors: Information not available")

    # Выводим среднюю загрузку системы за 1, 5 и 15 минут
    print(f"Load average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")

    # Выводим информацию о подключенных дисках
    drives = get_disk_info()
    print("Drives:")
    if drives:
        for drive in drives:
            # Форматируем вывод для каждого диска
            print(
                f"  {drive['mount_point']:10} {drive['fs_type']:8} {drive['free_gb']}GB free / {drive['total_gb']}GB total")
    else:
        print("  No drives found")


if __name__ == "__main__":
    main()