#!/bin/bash

# THIS SCRIPT IS FOR ILLUSTRATIVE PURPOSES.
# You would run these openssl commands in your local dev environment
# to generate the necessary certificates and keys for the prototype.

echo "--- Generating CA ---"
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=MyTestCA"

echo "--- Generating Server Certificate ---"
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt

echo "--- Generating Client Certificate ---"
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=TestClient"
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt

echo "--- Cleaning up CSRs and CA serial ---"
rm *.csr
rm *.srl

echo "Place ca.crt, server.crt, server.key, client.crt, client.key in the security_system/auth/certs/ directory for the prototype."
mkdir -p certs
# You would manually move the generated files:
# mv ca.crt server.crt server.key client.crt client.key certs/
