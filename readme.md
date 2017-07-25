# A-MQ 6.3, STOMP and OCP

## Prerequisites

* A-MQ 6.3
* stomp.py version 4.1.18 or greater

## Configure the broker

### Generate the SSL keys and keystores

* Generate the certificate and add to the broker keystore
```
$ keytool -genkey -alias broker -keyalg RSA -keystore broker.ks
```

* Export the certificate for later addition to the client truststore
```
$ keytool -export -alias broker -keystore broker.ks -file broker_cert
```
* Generate the client truststore
```
$ keytool -genkey -alias client -keyalg RSA -keystore client.ks
```
* Import the broker certificate into the client truststore
```
$ keytool -import -alias broker -keystore client.ts -file broker_cert
```
* Export the certificate in DER format
```
$ keytool -export -alias broker -file broker.der -keystore broker.ks
```
* Reformat the certificate into PEM format
```
$ openssl x509 -inform DER -in broker.der -out certificate.pem
```
* Extract the key and convert it into P12 format
```
$ keytool -importkeystore -srckeystore broker.ks  -destkeystore keystore.p12 -deststoretype PKCS12
openssl pkcs12 -in keystore.p12  -nodes -nocerts -out broker.key
```

* Create OCP secret

```
$ oc secrets new broker-secret broker.ks client.ts
```


### Broker Configuration for non-OSE based brokers
```

<sslContext>
    <sslContext
        keyStore="broker.ks"
        keyStorePassword="changeit"
        trustStore="client.ts"
        trustStorePassword="changeit"
        />
</sslContext>

<transportConnectors>
...
    <transportConnector name="stomp" uri="stomp://0.0.0.0:61613?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
    <transportConnector name="stompssl" uri="stomp+ssl://0.0.0.0:61615?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
...
</transportConnectors>
```

## Python client example using stomp.py

```
import time
import sys

import stomp

class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error "%s"' % message)
    def on_message(self, headers, message):
        print('received a message "%s"' % message)
    def on_connected(self,headers,body):
        print('Connected to broker')

conn = stomp.Connection12([('broker-amq-stomp-ssl-amq-stomp.cloudapps.nocosetest.com', 443)])
ssl_result = conn.set_ssl([('broker-amq-stomp-ssl-amq-stomp.cloudapps.nocosetest.com',443)],
    key_file="broker.key",
    cert_file="certificate.pem")
conn.set_listener('', MyListener())
conn.start()
conn.connect('admin', 'admin', wait=True)
conn.subscribe(destination='/queue/noctestQ', id=1, ack='auto')

conn.send(body=' '.join(sys.argv[1:]), destination='/queue/noctestQ')

time.sleep(2)
conn.disconnect()
```

### Openshift resources

```
$ oc create serviceaccount amq-sa
serviceaccount "amq-sa" created

$ oc policy add-role-to-user view system:serviceaccount:amq-stomp:amq-sa
role "view" added: "system:serviceaccount:amq-stomp:amq-sa"

$ oc secrets new broker-secret broker.ks client.ts
secret/broker-secret
$ oc secrets add sa/amq-sa secret/broker-secret
```

### Creating the broker (non-persistent)
```
oc process -n openshift amq63-ssl \
-p MQ_USERNAME=admin \
-p MQ_PASSWORD=admin \
-p MQ_PROTOCOL=stomp,amqp \
-p MQ_QUEUES=noctestQ \
-p MQ_TOPICS=noctestT \
-p AMQ_SECRET=broker-secret \
-p AMQ_TRUSTSTORE=client.ts \
-p AMQ_KEYSTORE=broker.ks \
-p AMQ_TRUSTSTORE_PASSWORD=changeit \
-p AMQ_KEYSTORE_PASSWORD=changeit
```
