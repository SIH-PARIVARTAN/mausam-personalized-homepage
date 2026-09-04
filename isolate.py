try:
    from engine.tests.test_traveler_persona import test_traveler_destination_alert_urgency
    test_traveler_destination_alert_urgency()
except Exception as e:
    import traceback
    traceback.print_exc()
