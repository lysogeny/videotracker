"""Various helper functions"""
def disconnect(signal):
    """Disconnects the signal, catching any TypeError"""
    try:
        signal.disconnect()
    except TypeError:
        pass
