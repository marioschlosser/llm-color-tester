import openai
import os
from dotenv import load_dotenv
from itertools import islice
import time
import random
import string

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

def get_response_message(response):
    for choice in response.choices:
        if choice.message.role == 'assistant':
            message = choice.message.content
    return message

# load the prompt from a text file
with open("prompt.txt", "r") as text_file:
    prompt = text_file.read()

# initialize list of objects
test_objects = {}

# open text file with objects and colors and create test_objects
with open("objects_and_colors.txt", "r") as text_file:
    lines = text_file.readlines()
    for line in lines:
        line = line.strip()
        if line:
            test_objects.update({line.split(",")[0].strip(): line.split(",")[1].strip()})

# run the test for x different sizes of objects in the context window
num_test_intervals = 4
test_sizes = [len(test_objects) * (x+1) // num_test_intervals for x in range(num_test_intervals)]

# number of complete tests to run
test_number_max = 3

# list of lists that will store the number of correct tests of each test run
test_correct = []

# current test index
test_index = 0

# maximum number of retries per OpenAI API call
max_attempts = 5

# create randomized string for test file name
test_file_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

# create a text file that will store the number of correct tests of reach test run, with random file name
with open("test_results_" + test_file_name + ".txt", "w") as text_file:
    text_file.write("")

# run several tests
for test_index in range(test_number_max):
    # shuffle the dict for each test run
    tmp_items = list(test_objects.items())
    random.shuffle(tmp_items)
    shuffled_dict = dict(tmp_items)

    # reset test results for this test run
    test_correct.append([])

    # test all the different context sizes
    for test_size in test_sizes:
        print("Now evaluating # of objects in context window: " + str(test_size))

        # create the input string of objects
        data_string = "\n".join(f"{index}. {key}" for index, (key, value) in enumerate(islice(shuffled_dict.items(), test_size), 1))

        # and for backup, here with colors
        data_string_with_colors = "\n".join(f"{index}. {key}, {value}" for index, (key, value) in enumerate(islice(shuffled_dict.items(), test_size), 1))

        for attempt in range(max_attempts):
            print("Attempt: ", attempt)

            message = [{"role": "system", "content": prompt}, {"role": "user", "content": data_string}]

            print("Input (with colors):")
            print(data_string_with_colors)

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    max_tokens=3000,
                    temperature=0,
                    messages=message)

                break  # if the operation succeeds, exit the loop
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error {e}. Retrying...")
                time.sleep(30)
            else:
                print(f"Operation failed after {max_attempts} attempts.")

        msg = get_response_message(response)

        print("Output:")
        print(msg)

        # save input and output in a text file
        with open("test" + str(test_index) + "_" + str(test_size) + "_" + test_file_name + ".txt", "w") as text_file:
            text_file.write("Input (with colors):\n")
            text_file.write(data_string_with_colors)
            text_file.write("\n\nOutput:\n")
            text_file.write(msg)

        # Split the string by newline to get each object-color pair
        pairs = msg.split("\n")

        # Create a dictionary by splitting each pair by a comma
        ranked_dict = {}
        for pair in pairs:
            try:
                ranked_dict.update({pair.split(",")[0].strip(): pair.split(",")[1].strip()})
            except:
                print("error: " + pair)

        # evaluate the color correctness
        correct = sum(1 for obj, color in islice(shuffled_dict.items(), test_size) if color == ranked_dict.get(obj, None))

        test_correct[test_index].append(correct)

        # append the test index, the size of the test and the number of correct results to the results text file
        with open("test_results_" + test_file_name + ".txt", "a") as text_file:
            text_file.write(str(test_index) + "," + str(test_size) + "," + str(correct) + "\n")

print(test_correct)