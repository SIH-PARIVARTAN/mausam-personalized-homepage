import traceback
from engine.tests.test_traveler_persona import (
    test_traveler_destination_alert_urgency,
    test_local_p0_overrides_destination_alert,
    test_destination_alert_graceful_missing,
)

tasks = [
    ("test_traveler_destination_alert_urgency", test_traveler_destination_alert_urgency),
    ("test_local_p0_overrides_destination_alert", test_local_p0_overrides_destination_alert),
    ("test_destination_alert_graceful_missing", test_destination_alert_graceful_missing),
]

for name, task in tasks:
    try:
        task()
        print(f"{name} PASSED")
    except Exception as e:
        print(f"{name} FAILED: {str(e)}")
        traceback.print_exc()
