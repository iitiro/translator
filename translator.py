import json
import os
from openai import OpenAI
import re

# Читання API ключа з файлу API_assembly.txt
api_key_file = '/Users/ikudinov/Documents/Code/keys/api_openai.txt'

# Перевірка наявності файлу з API ключем
if not os.path.exists(api_key_file):
    print(f"Файл {api_key_file} не знайдено.")
    exit()

# Читання ключа
with open(api_key_file, 'r') as file:
    api_key = file.read().strip()

# Ініціалізація клієнта OpenAI
client = OpenAI(api_key=api_key)

# Системне повідомлення для моделі
def get_system_prompt(language):
    if language == "ua":
        return "You are a language expert, your job is to translate from English to Ukrainian."
    elif language == "en":
        return "You are a language expert, your job is to translate from Ukrainian to English."
    elif language == "ru-en":
        return "You are a language expert, your job is to translate from Russian to English."
    elif language == "ru-ua":
        return "You are a language expert, your job is to translate from Russian to Ukrainian."

def split_text_by_sentences(text, max_tokens=3000):
    """Функція для розбиття тексту на частини за реченнями (з урахуванням знаків '.', '?', але не '...')"""
    sentences = re.split(r'(?<!\.\.\.)(?<=\.|\?)\s', text)  # Розбиваємо текст на речення

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # Якщо довжина поточного блоку і нового речення перевищує ліміт, зберігаємо блок
        if len(current_chunk) + len(sentence) > max_tokens:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence

    # Додаємо останній блок тексту
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def translate_text(text, system_prompt):
    """Функція для перекладу тексту за допомогою GPT-4"""
    try:
        # Виклик моделі для перекладу тексту
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate the following text: {text}"}
            ],
            model="gpt-4",  # Використання GPT-4
            temperature=0.2,
            max_tokens=3000,  # Ліміт на кількість токенів для перекладу частинами
            top_p=0.1,
            frequency_penalty=0.2,
            presence_penalty=0.1,
        )
        response_json = json.loads(chat_completion.model_dump_json(indent=2))
        content = response_json['choices'][0]['message']['content']
        return content.strip()
    except Exception as e:
        print(f"Помилка під час перекладу: {e}")
        return None

# Шлях до папки з текстовими файлами
input_directory = "./!translator/in/"
output_directory = "./!translator/out/"

# Перевірка наявності папки для виведення, якщо її немає - створюємо
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Перевірка наявності папки з вхідними файлами
if not os.path.exists(input_directory):
    print(f"Папка {input_directory} не знайдена.")
    exit()

# Створюємо список файлів і мов для перекладу
translation_choices = {}

# Проходимо по всіх файлах у папці і збираємо вибори користувача
for filename in os.listdir(input_directory):
    if filename.endswith(".txt"):  # Перевірка, що файл має розширення .txt
        # Визначаємо мову для перекладу на основі назви файлу
        if filename.endswith("_en.txt"):
            translation_choices[filename] = "ua"
        elif filename.endswith("_ua.txt"):
            translation_choices[filename] = "en"
        elif filename.endswith("_ru.txt"):
            print(f"Файл {filename} містить текст російською.")
            language_choice = input("Перекласти на (en) англійську чи (ua) українську? Введіть 'en' або 'ua': ").strip().lower()
            if language_choice in ["en", "ua"]:
                translation_choices[filename] = f"ru-{language_choice}"
            else:
                print(f"Неправильний вибір мови для файлу: {filename}")
                continue
        else:
            print(f"Файл {filename} не відповідає жодному відомому суфіксу для перекладу.")
            continue

# Перекладаємо всі файли на основі виборів користувача
for filename, language in translation_choices.items():
    file_path = os.path.join(input_directory, filename)
    system_prompt = get_system_prompt(language)

    # Читання тексту з файлу
    with open(file_path, 'r', encoding='utf-8') as f:
        text_to_translate = f.read()

    print(f"Переклад файлу: {filename}")

    # Розбиття тексту на частини за реченнями
    text_chunks = split_text_by_sentences(text_to_translate)

    translated_text = ""
    
    # Перекладаємо кожен блок тексту окремо
    for chunk in text_chunks:
        translated_chunk = translate_text(chunk, system_prompt)
        if translated_chunk:
            translated_text += translated_chunk + "\n\n"
    
    if translated_text:
        # Формування імені для збереження перекладеного файлу
        output_filename = os.path.splitext(filename)[0] + "_translated.txt"
        output_filepath = os.path.join(output_directory, output_filename)

        # Запис перекладеного тексту у новий файл
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(translated_text)

        print(f"Переклад збережено: {output_filepath}")
    else:
        print(f"Не вдалося перекласти файл: {filename}")

# Повідомлення про завершення обробки всіх файлів
print("Переклад всіх файлів завершено.")