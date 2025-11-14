#!/bin/bash
# Script para instalar Playwright en Streamlit Cloud

echo "Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium
echo "Playwright installation complete!"
