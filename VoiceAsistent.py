# -*- coding: utf-8 -*-
from fnmatch import translate
from logging import shutdown
from vosk import Model, KaldiRecognizer  # оффлайн-распознавание от Vosk
from googlesearch import search  # поиск в Google
from pyowm import OWM  # использование OpenWeatherMap для получения данных о погоде
from termcolor import colored  # вывод цветных логов (для выделения распознанной речи)
from dotenv import load_dotenv  # загрузка информации из .env-файла
import speech_recognition  # распознавание пользовательской речи (Speech-To-Text)
import googletrans  # использование системы Google Translate
import pyttsx3  # синтез речи (Text-To-Speech)
import wikipediaapi  # поиск определений в Wikipedia
import random  # генератор случайных чисел
import webbrowser  # работа с использованием браузера по умолчанию (открывание вкладок с web-страницей)
import traceback  # вывод traceback без остановки работы программы при отлове исключений
import json  # работа с json-файлами и json-строками
import wave  # создание и чтение аудиофайлов формата wav
import os  # работа с файловой системой
import requests # работа с ссылками
from bs4 import BeautifulSoup #парсинг с сайта
import pyautogui as ptg






class OwnerPerson:
    """
    Информация о владельце, включающие имя, город проживания, родной язык речи, изучаемый язык (для переводов текста)
    """
    name = ""
    home_city = ""
    native_language = ""
    target_language = ""


class VoiceAssistant:
    """
    Настройки голосового ассистента, включающие имя, пол, язык речи
    Примечание: для мультиязычных голосовых ассистентов лучше создать отдельный класс,
    который будет брать перевод из JSON-файла с нужным языком
    """
    name = ""
    sex = ""
    speech_language = ""
    # recognition_language = ""

class Translation:
    def __init__(self,assistent_info: VoiceAssistant):
        self.assistant = assistent_info
    """
    Получение вшитого в приложение перевода строк для создания мультиязычного ассистента
    """
    with open("translations.json", "r", encoding="UTF-8") as file:
        translations = json.load(file)

    def get(self, text: str):
        """
        Получение перевода строки из файла на нужный язык (по его коду)
        :param text: текст, который требуется перевести
        :return: вшитый в приложение перевод текста
        """
        if text in self.translations:
            return self.translations[text][self.assistant.speech_language]
        else:
            # в случае отсутствия перевода происходит вывод сообщения об этом в логах и возврат исходного текста
            print(colored("Not translated phrase: {}".format(text), "red"))
            return text

