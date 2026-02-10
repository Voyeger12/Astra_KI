#!/usr/bin/env python3
from modules.ui.settings_manager import SettingsManager
sm = SettingsManager()
print(f'✅ Selected Model: {sm.get("selected_model")}')
