#!/usr/bin/env python3
"""
Enhanced YouTube Playlist Monitor

Monitors playlist playback, matches next song against dispatched_songs.json,
displays responsible team name, and tracks songs as played.

Author: Updated Version
"""

import asyncio
import os
import platform
import json
import aiofiles
from typing import Optional, Dict
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import requests
import os
import yaml
from utils.error_reporter import report_error
import re
from urllib.parse import urlparse, parse_qs, urlencode


def normalize_youtube_link(link):
    """
    Normalize YouTube video links to the standard desktop format.
    Preserves important parameters like list (playlist) and t (timestamp).
    """
    # Parse URL
    parsed = urlparse(link)
    
    query = parse_qs(parsed.query)
    video_id = None
    params = {}
    
    # Detect video ID
    if 'v' in query:
        video_id = query['v'][0]
    elif parsed.netloc in ['youtu.be']:
        video_id = parsed.path.lstrip('/')
    elif 'watch' in parsed.path:
        # Fallback for watch URLs without v param
        video_id_match = re.search(r'v=([^&]+)', parsed.query)
        if video_id_match:
            video_id = video_id_match.group(1)

    if not video_id:
        raise ValueError(f"Could not extract video ID from link: {link}")

    # Now preserve extra params like playlist ID and timestamp
    for key in ['list', 't', 'index']:
        if key in query:
            params[key] = query[key][0]

    # Build final URL
    base_url = f"https://www.youtube.com/watch?v={video_id}"
    if params:
        base_url += '&' + urlencode(params)

    return base_url


PLAYED_SONGS_FILE ="played_song.json"

def get_current_songs():
    """Fetches the current songs from the configured FastAPI server."""
    config_path = "configs/config.yaml"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        report_error(e, context="Please, remember to fill your configs/config.yaml file. Template is at config.yaml.template")
        raise e  # Stop execution if config cannot be loaded

    try:
        url = config["kai_api"]["song_endpoint"]
    except KeyError as e:
        report_error(e, context="Missing 'kai_api' or 'song_endpoint' in config.yaml")
        raise e

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        report_error(e, context=f"Error connecting to the server at {url}")
        raise e




async def init_browser() -> Chrome:
    chrome_options = Options()
    system_os = platform.system()

    if system_os == "Windows":
        profile = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    elif system_os == "Linux":
        profile = os.path.expanduser("~/.config/google-chrome")
    else:
        raise OSError(f"Unsupported OS: {system_os}")

    chrome_options.add_argument(f"user-data-dir={profile}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver


async def show_popup(driver: Chrome, message: str) -> None:
    script = f"""
    const popup = document.createElement('div');
    popup.style.position='fixed';
    popup.style.top='20px';
    popup.style.left='0';
    popup.style.backgroundColor='rgba(255,255,255,0.9)';
    popup.style.color='black';
    popup.style.padding='12px 24px';
    popup.style.borderRadius='6px';
    popup.style.boxShadow='0 2px 10px rgba(0,0,0,0.3)';
    popup.style.zIndex='99999';
    popup.style.fontWeight='bold';
    popup.innerText=`{message}`;
    popup.style.transition='left 20s linear';
    document.body.appendChild(popup);
    setTimeout(()=>popup.style.left='100%',100);
    setTimeout(()=>popup.remove(),20000);
    """
    driver.execute_script(script)




async def extract_next_video(driver: Chrome) -> Optional[Dict[str, str]]:
    try:
        next_video_element = driver.find_element(
            By.CSS_SELECTOR,
            "ytd-playlist-panel-video-renderer[selected] + ytd-playlist-panel-video-renderer #wc-endpoint"
        )
        link = next_video_element.get_attribute("href")
        title_element = next_video_element.find_element(By.CSS_SELECTOR, "#video-title")
        title = title_element.get_attribute("title").strip() or title_element.text.strip()
        return {"title": title, "link": link}
    except Exception as e:
        print(f"⚠️ Error extracting next video details: {e}")
        return None


async def load_json_async(file_name: str):
    try:
        async with aiofiles.open(file_name, 'r') as f:
            return json.loads(await f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


async def save_json_async(file_name: str, data):
    async with aiofiles.open(file_name, 'w') as f:
        await f.write(json.dumps(data, indent=4))


async def find_team_for_song(next_video_link: str, played_songs):
    dispatched_songs = get_current_songs()
    for song in dispatched_songs:
        print(normalize_youtube_link(song["link"]) , normalize_youtube_link(next_video_link), normalize_youtube_link(song["link"]) == normalize_youtube_link(next_video_link) )
        if normalize_youtube_link(song["link"]) == normalize_youtube_link(next_video_link) and song not in played_songs:
            return song["team"], song
    return None, None


async def on_youtube_playlist_page(driver: Chrome) -> bool:

    try:
        current_url = driver.current_url

        print(current_url)
    except Exception as e:
        print(f"Error getting current_url: {e}")
        return False

    if not current_url:
        return False

    print(current_url)
    return "youtube.com/watch" in current_url and "&list=" in current_url


async def monitor_video(driver: Chrome) -> None:
    notified = False
    while True:
        if not await on_youtube_playlist_page(driver):
            notified = False
            await asyncio.sleep(3)
            continue

        try:
            current_time = driver.execute_script(
                "return document.querySelector('.video-stream').currentTime;"
            )
            duration = driver.execute_script(
                "return document.querySelector('.video-stream').duration;"
            )
            print(current_time,duration )
            if duration - current_time <= 10 and not notified:
                next_video = await extract_next_video(driver)

                if next_video:
                    played_songs = await load_json_async(PLAYED_SONGS_FILE)

                    team, matched_song = await find_team_for_song(next_video['link'],  played_songs)

                    if team:
                        message = f"🎤 Next team is #{team} → singing: {next_video['title']}"
                        played_songs.append(matched_song)
                        await save_json_async(PLAYED_SONGS_FILE, played_songs)
                    else:
                        message = f"🎶 Next song: {next_video['title']} (No team matched)"
                    
                    await show_popup(driver, message)
                    print(f"✅ Next video: {next_video['title']} ({'Team: '+team if team else 'No team'})")

                else:
                    await show_popup(driver, "⚠️ This is the last song in the playlist.")
                    print("ℹ️ No further videos in playlist.")

                notified = True
                await asyncio.sleep(12)

            elif duration - current_time > 10:
                notified = False
                await asyncio.sleep(1)

        except Exception as error:
            print(f"Monitoring error occurred: {error}")
            await asyncio.sleep(3)


async def main() -> None:
    driver = await init_browser()
    print("✅ Browser ready. Idle until playlist detected...")

    try:
        while True:
            if await on_youtube_playlist_page(driver):
                print("▶️ Playlist detected, monitoring begins.")
                await monitor_video(driver)
            await asyncio.sleep(3)

    except KeyboardInterrupt:
        print("🛑 User terminated monitor.")
    finally:
        driver.quit()
        print("🚪 Closed browser cleanly.")


if __name__ == "__main__":
    asyncio.run(main())