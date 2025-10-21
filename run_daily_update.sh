#!/bin/bash

# Bihar Election Forecast - Daily Update Script
# Run this script daily to update forecasts

echo "🔄 Starting Bihar Election Forecast Daily Update..."
echo "=================================================="

# Run the daily update
python3 main.py update

# Check if successful
if [ $? -eq 0 ]; then
    echo "✅ Daily update completed successfully!"
    echo "📊 Dashboard data has been refreshed"
    echo "🌐 Visit your dashboard to see updated forecasts"
else
    echo "❌ Daily update failed"
    echo "🔧 Check logs for details"
fi

echo "=================================================="
echo "Next update: Tomorrow at the same time"