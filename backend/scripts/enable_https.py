
import paramiko

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"

# Minimal self-signed cert generation script with SAN (Subject Alternative Name)
# Note: Docker/Go requires SANs, CN is deprecated.
GEN_CERT_CMD = """
mkdir -p /data/harbor/common/config/nginx/cert
# Force remove old certs to ensure regeneration
rm -f /data/harbor/common/config/nginx/cert/server.crt
rm -f /data/harbor/common/config/nginx/cert/server.key

echo "Generating self-signed certificate with SAN..."
# Create a temporary config file for OpenSSL
cat > /tmp/openssl.cnf <<EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C = CN
ST = State
L = City
O = Harbor
CN = 10.20.1.204

[v3_req]
subjectAltName = @alt_names

[alt_names]
IP.1 = 10.20.1.204
DNS.1 = 10.20.1.204
EOF

openssl req -newkey rsa:4096 -nodes -sha256 -keyout /data/harbor/common/config/nginx/cert/server.key -x509 -days 365 -out /data/harbor/common/config/nginx/cert/server.crt -config /tmp/openssl.cnf -extensions v3_req

chmod 644 /data/harbor/common/config/nginx/cert/server.crt
chmod 644 /data/harbor/common/config/nginx/cert/server.key
rm -f /tmp/openssl.cnf
"""

NGINX_CONF_HTTPS = r"""worker_processes auto;
pid /tmp/nginx.pid;
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}
http {
    tcp_nodelay on;
    client_body_temp_path /tmp/client_body_temp;
    proxy_temp_path       /tmp/proxy_temp;
    fastcgi_temp_path     /tmp/fastcgi_temp;
    uwsgi_temp_path       /tmp/uwsgi_temp;
    scgi_temp_path        /tmp/scgi_temp;
    client_max_body_size 0;

    types {
        text/html                             html htm shtml;
        text/css                              css;
        text/xml                              xml;
        image/gif                             gif;
        image/jpeg                            jpeg jpg;
        application/javascript                js;
        application/atom+xml                  atom;
        application/rss+xml                   rss;
        text/mathml                           mml;
        text/plain                            txt;
        text/vnd.sun.j2me.app-descriptor      jad;
        text/vnd.wap.wml                      wml;
        text/x-component                      htc;
        image/png                             png;
        image/tiff                            tif tiff;
        image/vnd.wap.wbmp                    wbmp;
        image/x-icon                          ico;
        image/x-jng                           jng;
        image/x-ms-bmp                        bmp;
        image/svg+xml                         svg svgz;
        image/webp                            webp;
        application/font-woff                 woff;
        application/java-archive              jar war ear;
        application/json                      json;
        application/mac-binhex40              hqx;
        application/msword                    doc;
        application/pdf                       pdf;
        application/postscript                ps eps ai;
        application/rtf                       rtf;
        application/vnd.apple.mpegurl         m3u8;
        application/vnd.ms-excel              xls;
        application/vnd.ms-powerpoint         ppt;
        application/vnd.wap.wmlc              wmlc;
        application/vnd.google-earth.kml+xml  kml;
        application/vnd.google-earth.kmz      kmz;
        application/x-7z-compressed           7z;
        application/x-cocoa                   cco;
        application/x-java-archive-diff       jardiff;
        application/x-java-jnlp-file          jnlp;
        application/x-makeself                run;
        application/x-perl                    pl pm;
        application/x-pilot                   prc pdb;
        application/x-rar-compressed          rar;
        application/x-redhat-package-manager  rpm;
        application/x-sea                     sea;
        application/x-shockwave-flash         swf;
        application/x-stuffit                 sit;
        application/x-tcl                     tcl tk;
        application/x-x509-ca-cert            der pem crt;
        application/x-xpinstall               xpi;
        application/xhtml+xml                 xhtml;
        application/xspf                      xspf;
        application/zip                       zip;
        application/octet-stream              bin exe dll;
        application/octet-stream              deb;
        application/octet-stream              dmg;
        application/octet-stream              iso img;
        application/octet-stream              msi msp msm;
        application/vnd.openxmlformats-officedocument.wordprocessingml.document    docx;
        application/vnd.openxmlformats-officedocument.spreadsheetml.sheet          xlsx;
        application/vnd.openxmlformats-officedocument.presentationml.presentation  pptx;
        audio/midi                            mid midi kar;
        audio/mpeg                            mp3;
        audio/ogg                             ogg;
        audio/x-m4a                           m4a;
        audio/x-realaudio                     ra;
        video/3gpp                            3gpp 3gp;
        video/mp2t                            ts;
        video/mp4                             mp4;
        video/mpeg                            mpeg mpg;
        video/quicktime                       mov;
        video/webm                            webm;
        video/x-flv                           flv;
        video/x-m4v                           m4v;
        video/x-mng                           mng;
        video/x-ms-asf                        asx asf;
        video/x-ms-wmv                        wmv;
        video/x-msvideo                       avi;
    }
    default_type application/octet-stream;

    server {
        listen 8080;
        server_tokens off;

        # Do not force redirect to HTTPS
        # location / {
        #    return 301 https://$host$request_uri;
        # }

        location / {
            proxy_pass http://portal:80/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /api/ {
            proxy_pass http://core:8080/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /c/ {
            proxy_pass http://core:8080/c/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /service/ {
            proxy_pass http://core:8080/service/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /v2/ {
            proxy_pass http://core:8080/v2/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }
        
        location /chartrepo/ {
            proxy_pass http://core:8080/chartrepo/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }
    }

    server {
        listen 8443 ssl;
        server_tokens off;

        ssl_certificate /etc/nginx/cert/server.crt;
        ssl_certificate_key /etc/nginx/cert/server.key;
        ssl_protocols TLSv1.2 TLSv1.3;

        location / {
            proxy_pass http://portal:80/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /api/ {
            proxy_pass http://core:8080/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /c/ {
            proxy_pass http://core:8080/c/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /service/ {
            proxy_pass http://core:8080/service/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /v2/ {
            proxy_pass http://core:8080/v2/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }
        
        location /chartrepo/ {
            proxy_pass http://core:8080/chartrepo/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_request_buffering off;
        }
    }
}
"""

def main():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, username=USER, password=PASS)
        
        print("Generating certificates with SAN...")
        # Use a simpler command to write the script to a file and execute it, avoiding quoting hell
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/gen_cert.sh", "w") as f:
            f.write(GEN_CERT_CMD)
        sftp.close()
        
        cmd = f"echo '{PASS}' | sudo -S bash /tmp/gen_cert.sh"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("Writing nginx.conf with SSL...")
        sftp = ssh.open_sftp()
        with sftp.file("/tmp/nginx.conf", "w") as f:
            f.write(NGINX_CONF_HTTPS)
        sftp.close()
        
        cmd = f"echo '{PASS}' | sudo -S mv /tmp/nginx.conf /data/harbor/common/config/nginx/nginx.conf"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        print("Restarting nginx container...")
        cmd = f"echo '{PASS}' | sudo -S docker restart nginx"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("HTTPS enabled on port 8443 (mapped to host 443).")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
