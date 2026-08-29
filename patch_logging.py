import re
with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

old_except = """        except Exception as e:
            import logging
            logging.error(f"Failed to generate vector grid: {e}")
            return {"wind": [], "current": [], "error": str(e)}"""

new_except = """        except Exception:
            import logging
            logging.exception("Failed to generate vector grid")
            raise"""

content = content.replace(old_except, new_except)

# Also let's log the exception in the get_ww3_url and get_currents_url so we can see WHY pydap failed
old_url_ww3 = """            try:
                ds = xr.open_dataset(base_url, engine="pydap")
                ds.close()
                return base_url
            except Exception:
                continue"""
new_url_ww3 = """            try:
                # Suppress the PyDAP warning for cleaner logs
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ds = xr.open_dataset(base_url.replace('https://', 'http://'), engine="pydap")
                    ds.close()
                return base_url
            except Exception as e:
                import logging
                logging.error(f"WW3 URL test failed for {base_url}: {e}")
                continue"""
content = content.replace(old_url_ww3, new_url_ww3)

old_url_curr = """            try:
                ds = xr.open_dataset(base_url, engine="pydap")
                ds.close()
                return base_url
            except Exception:
                continue"""
new_url_curr = """            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ds = xr.open_dataset(base_url.replace('https://', 'http://'), engine="pydap")
                    ds.close()
                return base_url
            except Exception as e:
                import logging
                logging.error(f"Currents URL test failed for {base_url}: {e}")
                continue"""
content = content.replace(old_url_curr, new_url_curr)

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
