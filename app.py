import os
os.environ["SDL_AUDIODRIVER"] = "dummy"  # <-- Esto es lo importante

from ollama import chat
import speech_recognition as sr
from datetime import date
from io import BytesIO
from pygame import mixer 
import threading
import queue
import time
from pydub import AudioSegment
from elevenlabs import generate, save, set_api_key

mixer.init()

#os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

today = str(date.today())

numtext = 0 
numtts = 0 
numaudio = 0

messages = []

# ElevenLabs config
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')

if ELEVENLABS_API_KEY:
    set_api_key(ELEVENLABS_API_KEY)

def generate_speech_elevenlabs(text, wavfile):
    """Genera audio usando ElevenLabs"""
    try:
        if not ELEVENLABS_API_KEY:
            print("Error: ELEVENLABS_API_KEY no configurada")
            return False
            
        # Generar audio con ElevenLabs
        audio = generate(
            text=text,
            voice=ELEVENLABS_VOICE_ID,
            model="eleven_multilingual_v2"
        )
        
        # Guardar directamente como WAV
        save(audio, wavfile)
        return True
    except Exception as e:
        print(f"Error generando audio con ElevenLabs: {e}")
        return False

def chatfun(request, text_queue, llm_finished):
    global numtext, messages
    messages.append({'role': 'user', 'content': request})

    response = chat(
        model = 'isa',
        messages = messages,
        stream = True,
    )
    
    shortstring = ''  
    reply = ''
    append2log(f"AI: ") 

    for chunk in response:
        ctext = chunk['message']['content']
        shortstring = "".join([shortstring, ctext])
        if len(shortstring) > 40:
            print(shortstring, end='', flush=True) 
            text_queue.put(shortstring.replace("*", ""))
            numtext += 1 
            reply = "".join([reply, shortstring])
            shortstring = ''
        else:
            continue
        time.sleep(0.2)
     
    if len(shortstring) > 0: 
        print(shortstring, end='', flush=True) 
        shortstring = shortstring.replace("*", "")
        text_queue.put(shortstring)                          
        numtext += 1 
        reply = "".join([reply, shortstring])
        
    messages.append({'role': 'assistant', 'content': reply})
    append2log(f"{reply}") 
    llm_finished.set()

def speak_text(text):
    wavfile = "temp_speak.wav"
    if generate_speech_elevenlabs(text, wavfile):
        try:
            mixer.music.load(wavfile)
            mixer.music.play()
            while mixer.music.get_busy(): 
                time.sleep(0.1)
            os.remove(wavfile)
        except KeyboardInterrupt:
            mixer.music.stop()
            if os.path.exists(wavfile):
                os.remove(wavfile)
    else:
        print("Error generando audio para reproducción")

def text2speech(text_queue, textdone,llm_finished, audio_queue, stop_event):
    global numtext, numtts
    while not stop_event.is_set():
        if not text_queue.empty():
            text = text_queue.get(timeout = 0.5)
            numtts += 1 
            wavfile = f"temp_tts_{numtts}.wav"
            if generate_speech_elevenlabs(text, wavfile):
                audio_queue.put(wavfile)
            text_queue.task_done()
        if llm_finished.is_set() and numtts == numtext: 
            time.sleep(0.2)
            textdone.set()
            break

def play_audio(audio_queue,textdone, stop_event):
    global numtts, numaudio 
    while not stop_event.is_set():
        wavfile = audio_queue.get()
        numaudio += 1 
        try:
            mixer.music.load(wavfile)
            mixer.music.play()
            while mixer.music.get_busy(): 
                time.sleep(0.1)
            os.remove(wavfile)
        except Exception as e:
            print(f"Error reproduciendo audio: {e}")
        audio_queue.task_done() 
        if textdone.is_set() and numtts == numaudio: 
            break

def append2log(text):
    global today
    fname = 'chatlog-' + today + '.txt'
    with open(fname, "a", encoding='utf-8') as f:
        f.write(text + "\n")
        f.close 
      
slang = "en-EN"

def main():
    global today, slang, numtext, numtts, numaudio, messages
    rec = sr.Recognizer()
    mic = sr.Microphone()
    rec.dynamic_energy_threshold=False
    rec.energy_threshold = 400    
    i=1
    sleeping = True 
    while True:     
        with mic as source:            
            rec.adjust_for_ambient_noise(source, duration= 1)
            print("Listening ...")
            try: 
                audio = rec.listen(source, timeout = 20, phrase_time_limit = 30)
                text = rec.recognize_google(audio, language=slang)
                if sleeping == True:
                    if "jack" in text.lower():
                        request = text.lower().split("jack")[1]
                        sleeping = False
                        append2log(f"_"*40)                    
                        today = str(date.today())  
                        messages = []                      
                        if len(request) < 2:
                            speak_text("Hi, there, how can I help?")
                            append2log(f"AI: Hi, there, how can I help? \n")
                            continue                      
                    else:
                        continue
                else: 
                    request = text.lower()
                    if "that's all" in request:
                        append2log(f"You: {request}\n")
                        speak_text("Bye now")
                        append2log(f"AI: Bye now. \n")                        
                        print('Bye now')
                        sleeping = True
                        continue
                    if "jack" in request:
                        request = request.split("jack")[1]                        
                append2log(f"You: {request}\n ")
                print(f"You: {request}\n AI: ", end='')
                text_queue = queue.Queue()
                audio_queue = queue.Queue()
                llm_finished = threading.Event()                
                data_available = threading.Event() 
                textdone = threading.Event() 
                busynow = threading.Event()
                stop_event = threading.Event()                
                llm_thread = threading.Thread(target=chatfun, args=(request, text_queue,llm_finished,))
                tts_thread = threading.Thread(target=text2speech, args=(text_queue,textdone,llm_finished, audio_queue, stop_event,))
                play_thread = threading.Thread(target=play_audio, args=(audio_queue,textdone, stop_event,))
                llm_thread.start()
                tts_thread.start()
                play_thread.start()
                llm_finished.wait()
                llm_thread.join()  
                time.sleep(0.5)
                audio_queue.join()
                stop_event.set()  
                tts_thread.join()
                play_thread.join()  
                numtext = 0 
                numtts = 0 
                numaudio = 0
                print('\n')
            except Exception as e:
                continue 
 
if __name__ == "__main__":
    main()
