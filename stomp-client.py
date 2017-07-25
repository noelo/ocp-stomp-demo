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
