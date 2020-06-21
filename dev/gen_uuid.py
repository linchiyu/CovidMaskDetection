import uuid
import hashlib, binascii, os

def generate_key():
	"""Hash a password for storing."""
	password = str(uuid.UUID(int=uuid.getnode()))
	
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
	provided_password = str(uuid.UUID(int=uuid.getnode()))
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