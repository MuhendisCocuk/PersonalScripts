import platform
import subprocess
import re

def get_os():
    return platform.system()

def get_ssds_windows():
    ssds = []
    try:
        # Tüm diskleri listeler
        cmd = 'wmic diskdrive get DeviceID,Model,MediaType'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        lines = result.stdout.splitlines()[1:]
        for line in lines:
            if line.strip() == "":
                continue
            parts = line.split()
            # SSD olanları filtrele
            if "SSD" in line.upper():
                device = parts[0]
                model = " ".join(parts[1:-1])
                ssds.append({"device": device, "model": model, "health": 100})  # Windows kabaca %100
    except Exception:
        pass
    return ssds

def get_ssds_linux():
    ssds = []
    try:
        # Tüm diskleri listeler
        result = subprocess.run(["lsblk", "-d", "-o", "NAME,TYPE,MODEL"], capture_output=True, text=True)
        lines = result.stdout.splitlines()[1:]
        for line in lines:
            name, dtype, *model = line.split()
            if dtype == "disk":
                device_path = "/dev/" + name
                model_name = " ".join(model)
                health = get_smart_health_linux(device_path)
                ssds.append({"device": device_path, "model": model_name, "health": health})
    except Exception:
        pass
    return ssds

def get_smart_health_linux(disk):
    try:
        result = subprocess.run(["sudo", "smartctl", "-A", disk], capture_output=True, text=True)
        output = result.stdout
        # Health için SMART overall-health
        match = re.search(r"SMART overall-health self-assessment test result:\s*(\w+)", output)
        if match:
            status = match.group(1)
            if status.lower() == "passed":
                return 100
            else:
                return 50
        # Alternatif Percentage Used
        match = re.search(r"Percentage Used:\s+(\d+)", output)
        if match:
            used = int(match.group(1))
            return 100 - used
        return None
    except Exception:
        return None

if __name__ == "__main__":
    os_name = get_os()
    ssds = []

    if os_name == "Windows":
        ssds = get_ssds_windows()
    else:
        ssds = get_ssds_linux()

    # Sağlık durumuna göre azalan sırada sıralama
    ssds_sorted = sorted(ssds, key=lambda x: x["health"] if x["health"] is not None else 0, reverse=True)

    print(f"Bulunan SSD'ler ({len(ssds_sorted)}):\n")
    for ssd in ssds_sorted:
        print(f"Model: {ssd['model']}, Cihaz: {ssd['device']}, Health: {ssd['health']}%")