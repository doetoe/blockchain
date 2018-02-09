import socket

def port_is_free(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("0.0.0.0", port))
        result = True
    except:
        result = False
    finally:
        sock.close()
    return result
