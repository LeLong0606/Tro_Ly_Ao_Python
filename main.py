# pip install openai
# pip install SpeechRecognition
# pip install pyttsx3
# pip install pyaudio

import time
import openai
import speech_recognition as sr
import pyttsx3
import os

# Function to get OpenAI API key
def get_openai_key():
    with open('key.txt') as f:
        return f.read().strip()

# Create a OpenAI connection to access its threads and assistants
openai_client = openai.OpenAI(api_key=get_openai_key())
openai_threads = openai_client.beta.threads
openai_assistants = openai_client.beta.assistants

# Function Create Assistant
def create_assistant():
    assistant = openai_assistants.create(
        name="Orion",
        instructions="This is a virtual assistant that helps you answer the problems you are having",
        tools=[],
        model="gpt-4-1106-preview"
    )
    return assistant

# Function Delete Assistant
# def delete_assistant(assistant):
#     try:
#         openai_assistants.delete(assistant.id)
#         print("[Orion]: Assistant has been successfully deleted.")
#     except Exception as e:
#         print(f"[Error]: Unable to delete assistant. {e}")

# Function Listen And Recognize
def listen_and_recognize():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        print("[Orion] Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"[You]: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("Unable to recognize speech")
        return "unrecognized"
    except sr.RequestError as e:
        print(f"Connection error: {e}")
        return "error"

# Function Speak
def speak(output_text):
    engine = pyttsx3.init()
    engine.say(output_text)
    engine.runAndWait()

#Function to get assistant ID from file
def get_assistant_id():
    if os.path.exists('assistant_id.txt'):
        with open('assistant_id.txt', 'r') as f:
            return f.read().strip()
    return None

# Function to save the assistant's ID to file
def save_assistant_id(assistant_id):
    with open('assistant_id.txt', 'w') as f:
        f.write(assistant_id)

# Function to create or get assistant
def get_or_create_assistant():
    assistant_id = get_assistant_id()
    if assistant_id:
        try:
            return openai_assistants.retrieve(assistant_id)
        except openai.OpenAIError:
            print("Assistant with saved ID not found. Creating a new one.")

    assistant = create_assistant()
    save_assistant_id(assistant.id)
    return assistant

# Function waiting for command
def wait_for_activation():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    while True:
        with microphone as source:
            print("[Orion] Waiting for activation...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio, language="en-US").lower()
            if "hello" in text.lower() or "orion" in text.lower():
                return True
            if "bye" in text.lower():
                return False
        except sr.UnknownValueError:
            pass  # Continue waiting if voice is not recognized
        except sr.RequestError as e:
            print(f"Connection error: {e}")

# Function listens for questions
def ask_question():
    return listen_and_recognize()

# Function finds the answer to the question
def ask_assistant(user_question, thread, assistant):
    # Pass in the user question into the existing thread
    openai_threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_question
    )

    # Use runs to wait for the assistant response
    run = openai_threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        # instructions=f'Keep in mind that user has no knowledge of math, especially {user_question} so please explain the answer in detail and simple.'
    )

    is_running = True
    while is_running:
        run_status = openai_threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        is_running = run_status.status != "completed"
        time.sleep(1)

    return run

# Function gives the answer
def assistant_response(thread, run):
    # Get information from the thread as it was
    # Get the messages list from the thread
    messages = openai_threads.messages.list(thread_id=thread.id)
    # Get the last message for the current run
    last_message = [message for message in messages.data if message.run_id == run.id and message.role == "assistant"][
        -1]
    # If an assistant message is found, print it
    if last_message:
        response = last_message.content[0].text.value
        print(f"[Orion]: {response}")
        speak(response)
    else:
        error_message = "I'm sorry, I am not sure how to answer that. Can you ask another question?"
        print(f"[Orion]: {error_message}")
        speak(error_message)

# Main function
def main():
    unrecognized_count = 0  # Variable that counts the number of times the voice was not recognized
    assistant = get_or_create_assistant()
    thread = openai_threads.create()
    greeting = "Hello, I am Orion, programmed to answer all your questions. How can I help you today?"
    print(f"[Orion]: {greeting}")
    speak(greeting)

    asking = True
    while asking:
        user_question = ask_question()
        # Check if voice is not recognized
        if user_question == "unrecognized":
            unrecognized_count += 1
            if unrecognized_count >= 2:
                goodbye_coercion = "Looks like you have no more questions. Goodbye!"
                print(f"[Orion]: {goodbye_coercion}")
                speak(goodbye_coercion)
                break
            else:
                continue

        if "bye" in user_question.lower():
            goodbye_message = "Goodbye. Pleased to serve you!"
            print(f"[Orion]: {goodbye_message}")
            speak(goodbye_message)
            break

        run = ask_assistant(user_question, thread, assistant)
        assistant_response(thread, run)

    # delete_assistant(assistant)  # Delete the assistant after use

if __name__ == "__main__":
    while True:
        activation = wait_for_activation()
        if activation:
            main()  # Run main program if enabled
        else:
            message_ends = "Goodbye!"
            print(f"[Orion]: {message_ends}")
            speak(message_ends)
            break  # Exit the loop and end the program