class VoiceInit:
    def __init__(self):
        # инициализация инструментов распознавания и ввода речи
        self.recognizer = speech_recognition.Recognizer()
        self.microphone = speech_recognition.Microphone()

        # инициализация инструмента синтеза речи
        self.ttsEngine = pyttsx3.init()

        
        # настройка данных голосового помощника
        self.assistant = VoiceAssistant()
        self.assistant.name = "астра"
        self.assistant.sex = "female"
        self.assistant.speech_language = "ru"

        # добавление возможностей перевода фраз (из заготовленного файла)
        self.translator = Translation(self.assistant)
        # загрузка информации из .env-файла (там лежит API-ключ для OpenWeatherMap)
        load_dotenv()
        
        self.commands = {
            ("help","comands","what can you do","список команд","команды","расскажи мне что ты умеешь","твои возможности"):self.show_help,
            ("hello", "hi", "morning", "привет","доброе утро"): self.play_greetings,
            ("bye", "goodbye", "quit", "exit", "stop", "пока" ,"завершить работу","завершение работы"): self.play_farewell_and_quit,
            ("search", "google", "find", "найди мне"): self.search_for_term_on_google,
            ("video", "youtube", "watch", "видео","найди видео"): self.search_for_video_on_youtube,
            ("wikipedia", "definition", "about", "информация", "википедия"): self.search_for_definition_on_wikipedia,
            ("translate", "interpretation", "translation", "перевод", "перевести", "переведи"): self.get_translation,
            ("change language","language", "изменить язык","измени язык","язык"): self.change_language,
            ("weather", "forecast", "погода", "прогноз"): self.get_weather_forecast,
            ("vkontakte", "self.person", "run", "пробей", "в контакте","вконтакте"): self.run_person_through_social_nets_databases,
            ("toss", "coin", "монета","монетка", "подбрось","монетку"): self.toss_coin,
            ("change my name","change name","измени мое имя","изменить имя","сменить имя","смена имени"): self.change_name,
            ("change my city","change city","измени мой город","изменить местоположение","изменить город","сменить город","смена города"): self.change_city,
            ("change language","language", "изменить родной язык","измени мой родной язык","родной язык"): self.change_language,
            ("turn off computer", "terminate computer", "отключи компьютер" ,"отключить компьютер","выключи компьютер"): self.turn_off_the_computer,
            ("sleep mode", "hibernate computer", "активируй режим сна" ,"спи","режим сна"): self.sleeping_mode,
            ("restart computer", "reboot computer", "рестарт" ,"перезагрузка","инициация перезагрузки","перезагрузи компьютер"): self.restart_the_computer,
        }

         # настройка данных пользователя
        with open("config.txt","r",encoding="utf-8") as fl:
            self.data = fl.readlines()
        self.person = OwnerPerson()
        self.person.name = self.data[1].split("Name: ")[1]
        self.person.native_language = self.data[2].split("Lang: ")[1]
        self.person.target_language = self.data[3].split("L_Lang: ")[1]
        self.person.home_city = self.data[4].split("City: ")[1]

        if int(self.data[0].split("Status: ")[1]) == 0:
            self.execute_command_with_name("привет", "")
            self.execute_command_with_name("команды", "")
       
    
    def rebuild_data(self,old_data,new_data):
        with open("config.txt") as fl:
            fl.write(self.data)

    # Установка голоса асистента
    def setup_assistant_voice(self):
        """
        Установка голоса по умолчанию (индекс может меняться в зависимости от настроек операционной системы)
        """
        voices = self.ttsEngine.getProperty("voices")

        if self.assistant.speech_language == "en":
            self.assistant.recognition_language = "en-US"
            if self.assistant.sex == "female":
                # Microsoft Zira Desktop - English (United States)
                self.ttsEngine.setProperty("voice", voices[1].id)
            else:
                # Microsoft David Desktop - English (United States)
                self.ttsEngine.setProperty("voice", voices[2].id)
        else:
            self.assistant.recognition_language = "ru-RU"
            # Microsoft Irina Desktop - Russian
            self.ttsEngine.setProperty("voice", voices[0].id)

    # Запись и распознование голоса
    def record_and_recognize_audio(self,*args: tuple):
        with self.microphone:
            recognized_data = ""

            # запоминание шумов окружения для последующей очистки звука от них
            self.recognizer.adjust_for_ambient_noise(self.microphone, duration=1)

            try:
                print("Слушаю...")
                audio = self.recognizer.listen(self.microphone, 5, 5)

                with open("microphone-results.wav", "wb") as file:
                    file.write(audio.get_wav_data())

            except speech_recognition.WaitTimeoutError:
                # self.play_voice_assistant_speech(self.translator.get("Can you check if your microphone is on, please?"))
                traceback.print_exc()
                return

            # использование online-распознавания через Google (высокое качество распознавания)
            try:
                # print("Started recognition...")
                recognized_data = self.recognizer.recognize_google(audio, language=self.assistant.recognition_language).lower()

            except speech_recognition.UnknownValueError:
                pass  # self.play_voice_assistant_speech("What did you say again?")

            # в случае проблем с доступом в Интернет происходит попытка использовать offline-распознавание через Vosk
            except speech_recognition.RequestError:
                # print(colored("Trying to use offline recognition...", "cyan"))
                recognized_data = self.use_offline_recognition()

            return recognized_data

    # Функция для офлайн записи
    def use_offline_recognition(self):
        """
        Переключение на оффлайн-распознавание речи
        :return: распознанная фраза
        """
        recognized_data = ""
        try:
            # проверка наличия модели на нужном языке в каталоге приложения
            if not os.path.exists("models/vosk-model-small-" + self.assistant.speech_language + "-0.4"):
                print(colored("Please download the model from:\n"
                            "https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.",
                            "red"))
                exit(1)

            # анализ записанного в микрофон аудио (чтобы избежать повторов фразы)
            wave_audio_file = wave.open("microphone-results.wav", "rb")
            model = Model("models/vosk-model-small-" + self.assistant.speech_language + "-0.4")
            offline_recognizer = KaldiRecognizer(model, wave_audio_file.getframerate())

            data = wave_audio_file.readframes(wave_audio_file.getnframes())
            if len(data) > 0:
                if offline_recognizer.AcceptWaveform(data):
                    recognized_data = offline_recognizer.Result()

                    # получение данных распознанного текста из JSON-строки (чтобы можно было выдать по ней ответ)
                    recognized_data = json.loads(recognized_data)
                    recognized_data = recognized_data["text"]
        except:
            traceback.print_exc()
            print(colored("Sorry, speech service is unavailable. Try again later", "red"))

        return recognized_data

    # Функция для инициации голоса асистента
    def play_voice_assistant_speech(self,text_to_speech):
        """
        Проигрывание речи ответов голосового ассистента (без сохранения аудио)
        :param text_to_speech: текст, который нужно преобразовать в речь
        """
        self.ttsEngine.say(str(text_to_speech))
        self.ttsEngine.runAndWait()

    # Функция приветствия
    def show_help(self,*args: tuple):
        """
        Проигрывание случайной приветственной речи
        """
        translator = self.translator
        text = translator.get("That's my command's,whose can I do for you {}").format(self.person.name)
        self.play_voice_assistant_speech(text)
        os.startfile("help.txt")
    
    # Функция приветствия
    def play_greetings(self,*args: tuple):
        """
        Проигрывание случайной приветственной речи
        """
        translator = self.translator
        greetings = [
            translator.get("Hello, {}! How can I help you today?").format(self.person.name),
            translator.get("Good day to you {}! How can I help you today?").format(self.person.name)
        ]
        self.play_voice_assistant_speech(greetings[random.randint(0, len(greetings) - 1)])

    # Функция завершения работы 
    def play_farewell_and_quit(self,*args: tuple):
        """
        Проигрывание прощательной речи и выход
        """
        farewells = [
            self.translator.get("Goodbye, {}! Have a nice day!").format(self.person.name),
            self.translator.get("See you soon, {}!").format(self.person.name)
        ]
        self.play_voice_assistant_speech(farewells[random.randint(0, len(farewells) - 1)])
        self.ttsEngine.stop()
        quit()

    # Функция поиска в google
    def search_for_term_on_google(self,*args: tuple):
        """
        Поиск в Google с автоматическим открытием ссылок (на список результатов и на сами результаты, если возможно)
        :param args: фраза поискового запроса
        """
        if not args[0]: return
        search_term = " ".join(args[0])

        # открытие ссылки на поисковик в браузере
        url = "https://google.com/search?q=" + search_term
        webbrowser.get().open(url)

        # альтернативный поиск с автоматическим открытием ссылок на результаты (в некоторых случаях может быть небезопасно)
        search_results = []
        try:
            for _ in search(search_term,  # что искать
                            tld="com",  # верхнеуровневый домен
                            lang=self.assistant.speech_language,  # используется язык, на котором говорит ассистент
                            num=1,  # количество результатов на странице
                            start=0,  # индекс первого извлекаемого результата
                            stop=1,  # индекс последнего извлекаемого результата (я хочу, чтобы открывался первый результат)
                            pause=1.0,  # задержка между HTTP-запросами
                            ):
                search_results.append(_)
                webbrowser.get().open(_)

        # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
        except:
            self.play_voice_assistant_speech(self.translator.get("Seems like we have a trouble. See logs for more information"))
            traceback.print_exc()
            return

        print(search_results)
        self.play_voice_assistant_speech(self.translator.get("Here is what I found for {} on google").format(search_term))

    # Найти видео на ютубе
    def search_for_video_on_youtube(self,*args: tuple):
        """
        Поиск видео на YouTube с автоматическим открытием ссылки на список результатов
        :param args: фраза поискового запроса
        """
        if not args[0]: return
        search_term = " ".join(args[0])
        url = "https://www.youtube.com/results?search_query=" + search_term
        webbrowser.get().open(url)
        self.play_voice_assistant_speech(self.translator.get("Here is what I found for {} on youtube").format(search_term))

    # Поиск по википедии
    def search_for_definition_on_wikipedia(self,*args: tuple):
        """
        Поиск в Wikipedia определения с последующим озвучиванием результатов и открытием ссылок
        :param args: фраза поискового запроса
        """
        if not args[0]: return

        search_term = " ".join(args[0])

        # установка языка (в данном случае используется язык, на котором говорит ассистент)
        wiki = wikipediaapi.Wikipedia(self.assistant.speech_language)

        # поиск страницы по запросу, чтение summary, открытие ссылки на страницу для получения подробной информации
        wiki_page = wiki.page(search_term)
        try:
            if wiki_page.exists():
                self.play_voice_assistant_speech(self.translator.get("Here is what I found for {} on Wikipedia").format(search_term))
                webbrowser.get().open(wiki_page.fullurl)

                # чтение ассистентом первых двух предложений summary со страницы Wikipedia
                # (могут быть проблемы с мультиязычностью)
                self.play_voice_assistant_speech(wiki_page.summary.split(".")[:2])
            else:
                # открытие ссылки на поисковик в браузере в случае, если на Wikipedia не удалось найти ничего по запросу
                self.play_voice_assistant_speech(self.translator.get(
                    "Can't find {} on Wikipedia. But here is what I found on google").format(search_term))
                url = "https://google.com/search?q=" + search_term
                webbrowser.get().open(url)

        # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
        except:
            self.play_voice_assistant_speech(self.translator.get("Seems like we have a trouble. See logs for more information"))
            traceback.print_exc()
            return

    # Функция переводчика
    def get_translation(self,*args: tuple):
        """
        Получение перевода текста с одного языка на другой (в данном случае с изучаемого на родной язык или обратно)
        :param args: фраза, которую требуется перевести
        """
        if not args[0]: return

        search_term = " ".join(args[0])
        google_translator = googletrans.Translator()
        translation_result = ""

        old_assistant_language = self.assistant.speech_language
        try:
            # если язык речи ассистента и родной язык пользователя различаются, то перевод выполяется на родной язык
            if self.assistant.speech_language != self.person.native_language:
                translation_result = google_translator.translate(search_term,  # что перевести
                                                        src=self.person.target_language,  # с какого языка
                                                        dest=self.person.native_language)  # на какой язык

                self.play_voice_assistant_speech("The translation for {} in Russian is".format(search_term))

                # смена голоса ассистента на родной язык пользователя (чтобы можно было произнести перевод)
                self.assistant.speech_language = self.person.native_language
                self.setup_assistant_voice()

            # если язык речи ассистента и родной язык пользователя одинаковы, то перевод выполяется на изучаемый язык
            else:
                translation_result = google_translator.translate(search_term,  # что перевести
                                                        src=self.person.native_language,  # с какого языка
                                                        dest=self.person.target_language)  # на какой язык
                self.play_voice_assistant_speech("По-английски {} будет как".format(search_term))

                # смена голоса ассистента на изучаемый язык пользователя (чтобы можно было произнести перевод)
                self.assistant.speech_language = self.person.target_language
                self.setup_assistant_voice()

            # произнесение перевода
            self.play_voice_assistant_speech(translation_result.text)

        # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
        except:
            self.play_voice_assistant_speech(self.translator.get("Seems like we have a trouble. See logs for more information"))
            traceback.print_exc()

        finally:
            # возвращение преждних настроек голоса помощника
            self.assistant.speech_language = old_assistant_language
            self.setup_assistant_voice()

    # Функция для прогноза погоды
    def get_weather_forecast(self,*args: tuple):
        from pyowm.utils.config import get_default_config
        """
        Получение и озвучивание прогнза погоды
        :param args: город, по которому должен выполняться запос
        """
        # в случае наличия дополнительного аргумента - запрос погоды происходит по нему,
        # иначе - используется город, заданный в настройках
        
        if len(args[0]) >= 3:
            city_name = args[0][0]
        else:
            city_name = self.person.home_city
            print(city_name)

        try:
            # config_dict = get_default_config()
            # config_dict['language'] = 'ru' 
            # использование API-ключа, помещённого в .env-файл по примеру WEATHER_API_KEY = "01234abcd....."
            weather_api_key = "374a9eaca9a88b0fa340acb2baea431b"
            open_weather_map = OWM(weather_api_key)

            # запрос данных о текущем состоянии погоды
            weather_manager = open_weather_map.weather_manager()
            observation = weather_manager.weather_at_place(city_name)
            weather = observation.weather

        # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
        except:
            self.play_voice_assistant_speech(self.translator.get("Seems like we have a trouble. See logs for more information"))
            traceback.print_exc()
            return

        # разбивание данных на части для удобства работы с ними
        status = weather.detailed_status
        temperature = weather.temperature('celsius')["temp"]
        wind_speed = weather.wind()["speed"]
        pressure = int(weather.pressure["press"] / 1.333)  # переведено из гПА в мм рт.ст.

        # вывод логов
        print(colored("Weather in " + city_name +
                    ":\n * Status: " + status +
                    "\n * Wind speed (m/sec): " + str(wind_speed) +
                    "\n * Temperature (Celsius): " + str(temperature) +
                    "\n * Pressure (mm Hg): " + str(pressure), "yellow"))
        status = self.translator.get(str(status))
        # озвучивание текущего состояния погоды ассистентом (здесь для мультиязычности требуется дополнительная работа)
        self.play_voice_assistant_speech(self.translator.get("It is {0} in {1}").format(status, city_name))
        self.play_voice_assistant_speech(self.translator.get("The temperature is {} degrees Celsius").format(str(round(temperature))))
        self.play_voice_assistant_speech(self.translator.get("The wind speed is {} meters per second").format(str(wind_speed)))
        self.play_voice_assistant_speech(self.translator.get("The pressure is {} mm Hg").format(str(pressure)))

    # Изменить язык
    def change_language(self,*args: tuple):
        """
        Изменение языка голосового ассистента (языка распознавания речи)
        """
        self.assistant.speech_language = "ru" if self.assistant.speech_language == "en" else "en"
        self.setup_assistant_voice()
        print(colored("Language switched to " + self.assistant.speech_language, "cyan"))

    # Поиск для пробива человека
    def run_person_through_social_nets_databases(self,*args: tuple):
        """
        Поиск человека по базе данных социальных сетей ВКонтакте и Facebook
        :param args: имя, фамилия TODO город
        """
        if not args[0]: return

        google_search_term = " ".join(args[0])
        vk_search_term = "_".join(args[0])
        fb_search_term = "-".join(args[0])

        # открытие ссылки на поисковик в браузере
        url = "https://google.com/search?q=" + google_search_term + " site: vk.com"
        webbrowser.get().open(url)

        url = "https://google.com/search?q=" + google_search_term + " site: facebook.com"
        webbrowser.get().open(url)

        # открытие ссылкок на поисковики социальных сетей в браузере
        vk_url = "https://vk.com/people/" + vk_search_term
        webbrowser.get().open(vk_url)

        fb_url = "https://www.facebook.com/public/" + fb_search_term
        webbrowser.get().open(fb_url)

        self.play_voice_assistant_speech(self.translator.get("Here is what I found for {} on social nets").format(google_search_term))

    # Подбросить монетку
    def toss_coin(self,*args: tuple):
        """
        "Подбрасывание" монетки для выбора из 2 опций
        """
        flips_count, heads, tails = 3, 0, 0

        for flip in range(flips_count):
            if random.randint(0, 1) == 0:
                heads += 1

        tails = flips_count - heads
        winner = "Tails" if tails > heads else "Heads"
        self.play_voice_assistant_speech(self.translator.get(winner) + " " + self.translator.get("won"))

    """
        Блок изменений параметров пользователя
    """

    def change_name(self,*args:tuple):
        self.play_voice_assistant_speech(self.translator.get("Whose name you could use?"))
        voice_input = self.record_and_recognize_audio()
        self.person.name = voice_input
        self.play_voice_assistant_speech(self.translator.get("Well {}! We can continue our work now".format(self.person.name)))
    
    def change_city(self,*args:tuple):
        self.play_voice_assistant_speech(self.translator.get("And what city you live?"))
        voice_input = self.record_and_recognize_audio()
        self.person.home_city = voice_input
        self.play_voice_assistant_speech(self.translator.get("Location was changed on {}".format(self.person.home_city)))

    

    """
        Блок взаимодействия с оперционной системой
    """

    def turn_off_the_computer(self,*args:tuple): # Выключение устройства
        self.play_voice_assistant_speech(self.translator.get("Iniciate turn off the computer. See you soon {}, goodbye").format(self.person.name))
        os.system("shutdown -s -t 0")
    
    def restart_the_computer(self,*args:tuple): # Выключение устройства
        self.play_voice_assistant_speech(self.translator.get("Iniciate restart the computer. Wait a minute.").format(self.person.name))
        os.system("reboot")

    def sleeping_mode(self,*args:tuple): # Гибернация устройства
        self.play_voice_assistant_speech(self.translator.get("Good night, {}").format(self.person.name))
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    
    def press_in_center(self,*args:tuple):
        ptg.click(1000,500)


    # перечень команд для использования (качестве ключей словаря используется hashable-тип tuple)
    # в качестве альтернативы можно использовать JSON-объект с намерениями и сценариями
    # (подобно тем, что применяют для чат-ботов)
    # Выполнение функции
    def execute_command_with_name(self,command_name: str, *args: list):
        """
        Выполнение заданной пользователем команды и аргументами
        :param command_name: название команды
        :param args: аргументы, которые будут переданы в метод
        :return:
        """
        find = False
        for key in self.commands.keys():
            if command_name in key:
                self.commands[key](*args)
                find = True
            else:
                pass
        if find == False:
            self.play_voice_assistant_speech("Я не поняла что вы сказали, повторите еще раз ?")
            

    
    def RunVoiceAsistent(self):
        # установка голоса по умолчанию
        self.setup_assistant_voice()
        
        while True:
            # старт записи речи с последующим выводом распознанной речи и удалением записанного в микрофон аудио
            voice_input = self.record_and_recognize_audio()
            files = os.listdir()
            if "microphone-results.wav" in files:
                os.remove("microphone-results.wav")
            # отделение комманд от дополнительной информации (аргументов)
            if voice_input != None:
                if self.assistant.name in voice_input:
                    if voice_input == self.assistant.name:
                        self.play_voice_assistant_speech("Что?")
                    else:
                        print(colored(voice_input, "blue"))
                        voice_input = voice_input[voice_input.find(self.assistant.name)+len(self.assistant.name):]
                        # voice_input = voice_input[1]
                        command = voice_input
                        command2 = ""
                        if len(command.split(" ")) > 1:
                            for key in self.commands.keys():
                                for val in key:
                                    if val in command:
                                        command2 = val
                        command = command2
                        try:
                            command_options = voice_input.strip().split(command)
                        except ValueError:
                            command_options = ""
                        self.execute_command_with_name(command, command_options)

run = VoiceInit()
run.RunVoiceAsistent()
