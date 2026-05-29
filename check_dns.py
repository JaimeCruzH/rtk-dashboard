import socket

try:
    ip = socket.gethostbyname('agentexperto.work')
    print(f'agentsxperto.work resolves to: {ip}')
except Exception as e:
    print(f'DNS resolution failed: {e}')

try:
    ip = socket.gethostbyname('38.242.211.89')
    host = socket.gethostbyaddr('38.242.211.89')
    print(f'Reverse lookup of 38.242.211.89: {host[0]}')
except Exception as e:
    print(f'Reverse lookup failed (normal if no PTR record): {e}')