# Ouster LiDAR : Laptop Direct Connection Setup

## Network Details
| Device | Interface | IPv4 |
|--------|-----------|------|
| Laptop | enp109s0 | 169.254.1.1 |
| Ouster LiDAR | — | 169.254.96.62 |

**Sensor hostname:** `os-122136000473.local`

---

## Setup Steps

### 1. Identify network interfaces
This is important since you might have several devices connected to different ethernet ports.

```bash
nmcli connection show
# or
ip addr show
```

### 2. Configure the interface IPv4 method
If you wish to proceed without DHCP, you can either use the static or link-local route. Choose one:

```bash
# Option A: Static (what was used in this setup)
nmcli con modify enp109s0-static ipv4.method manual ipv4.addresses "169.254.1.1/16"

# Option B: Link-Local
nmcli con modify enp109s0-static ipv4.method link-local ipv4.addresses ""
```

### 3. Bring up the connection
```bash
nmcli con up enp109s0-static
```

If this fails, run the following commands manually (required after every reboot):

```bash
nmcli device set enp109s0 managed yes
sudo ip link set enp109s0 up
sudo ip addr add 169.254.1.1/16 dev enp109s0
```

### 4. Verify the interface is up
```bash
ip addr show enp109s0
```
You should see `state UP` and `inet 169.254.1.1/16`.

### 5. Ping, monitor and Visualize
```bash
ping -4 -c3 os-122136000473.local
```
The IP in the response is the sensor's IPv4 address.

You can now also monitor the status of the sensor by opening the following link on your system's browser, or visualise the data from the terminal:

```bash
# Monitor diagnostics
http://os-122136000473.local/ 

# Visualize live sensor
$ ouster-cli source $SENSOR_HOSTNAME viz

```



---

## Notes
- The laptop uses a **static IPv4 address** manually assigned in the link-local range (`169.254.x.x`).
- This setup does **not persist across reboots** — Step 3 must be re-run each session.
- The sensor homepage is accessible at `http://169.254.96.62/` or `http://os-122136000473.local/`.

---

## Troubleshooting
If the interface refuses to come up, check whether the NIC driver is loaded and the cable is detected:

```bash
sudo ethtool enp109s0
```
Look for `Link detected: yes`. If it says `no`, check the cable or the ethernet port.