import uuid
import hashlib, binascii, os

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
	f = open("key", "w")
	f.write((salt + pwdhash).decode('ascii'))
	f.close()

	return (salt + pwdhash).decode('ascii')

def verify_key():
	"""Verify a stored password against one provided by user"""
	provided_password = str(get_id())
	f = open("data/key", "r")
	stored_password = f.read()
	f.close()
	salt = stored_password[:64]
	stored_password = stored_password[64:]
	pwdhash = hashlib.pbkdf2_hmac('sha512', 
								  provided_password.encode('utf-8'), 
								  salt.encode('ascii'), 
								  100000)
	pwdhash = binascii.hexlify(pwdhash).decode('ascii')
	return pwdhash == stored_password

if __name__ == '__main__':
	generate_key()