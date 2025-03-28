from flask import Flask, render_template
import asyncio
import aiohttp
import nest_asyncio  # Needed if you're running Flask + asyncio together (especially in Jupyter, etc.)
from riot_api import get_death_stats

# Patch event loop issues if needed
nest_asyncio.apply()

app = Flask(__name__)

SUMMONERS = [
    ("Marenios", "NA1"),
    ("7pH", "NA1"),
    ("kidmop", "NA1"),
    ("Moonr0k", "42069"),
    ("BaccaFlokka", "0001")
]

@app.route('/')
def index():
    try:
        stats_list, top_feeder_name = asyncio.run(gather_stats())
        return render_template('index.html', stats_list=stats_list, top_feeder=top_feeder_name)
    except Exception as e:
        print("❌ Error in index route:", e)
        return "Internal Server Error", 500

async def gather_stats():
    async with aiohttp.ClientSession() as session:
        stats_list = await asyncio.gather(*(get_death_stats(session, *s) for s in SUMMONERS))

        # Filter out any errored players first
        valid_stats = [s for s in stats_list if 'error' not in s]

        # Sort by deaths, descending
        sorted_stats = sorted(valid_stats, key=lambda x: x['deaths'], reverse=True)

        # Add back any errored stats at the bottom (optional)
        errored_stats = [s for s in stats_list if 'error' in s]
        stats_list = sorted_stats + errored_stats

        # Pick the top feeder
        top_feeder_name = sorted_stats[0]['summoner'] if sorted_stats else None

    return stats_list, top_feeder_name

if __name__ == '__main__':
    app.run(debug=True, port=5050)
