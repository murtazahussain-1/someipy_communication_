# Communication Using SOME/IP Protocol
This project sends the temperature of a device's 4 logical cores to a receiver using SOME/IP protocol using a UDP layer.

# Dependencies
```bash
pip3 install someipy
pip3 install psutils
// Also install Python 3.12>=
```
# How to run the project?
```bash
sudo su
cd example_apps

// Create and run a virtual python environment
python3 -m venv env
source env/bin/activate

// Start the receiver
python3 someipy_receive_udp.py

// Repeat the above mentioned steps except the last command, on another PC
python3 someipy_send_udp.py
```
