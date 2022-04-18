# Non-local imports
import pysftp

# Project modules 
import _keys


# Define the pysftp connection
try:
    pysftp_connection = pysftp.Connection(
        host = _keys.sftp_host,
        username = _keys.sftp_username,
        password = _keys.sftp_password
    )
except AttributeError:  # if credentials weren't given in _keys.py
    pysft_connection = None


def upload_performance(print_success: bool = True):
    """
    Puts the performance CSV, from the local Data/ folder, where indicated
    in the _keys.py module in the SFTP section. 

    If deployment is successful, the function returns True. If not, it 
    returns False.
    """
    # If credentials were not given in _keys.py
    if pysftp_connection is None:
        return False
        
    try:
        with pysftp_connection as sftp:
            with sftp.cd(_keys.sftp_remote_dir):
                sftp.put('Data/performance.csv')
        if print_success:
            print('SFTP was successful.')
        return True
    except:
        if print_success:
            print('SFTP failed.')
        return False
