import uuid
import hashlib, binascii, os

REMOVE = False

def get_id():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        if 'nt' in os.name: #windows
            cpuserial = uuid.UUID(int=uuid.getnode())
        else:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial = line[10:26]
            f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

def generate_key():
    """Hash a password for storing."""
    password = str(get_id())
    
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    f = open("data/key", "w")
    f.write((salt + pwdhash).decode('ascii'))
    f.close()

    return (salt + pwdhash).decode('ascii')


if __name__ == '__main__':
    generate_key()
    if REMOVE:
        os.remove('first_run.py')