import argparse
from ast import Global
import os
import queue
import dotenv
import sounddevice as sd
import vosk
import sys
import json
import time
import pyttsx3
from dotenv import load_dotenv  # загрузка информации из .env-файла
from pyowm import OWM  # использование OpenWeatherMap для получения данных о погоде
from termcolor import colored  # вывод цветных логов (для выделения распознанной речи)

tts = pyttsx3.init()

model = vosk.Model(
    "C:\\PycharmProjects\\Speech2Text\\vosk-model-small-ru-0.22")


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def get_weather_info():
    weather_api_key = os.getenv("WEATHER_API_KEY")
    open_weather_map = OWM(weather_api_key)

    # запрос данных о текущем состоянии погоды
    weather_manager = open_weather_map.weather_manager()
    observation = weather_manager.weather_at_place("Moscow")
    weather = observation.weather

    # разбивание данных на части для удобства работы с ними
    status = weather.detailed_status
    temperature = weather.temperature('celsius')["temp"]
    wind_speed = weather.wind()["speed"]
    pressure = int(weather.pressure["press"] / 1.333)  # переведено из гПА в мм рт.ст.

    # вывод логов
    print(colored("Weather in Moscow" +
                  ":\n * Status: " + status +
                  "\n * Wind speed (m/sec): " + str(wind_speed) +
                  "\n * Temperature (Celsius): " + str(temperature) +
                  "\n * Pressure (mm Hg): " + str(pressure), "yellow"))

    speak("Температура воздуха в Москве " + str(round(temperature)) + " градусов Цельсия")
    speak("Скорость ветра " + str(round(wind_speed)) + " метров в секунду")
    speak("Давление " + str(pressure) + " миллиметра ртутного столба")


def speak(text):
    tts.say(text)
    tts.runAndWait()


def listen():
    try:
        is_working_mode = False

        global q
        q = queue.Queue()
        with sd.RawInputStream(samplerate=44100, blocksize=8000, device=None, dtype='int16', channels=1, callback=callback):
            print('#' * 10, 'Switching to listen mode. Press Ctrl+C to exit', '#' * 10)

            recognizer = vosk.KaldiRecognizer(model, 44100)
            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    json_result = recognizer.Result()
                    text = json.loads(json_result)["text"]
                    if text:
                        print(text)
                        return text

    except Exception as e:
        print(e)
        exit("Fatal error" + ": " + str(e))


if __name__ == '__main__':
    rate = tts.getProperty('rate')  # Скорость произношения
    tts.setProperty('rate', rate-40)

    volume = tts.getProperty('volume')  # Громкость голоса
    tts.setProperty('volume', volume+0.9)

    voices = tts.getProperty('voices')

# Задать голос по умолчанию
tts.setProperty('voice', 'ru')

load_dotenv()

while True:
    text = listen()
    if "погод" in text:
        get_weather_info()
    else:    
        speak(text)