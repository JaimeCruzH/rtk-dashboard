import socket
s = socket.socket()
s.settimeout(1)
r = s.connect_ex(('0.0.0.0', 8088))
print('Free' if r != 0 else 'Busy')
s.close()
