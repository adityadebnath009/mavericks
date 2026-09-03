with open("backend/app/api/services/cache_warmer.py", "r") as f:
    content = f.read()

find = '''            res = PFZEnricherService.enrich_feature_collection(pfz_features, cycle=current_cycle)
            if res.get("enrichment_status") == "PARTIAL_RAW_FALLBACK":
                raise Exception("PFZ telemetry enrichment timed out or failed; raw geometry preserved.")
        except Exception as e:
            logger.error(f"Warming PFZ set failed: {e}")
            all_success = False'''

replace = '''            res = PFZEnricherService.enrich_feature_collection(pfz_features, cycle=current_cycle, shutdown_event=self.shutdown_event)
            if res.get("enrichment_status") == "PARTIAL_RAW_FALLBACK":
                raise Exception("PFZ telemetry enrichment timed out or failed; raw geometry preserved.")
        except InterruptedError:
            logger.info("PFZ enrichment aborted due to shutdown signal.")
            return False
        except Exception as e:
            logger.error(f"Warming PFZ set failed: {e}")
            all_success = False

        if self.shutdown_event.is_set():
            return False'''

content = content.replace(find, replace)

with open("backend/app/api/services/cache_warmer.py", "w") as f:
    f.write(content)
