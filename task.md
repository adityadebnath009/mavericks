# Task List: BSI Engine & Safety Integration

- [x] **Step 1: Create BSI Calculator Service**
  - Create the file `backend/app/api/services/bsi_calculator.py` implementing steepness, crossing sea, and rapid wind-sea development indexes.
- [x] **Step 2: Create Unit Test Suite**
  - Create the test file `backend/tests/test_bsi_calculator.py` verifying all 8 BSI states (0 to 7) using parameterized test cases.
- [x] **Step 3: Verify BSI Logic via Pytest**
  - Run the test suite in the terminal to confirm the mathematical accuracy of the indices and their bitwise summation.
- [x] **Step 4: Integrate BSI into Safety Endpoint**
  - Update `backend/app/api/endpoints/safety.py` to calculate BSI dynamically based on forecast timelines.
- [x] **Step 5: Implement Vessel-Specific Beam Safety Checks**
  - Integrate the `beam < 4 * Hs` critical beam calculation to alert small boats.
- [x] **Step 6: Build UI Map & Popups**
  - Implement visual buffer zones and popup cards displaying localized BSI and distance warnings on the MapLibre GL frontend.
