# Non-local imports
import pysftp

# Local imports
import _keys

# Define the pysftp connection
pysftp_connection = pysftp.Connection(
    host = _keys.sftp_host,
    username = _keys.sftp_username,
    password = _keys.sftp_password
)


def upload_performance():
    """
    Puts the performance CSV, from the local Data/ folder, where indicated
    in the _keys.py module in the SFTP section. 
    """
    with pysftp_connection as sftp:
        with sftp.cd(_keys.sftp_remote_dir):
            sftp.put('Data/performance.csv')
