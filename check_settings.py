from app import create_app

app = create_app()

with app.app_context():
    from app.models.registry import get_models
    models = get_models()
    SystemSetting = models['SystemSetting']

    settings = SystemSetting.query.filter(SystemSetting.setting_key.like('core_%_start_time')).all()
    print("Core timeslot settings in database:")
    for s in settings:
        print(f"{s.setting_key}: {s.setting_value}")

    if not settings:
        print("No core timeslot settings found in database - using defaults")
