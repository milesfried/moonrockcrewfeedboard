import aiohttp
import asyncio
import os
from dotenv import load_dotenv
from collections import Counter
import ssl
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())
load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}

async def fetch_json(session, url):
    try:
        async with session.get(url, headers=HEADERS, ssl=ssl_context) as res:
            if res.status == 200:
                return await res.json()
            else:
                print(f"❌ {res.status}: {url}")
                return {}
    except Exception as e:
        print(f"❌ SSL ERROR: {e}")
        return {}


async def get_puuid(session, game_name, tag_line):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    data = await fetch_json(session, url)
    return data.get("puuid")

async def get_match_ids(session, puuid, count=5):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    return await fetch_json(session, url)

async def get_death_stats(session, game_name, tag_line):
    try:
        puuid = await get_puuid(session, game_name, tag_line)
        if not puuid:
            return {"summoner": f"{game_name}#{tag_line}", "error": "Summoner not found"}

        match_ids = await get_match_ids(session, puuid)
        if not match_ids:
            return {"summoner": f"{game_name}#{tag_line}", "error": "No matches"}

        deaths = 0
        champ_counter = Counter()

        async def fetch_match(match_id):
            await asyncio.sleep(0.7)  # 👈 small delay to ease up on the API
            url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
            data = await fetch_json(session, url)
            if 'info' not in data:
                return 0, None
            for p in data['info']['participants']:
                if p['puuid'] == puuid:
                    return p['deaths'], p['championName']
            return 0, None

        results = await asyncio.gather(*(fetch_match(mid) for mid in match_ids))
        for death_count, champ in results:
            deaths += death_count
            if champ:
                champ_counter[champ] += 1

        most_common = champ_counter.most_common(1)
        most_played_champ = most_common[0][0] if most_common else None

        return {
            "summoner": f"{game_name}#{tag_line}",
            "matches": len(match_ids),
            "deaths": deaths,
            "avg_deaths": round(deaths / len(match_ids), 2),
            "champion": most_played_champ
        }

    except Exception as e:
        return {"summoner": f"{game_name}#{tag_line}", "error": str(e)}
