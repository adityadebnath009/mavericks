class DataUnavailableError(Exception):
    """Raised when required environmental or geofencing data is completely unavailable."""
    pass

class NoSafeRouteError(Exception):
    """Raised when no safe route can be physically found."""
    pass
