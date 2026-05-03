from prometheus_client import Gauge

hashrate = Gauge("asic_hashrate", "Hashrate", ["ip"])
temp = Gauge("asic_temp", "Temperature", ["ip"])
fan = Gauge("asic_fan", "Fan speed", ["ip"])

# New metrics from /metrics endpoint
chip_temp = Gauge("asic_chip_temp", "Chip max temperature", ["ip"])
pcb_temp = Gauge("asic_pcb_temp", "PCB max temperature", ["ip"])
fan_duty = Gauge("asic_fan_duty", "Fan duty percentage", ["ip"])
power = Gauge("asic_power_watts", "Power consumption in watts", ["ip"])
