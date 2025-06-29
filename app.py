import os
os.environ["SDL_AUDIODRIVER"] = "dummy"  # <-- Esto es lo importante

from ollama import chat
import speech_recognition as sr
from datetime import date
from gtts import gTTS
from io import BytesIO
from pygame import mixer 
import threading
import queue
import time

mixer.init()

#os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

today = str(date.today())

numtext = 0 
numtts = 0 
numaudio = 0

messages = [] 

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
    llm_finished.set()  # Signal completion of the text generation by LLM

def speak_text(text):
    mp3file = BytesIO()
    tts = gTTS(text, lang="en", tld = 'us') 
    tts.write_to_fp(mp3file)
    mp3file.seek(0)
    try:
        mixer.music.load(mp3file, "mp3")
        mixer.music.play()
        while mixer.music.get_busy(): 
            time.sleep(0.1)
    except KeyboardInterrupt:
        mixer.music.stop()
        mp3file.close()
    mp3file.close()	

def text2speech(text_queue, textdone,llm_finished, audio_queue, stop_event):
    global numtext, numtts
    while not stop_event.is_set():  # Keep running until stop_event is set
        if not text_queue.empty():
            text = text_queue.get(timeout = 0.5)  # Wait for 2 second for an item
            numtts += 1 
            mp3file = BytesIO()
            tts = gTTS(text, lang="en", tld = 'us') 
            tts.write_to_fp(mp3file)
            audio_queue.put(mp3file)
            text_queue.task_done()
        if llm_finished.is_set() and numtts == numtext: 
            time.sleep(0.2)
            textdone.set()
            break 
        
def play_audio(audio_queue,textdone, stop_event):
    global numtts, numaudio 
    while not stop_event.is_set():  # Keep running until stop_event is set
        mp3audio = audio_queue.get()  # Get BytesIO object (non-blocking)
        numaudio += 1 
        mp3audio.seek(0)
        mixer.music.load(mp3audio, "mp3")
        mixer.music.play()
        while mixer.music.get_busy(): 
            time.sleep(0.1)
        audio_queue.task_done() 
        if textdone.is_set() and numtts == numaudio: 
            break  # Exit loop if queue is empty and processing is finished         

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
