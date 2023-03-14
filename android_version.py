import os
import openai
import threading
import sounddevice as sd
from scipy.io.wavfile import write

#This is the part of the script that will handle transactions between the curl address and the python script for vocalising the transactions. 
models = {"gpt-3.5-turbo":"/v1/chat/completions","whisper-1":"/v1/audio/transcriptions"}
#gpt-3.5-turbo -> endpoint '/v1/chat/completions'
#whisper-1 -> endpoint '/v1/audio/transcriptions'
# whisper-1 ->endpoint '/v1/audio/translations'

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
    print("Recording audio")
    fs = 44100  # Sample rate
    seconds = duration  # Duration of recording
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished
    write('output.wav', fs, myrecording)  # Save as WAV file
    print("Audio recorded")
    return "output.wav"

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
        #append the response to the message history if its not empty and return it
        append_to_local_log_file(response)
        #if response contains the string '"content":""\n'
        #check if there is anything between the content and the newline
        # if there is, then return the response
        # if there is not, then return None
        try:
            #turn the response into a simple string
            response = str(response)
            #find '"content":' and then find the next '",'
            #get the string inbetween
            #if the string is empty, then return None
            #if the string is not empty, then return the response
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
    #check if the subdir conversations exists
    #if it does not, then create it
    #if it does, then continue
    #check if the file convo_name exists
    #if it does not, then create it
    #if it does, then append data to it
    #if the file is too large, then create a new file
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
            speech_to_text = record_and_transcribe(int(input("Enter duration of recording: (seconds)")))
            messageHistory.append({"role": "user", "content": str(speech_to_text)})
            newMessageHistory = prompt_chat_GPT(messageHistory)
            if newMessageHistory!=None:
                messageHistory = newMessageHistory
            lastMessage = messageHistory[-1]["content"]
            print(lastMessage)
            speaker = threading.Thread(target=text_to_speech_english,args=(lastMessage,))
            speaker.start()
            if speech_to_text != None:
                log_conversation(speech_to_text,messageHistory)
            #if the last message from the user is not empty, then 
        
if __name__ == "__main__":
    initiate_conversation()
