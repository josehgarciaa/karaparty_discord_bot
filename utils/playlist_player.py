from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class YouTubePlaylistMonitor:
    """
    A class to monitor a YouTube playlist and display a custom message
    shortly before each video ends, using a provided queue with song info.
    """

    def __init__(self, playlist_url, queue, profile_path=None):
        """
        Initialize the YouTubePlaylistMonitor.

        Args:
            playlist_url (str): URL of the YouTube playlist.
            queue (list): List of dictionaries with 'title', 'team', and 'link'.
            profile_path (str, optional): Path to the Chrome user profile for session reuse.
        """
        self.playlist_url = playlist_url
        self.queue = queue

        chrome_options = Options()
        if profile_path:
            chrome_options.add_argument(f"user-data-dir={profile_path}")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 20)

    def start_playlist(self):
        """
        Load the playlist URL and start playing the first video.
        """
        self.driver.get(self.playlist_url)
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ytd-playlist-video-renderer'))
        )
        time.sleep(5)

        first_video = self.driver.find_element(By.CSS_SELECTOR, 'ytd-playlist-video-renderer')
        ActionChains(self.driver).move_to_element(first_video).click().perform()

    def show_custom_popup(self, message):
        """
        Show a custom animated popup with the provided message.

        Args:
            message (str): The message to display in the popup.
        """
        script = f"""
            let popup = document.createElement('div');
            popup.id = 'custom-alert';
            popup.style.position = 'fixed';
            popup.style.top = '20px';
            popup.style.left = '0';
            popup.style.backgroundColor = 'rgba(255,255,255,0.9)';
            popup.style.color = 'black';
            popup.style.padding = '12px 24px';
            popup.style.borderRadius = '6px';
            popup.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.3)';
            popup.style.zIndex = '99999';
            popup.style.fontWeight = 'bold';
            popup.innerText = '{message}';
            popup.style.transition = 'left 20s linear';
            document.body.appendChild(popup);

            setTimeout(() => popup.style.left = '100%', 100);
            setTimeout(() => popup.remove(), 20000);
        """
        self.driver.execute_script(script)

    def monitor_playlist(self):
        """
        Continuously monitor the current video and show a custom popup
        shortly before it ends, using the next item from the queue.
        """
        while self.queue:
            time.sleep(2)
            try:
                current_time = self.driver.execute_script(
                    "return document.getElementsByClassName('video-stream')[0].currentTime"
                )
                total_duration = self.driver.execute_script(
                    "return document.getElementsByClassName('video-stream')[0].duration"
                )

                if total_duration - current_time <= 10:
                    next_song = self.queue.pop(0)
                    message = (
                        f"Siguiente_ Equipo {next_song['team']} cantará: {next_song['title']}"
                    )
                    self.show_custom_popup(message)

                    time.sleep(12)

            except Exception as e:
                print("An error occurred:", e)
                break

    def close(self):
        """
        Close the browser session.
        """
        self.driver.quit()


