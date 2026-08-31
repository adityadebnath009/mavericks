    def resolve_vector_grid(cls, day: int = 1, hour: int = 12) -> dict:
        """Return the wind/current vector field for the exact requested 3-hour forecast step."""
        valid_hours = {0, 3, 6, 9, 12, 15, 18, 21}
        if day not in {1, 2, 3}:
            raise ValueError("day must be 1, 2, or 3")
        if hour not in valid_hours:
            raise ValueError("hour must be one of 0, 3, 6, 9, 12, 15, 18, or 21")

        grid_cache = os.path.join(cls.CACHE_DIR, f"vector_grid_d{day}_h{hour}.json")
        if os.path.exists(grid_cache) and time.time() - os.path.getmtime(grid_cache) < 6 * 3600:
            import json
            with open(grid_cache, "r", encoding="utf-8") as f:
                return json.load(f)

        try:
            import json
            ds_ww3 = cls._get_dataset(cls.get_ww3_url())
            ds_curr = cls._get_dataset(cls.get_currents_url())

            # WW3 is published on the 3-hour forecast cadence used by the UI.
            # Resolve the dataset's actual timestamp first, then select by timestamp.
            target_index = (day - 1) * 8 + (hour // 3)
            if target_index >= len(ds_ww3.TIME):
                raise IndexError(f"Requested forecast step is outside WW3 TIME dimension: day={day}, hour={hour}")

            target_timestamp = ds_ww3.TIME.values[target_index]
            target_timestamp = pd.to_datetime(target_timestamp)

            ww3_slice = (
                ds_ww3
                .sel(lat=slice(5, 25), lon=slice(65, 95))
                .sel(TIME=target_timestamp, method="nearest")
                .coarsen(lat=2, lon=2, boundary="trim")
                .mean()
            )

            curr_slice = (
                ds_curr
                .sel(LAT=slice(5, 25), LON=slice(65, 95), DEPTH1_1=0.0)
                .sel(TAXIS=target_timestamp, method="nearest")
                .coarsen(LAT=2, LON=2, boundary="trim")
                .mean()
            )

            wind_vectors = []
            lon_grid, lat_grid = np.meshgrid(ww3_slice.lon.values, ww3_slice.lat.values)
            for lat_val, lon_val, u, v in zip(
                lat_grid.ravel(), lon_grid.ravel(),
                ww3_slice.UWND.values.ravel(), ww3_slice.VWND.values.ravel()
            ):
                if np.isnan(u) or np.isnan(v):
                    continue
                speed = math.sqrt(u ** 2 + v ** 2) * 3.6
                direction = (math.degrees(math.atan2(u, v)) + 180) % 360
                wind_vectors.append({
                    "lat": round(float(lat_val), 2),
                    "lon": round(float(lon_val), 2),
                    "u": round(float(u), 2),
                    "v": round(float(v), 2),
                    "speed_kmh": round(speed, 1),
                    "direction_deg": round(direction, 1),
                })

            current_vectors = []
            lon_grid_c, lat_grid_c = np.meshgrid(curr_slice.LON.values, curr_slice.LAT.values)
            for lat_val, lon_val, u, v in zip(
                lat_grid_c.ravel(), lon_grid_c.ravel(),
                curr_slice.U.values.ravel(), curr_slice.V.values.ravel()
            ):
                if np.isnan(u) or np.isnan(v):
                    continue
                speed = math.sqrt(u ** 2 + v ** 2)
                direction = math.degrees(math.atan2(u, v)) % 360
                current_vectors.append({
                    "lat": round(float(lat_val), 2),
                    "lon": round(float(lon_val), 2),
                    "u": round(float(u), 3),
                    "v": round(float(v), 3),
                    "speed_ms": round(speed, 2),
                    "direction_deg": round(direction, 1),
                })

            grid_data = {
                "wind": wind_vectors,
                "current": current_vectors,
                "timestamp": target_timestamp.isoformat(),
                "day": day,
                "hour": hour,
                "source": "INCOIS WW3 + Currents",
            }

            os.makedirs(os.path.dirname(grid_cache), exist_ok=True)
            with open(grid_cache, "w", encoding="utf-8") as f:
                json.dump(grid_data, f)
            return grid_data
        except Exception:
            import logging
            logging.exception("Failed to generate vector grid")
            raise
