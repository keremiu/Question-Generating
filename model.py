import openai
import pandas as pd
import re

openai.api_key = "your_openai_key"

def parse_questions(content):
    question_indices = [match.start() for match in re.finditer(r"\b\d+\.\s", content)]
    questions = []

    for i in range(len(question_indices)):
        start_index = question_indices[i]
        end_index = question_indices[i + 1] if i + 1 < len(question_indices) else len(content)
        questions.append(content[start_index:end_index].strip())

    return questions
  
def generate_questions(difficulty, topic="", n=1):
    base_prompts = {
        "easy": "easy Python-related",
        "medium": "medium difficulty Python-related",
        "hard": "hard Python-related"
    }

    topic_prompt = f" about {topic}" if topic else ""

    questions, options, answers = [], [], []

    prompt = f"Generate {n} {base_prompts[difficulty]} multiple choice questions{topic_prompt}."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.8,
        max_tokens=500,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    generated_content = response.choices[0].message['content'].split("\n\n")
    parsed_questions = parse_questions(str(generated_content)) if n > 1 else [" ".join(generated_content)]
    
    for i, question in enumerate(parsed_questions):
        if i >= n:
            break

        answer_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"What is the correct answer for the following question?\n\n{question}"}
            ]
        )
        raw_answer = answer_response.choices[0].message['content'].strip()

        match = re.search(r'([A-Ea-e])\)', raw_answer)
        if match:
            answer_letter = match.group(1).upper()
        else:
            print("Could not determine the answer from GPT's response.")
            continue

        # Using regex to extract all the options from the question
        options_matches = re.findall(r'([A-Ea-e])\)\s*(.+)', question)
        option_string = "\n".join([f"{match[0]}) {match[1]}" for match in options_matches])

        questions.append(question)
        answers.append(answer_letter)
        options.append(option_string)

    return questions, options, answers

difficulty = input("Please select difficulty (easy/medium/hard): ").lower()
n = int(input("How many questions do you want to generate at once? "))
topic = input("Enter a specific Python topic (e.g. 'class', 'args') or leave blank for general: ")

questions, options, answers = generate_questions(difficulty, topic, n)

data = {'Question': questions, 'Options': options, 'Answer': answers}
df = pd.DataFrame(data)

filename = f'generated_mcq_questions_{difficulty}.csv'
df.to_csv(filename, index=False)
print(f"Questions saved to {filename}")
