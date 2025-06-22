import json

# Reset the settings file with an empty history
with open('train_settings.json', 'w') as f:
    json.dump({'history': []}, f, indent=4)

print("Settings have been reset. train_settings.json now contains an empty history.")
