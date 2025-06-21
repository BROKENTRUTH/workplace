#!/bin/bash

# THIS SCRIPT IS FOR ILLUSTRATIVE PURPOSES.
# You would run these openssl commands in your local dev environment
# to generate the necessary certificates and keys for the prototype.

# --- CA Configuration (for CRL) ---
# Create a ca.conf file (simplified example):
# [ ca ]
# default_ca = CA_default
# [ CA_default ]
# dir = ./myca              # Where everything is kept
# database = $dir/index.txt # database index file.
# new_certs_dir = $dir/newcerts # default place for new certs.
# certificate = $dir/ca.crt # The CA certificate
# serial = $dir/serial      # The current serial number
# private_key = $dir/ca.key # The private key
# crl = $dir/ca.crl         # The current CRL
# default_days = 365        # how long to certify for
# default_md = sha256       # use SHA-256 by default
# policy = policy_anything
# [ policy_anything ]
# countryName = optional
# stateOrProvinceName = optional
# localityName = optional
# organizationName = optional
# organizationalUnitName = optional
# commonName = supplied
# emailAddress = optional

# Setup CA directory structure (do this once)
# mkdir -p myca/newcerts
# touch myca/index.txt
# echo "01" > myca/serial # Start serial from 01 or a random hex string

echo "--- Generating CA ---"
openssl genrsa -out ca.key 2048
# Add -config ca.conf if using a config file for CA extensions
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=MyTestCA"

echo "--- Generating Server Certificate ---"
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"
# Add -config ca.conf and -extensions server_cert if using specific extensions
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt

echo "--- Generating Client Certificate (client1) ---"
openssl genrsa -out client1.key 2048
openssl req -new -key client1.key -out client1.csr -subj "/CN=TestClient1"
openssl x509 -req -days 365 -in client1.csr -CA ca.crt -CAkey ca.key -CAserial ca.srl -out client1.crt
# (Note: ca.srl is typically managed by 'openssl ca' command or by updating myca/serial)

echo "--- Generating Client Certificate (client2_to_revoke) ---"
openssl genrsa -out client2_to_revoke.key 2048
openssl req -new -key client2_to_revoke.key -out client2_to_revoke.csr -subj "/CN=TestClient2RevokeMe"
openssl x509 -req -days 365 -in client2_to_revoke.csr -CA ca.crt -CAkey ca.key -CAserial ca.srl -out client2_to_revoke.crt

echo "--- Revoking a Certificate (Example: client2_to_revoke.crt) ---"
# This requires the CA setup (index.txt, serial, etc.) and ca.conf
# openssl ca -config ca.conf -revoke myca/newcerts/CLIENT_SERIAL_NUMBER_HEX.pem # Replace with actual serial file
# Or more directly if you have the certificate:
# openssl ca -config path/to/your/openssl.cnf -revoke client2_to_revoke.crt -keyfile ca.key -cert ca.crt
echo " (Example: openssl ca -revoke client2_to_revoke.crt -keyfile ca.key -cert ca.crt -config your_openssl.cnf)"
# This updates the index.txt marking the cert as revoked.

echo "--- Generating CRL ---"
# openssl ca -config path/to/your/openssl.cnf -gencrl -out ca.crl -keyfile ca.key -cert ca.crt
echo " (Example: openssl ca -gencrl -out ca.crl -keyfile ca.key -cert ca.crt -config your_openssl.cnf)"
# The ca.crl file would then be distributed and used by the server.
# To view CRL: openssl crl -in ca.crl -text -noout

echo "--- Cleaning up CSRs (serial file ca.srl is important for CA) ---"
# rm *.csr
# Keep ca.srl if you are using it for -CAserial, or manage serial via index.txt database.

echo "Place ca.crt, server.crt, server.key, client1.crt, client1.key in the security_system/auth/certs/ directory."
echo "If using CRL, also place ca.crl there and ensure server logic can read it."
mkdir -p certs
# Manually move relevant files:
# mv ca.crt server.crt server.key client1.crt client1.key client2_to_revoke.crt client2_to_revoke.key certs/
# If CRL generated: mv ca.crl certs/
