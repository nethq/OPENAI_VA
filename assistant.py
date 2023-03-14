import os
import time
import openai
import threading
import pyaudio
import wave

def text_to_speech_english(text):
    import pyttsx3
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()



def transcribe_audio_english(audio_file_path):
    try:
        openai.api_key = open("key.env","r").read()
    except:
        print("Error: API key not found; key.env not found, or key not readable")
        return
    try:
        audio = open(audio_file_path,"rb")
        transcript = openai.Audio.transcribe("whisper-1",audio)
        if transcript["text"]!="":
            return transcript["text"]
        else:
            return transcript
    except:
        print("Error: Audio file not found")
        return
    
def record_audio(duration=5):
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fs = 44100  # Record at 44100 samples per second
    seconds = duration
    filename = "output.wav"

    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    print('Recording')

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []  # Initialize array to store frames

    # Store data in chunks for 3 seconds
    for i in range(0, int(fs / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream 
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()

    print('Finished recording')

    # Save the recorded data as a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()
    return filename

def record_and_transcribe(duration):
    x = record_audio(duration)
    ret = transcribe_audio_english(x)
    return ret

def prompt_chat_GPT(messageHistory,token_limit=50,temperature=0.65,stop=["\n","###"]):
    try:
        openai.api_key = open("key.env","r").read()
    except:
        print("Error: API key not found; key.env not found, or key not readable")
        return
    try:
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messageHistory
        )
        append_to_local_log_file(response)
        try:
            response = str(response)
            content_start = response.find('"content":')
            content_end = response.find('",',content_start)
            content = response[content_start+11:content_end]
            if content!="":
                messageHistory.append({"role": "assistant", "content": content})
                return messageHistory
            else:
                print("Response not analysed, saving to log.")
                return None
        except:
            print("Response not analysed, saving to log.")
            return
        else:
            return response
    except:
        print("Error: Prompt not sent")
        return

def append_to_local_log_file(data):
    if not os.path.exists("log.txt"):
        open("log.txt","w").close()
    with open("log.txt","a") as f:
        f.write(str(data)+"\n")

def log_conversation(convo_string,convo_data):
    if not os.path.exists("conversations"):
        os.mkdir("conversations")
    if not os.path.exists("conversations/"+str(convo_string).strip()+".txt"):
        file = open("conversations/{0}.txt".format(convo_string),"a")
        file.write(str(convo_data))
        file.close()


def initiate_conversation():
    speaker = threading.Thread()
    messageHistory = [{"role": "system", "content": "You are a portable assistant, you will try to be as short and as concise as possible."}]
    while input("Press enter to continue, or type 'exit' to exit: ")!="exit":
        try:
            speech_to_text = record_and_transcribe(int(input("Enter duration of recording: (seconds)")))
            messageHistory.append({"role": "user", "content": str(speech_to_text)})
            newMessageHistory = prompt_chat_GPT(messageHistory)
            if newMessageHistory!=None:
                messageHistory = newMessageHistory
            lastMessage = messageHistory[-1]["content"]
            speaker = threading.Thread(target=text_to_speech_english,args=(lastMessage,))
            speaker.start()
            if speech_to_text != None:
                log_conversation(speech_to_text,messageHistory)
        except:
            print("ERROR: Recording/Transcription failed, please try again.")
        
if __name__ == "__main__":
    initiate_conversation()
