import paramiko
import sys

HOST = "10.20.1.204"
USER = "ubuntu"
PASS = "cepiec1qaz@WSXaczt8912059Nxtektppyoud"
CONFIG_PATH = "/data/harbor/common/config/registry/config.yml"

TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJoYXJib3ItdG9rZW4taXNzdWVyIiwic3ViIjoiaGFyYm9yLXJlZ2lzdHJ5IiwiYXVkIjoiaGFyYm9yLWNvcmUiLCJleHAiOjIwODc3ODIyMzUsIm5iZiI6MTc3MjQyMjE3NSwiaWF0IjoxNzcyNDIyMjM1fQ.iCFdh0sOcXYtbvPXn5_52j0q4CVVFyO-zMnuElcgrW-6w4zd3VNOeUO7lS7ypbnQjJY2zncwMNVZE5dHpfhss22hDdF20J3RmJf7ORMMle_c3GwRMjMofXfyjxfj6_onUc8E8nY7BALxdgEBSpjMnXMnJh-wtVA52OdvPYTYFQiIpOJIyIGWhs31kY8gwlRQL5Ynx2ng99rV018thSuU3QyXgLFZ44TkCUdGtcZWVvfsC2rSwhjZf8flFi51pgm-DrNla5kid3pg1Hl1i0d_r-z6lE-mhaEBV36WpgO4K1LVCLubeLe4bWuF6PD57U-7XVAxWFLR1gZSUZieGP63G4Y4IAlc8xL2F2vbHLr_wR_Apzf8YUnAxcOmfCNm3Ft_55ixT3iUmXBGCHbvdJYGjFCXqP4_Ix0-jYMRkD9IGOtygBw1lcWrFD5-9fgI3TYFTpr-DzJV8LS_JL9EObFbMUpcIbu4XQp4l2wadzRoVRZskU08k5Z-qS6eZQQtXz7wjfsC8Bq0ntvv6AI6Zo90Oy1CvGcofZQSm47t3usbHZwO2UI1mVSJwsF3eEcqlvNNFmd9TTYzBnfGGG4sxpAQW4wJh3L1ub-NYBuNbOm35Cqoscrr_1X0gsN5fchR7c7NlsbLd4g9NDM4_lA2FoX5TbHXXBsPgSYNM1Yg2KP1R5I"

NOTIFICATION_CONFIG = f"""
notifications:
  endpoints:
    - name: harbor
      disabled: false
      url: http://core:8080/service/notifications
      headers:
        Authorization: Bearer {TOKEN}
      timeout: 3000ms
      threshold: 5
      backoff: 1s
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASS)
        
        # Read existing config
        print(f"Reading {CONFIG_PATH}...")
        cmd = f"cat {CONFIG_PATH}"
        stdin, stdout, stderr = client.exec_command(cmd)
        content = stdout.read().decode()
        
        if "notifications:" in content:
            print("Warning: 'notifications' section already exists. Skipping append.")
            # We might want to replace it, but for now let's assume if it's there, it might be broken or I should overwrite.
            # Given previous checks showed it missing, this branch shouldn't hit.
        else:
            print("Appending notifications config...")
            new_content = content + NOTIFICATION_CONFIG
            
            # Write to temp file
            temp_path = "/tmp/registry_config.yml"
            sftp = client.open_sftp()
            with sftp.file(temp_path, 'w') as f:
                f.write(new_content)
            
            # Move and set permissions
            cmd = f"echo '{PASS}' | sudo -S mv {temp_path} {CONFIG_PATH}"
            client.exec_command(cmd)
            
            print("Restarting Registry...")
            cmd = f"echo '{PASS}' | sudo -S docker restart registry"
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            
            print("Done. Registry updated.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
