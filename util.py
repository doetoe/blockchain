import socket
from dateutil import tz, parser

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

def convert_timezone(s, from_zone, to_zone):
    """Converts a datetime iso string (datetime.isoformat()) from one zone to another"""
    if isinstance(s, str):
        s = parser.parse(s)
    s = s.replace(tzinfo=from_zone)
    return s.astimezone(to_zone).isoformat() 
    
def utc_to_local(s):
    """Converts a datetime iso string (datetime.isoformat()) from utc to local time"""
    return convert_timezone(
        s, from_zone = tz.tzutc(), to_zone = tz.tzlocal())
