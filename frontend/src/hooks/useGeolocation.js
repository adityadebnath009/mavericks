import { useState, useEffect } from 'react';

/**
 * Custom React hook that accesses the browser's native HTML5 Geolocation API
 * to retrieve and watch the user's active GPS coordinates.
 */
export function useGeolocation(options = {}) {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by this browser.');
      setLoading(false);
      return;
    }

    // Success callback when GPS coordinates are retrieved
    const handleSuccess = (position) => {
      setLocation({
        lat: position.coords.latitude,
        lon: position.coords.longitude,
        accuracy_meters: position.coords.accuracy,
        timestamp: position.timestamp
      });
      setLoading(false);
      setError(null);
    };

    // Error callback when user blocks location access or GPS fails
    const handleError = (err) => {
      setError(err.message);
      setLoading(false);
    };

    // Watch position in real-time to get updates as the vessel moves
    const watchId = navigator.geolocation.watchPosition(
      handleSuccess,
      handleError,
      {
        enableHighAccuracy: true, // Force GPS usage rather than IP location
        timeout: 10000,
        maximumAge: 0,
        ...options
      }
    );

    // Clean up watcher when component unmounts
    return () => navigator.geolocation.clearWatch(watchId);
  }, [options]);

  return { location, error, loading };
}
