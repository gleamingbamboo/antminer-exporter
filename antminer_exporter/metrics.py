from prometheus_client import Gauge

hashrate = Gauge("asic_hashrate", "Hashrate", ["ip"])
temp = Gauge("asic_temp", "Temperature", ["ip"])
fan = Gauge("asic_fan", "Fan speed", ["ip"])
