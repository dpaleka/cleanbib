#%%
import argparse
import os
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv
import bibtexparser
from bibtexparser.middlewares import SortFieldsCustomMiddleware
from cachier import cachier

CACHE_DIR="cache"

#%%
# Function to reformat bib entry
@cachier(cache_dir=CACHE_DIR)
def reformat(title):
    # Load environment variables from .env file
    load_dotenv()

    # Initialize OpenAI client with API key
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Prepare the prompt
    prompt_1 = """\
Reformat this bib title to wrap `{}` around names that should be capitalized, but not around other words.
Also wrap any beginning of a full sentence (not a subordinate clause) in `{}`.
Do not wrap the string "Large Language Models" in `{}`. Do not wrap random words in `{}`.

Example 1:
Concept Sliders: LoRA Adaptors for Precise Control in Diffusion Models
->
Concept Sliders: {LoRA} Adaptors for Precise Control in Diffusion Models

Example 2:
Tensor Trust: Interpretable Prompt Injection Attacks from an Online Game
Tensor Trust: Interpretable Prompt Injection Attacks from an Online Game

Example 3:
Feedback Loops Drive In-Context Reward Hacking in LLMs
->
Feedback Loops Drive In-Context Reward Hacking in {LLMs}

Example 4:
14 examples of how LLMs can transform materials science and chemistry: A reflection on a large language model hackathon
14 examples of how {LLMs} can transform materials science and chemistry: A reflection on a large language model hackathon

Example 5:
Do LLMs Understand Social Knowledge? Evaluating the Sociability of Large Language Models with SocKET Benchmark
Do {LLMs} Understand Social Knowledge? {Evaluating} the Sociability of Large Language Models with {SocKET} Benchmark


Now it's your turn:\n"""+f"""{title}\n->"""
    
    prompt = """\
Reformat this bib title to wrap `{}` around names that should absolutely be capitalized in the reference, but not around other words.
In general, the first word of a full sentence should be wrapped in `{}`, as well as any all-caps acronyms, or always-capitalized words like "COVID-19".
Feel free to remove any `{}` that are not needed.

Example 1:
Concept Sliders: LoRA Adaptors for Precise Control in Diffusion Models
->
Concept Sliders: {LoRA} Adaptors for Precise Control in Diffusion Models

Now it's your turn:\n"""+f"""{title}\n->"""

    # Call GPT-3.5-turbo model
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        #model="gpt-4-turbo-preview",
        model="gpt-3.5-turbo-0125",
    )

    # Extract and return the reformatted bib entry from the response
    try:
        reformatted_entry = chat_completion.choices[0].message.content
        # find the first @ and return everything after that
        return reformatted_entry.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def reformat_title_using_rules(title):
    words_to_capitalize = ["LLMs", "LLM", "AI", "ML", "NLP", "I", "GPT", "GPTs", "ChatGPT", "Delphi", "Occam’s"]
    lower_words_to_capitalize = [word.lower() for word in words_to_capitalize]
    names = ["Biden", "Harris", "Bradley", "Terry", "Jiang"]

    # first remove random {}
    if title[0] == "{" and title[-1] == "}":
        # remove all {} from the string everywhere
        title = title.replace("{", "").replace("}", "")

    def to_capitalize(word, prev_word=None) -> bool:
        word = word.strip("{}")
        if word.lower() in lower_words_to_capitalize:
            return True
        if word.isupper():
            return True
        if word in names:
            return True
        # if there are two or more capital letters in the word, it's probably an acronym, except if it's a hyphenated word
        if sum(1 for letter in word if letter.isupper()) > 1:
            if "-" not in word:
                return True
            else:
                parts = word.split("-")
                for part in parts:
                    if sum(1 for letter in part if letter.isupper()) > 1:
                        return True
                for part in parts:
                    if part in names:
                        return True
        if prev_word and prev_word[-1] in ".!?":
            return True
        return False
    
    words = title.split()
    for i in range(len(words)):
        if to_capitalize(words[i], words[i-1] if i > 0 else None):
            if words[i] in lower_words_to_capitalize:
                idx = lower_words_to_capitalize.index(words[i])
                words[i] = words_to_capitalize[idx]
            if words[i][0] == "{" and words[i][-1] == "}":
                words[i] = words[i][1:-1]
            words[i] = words[i][0].upper() + words[i][1:]
            words[i] = "{" + words[i] + "}"
    return " ".join(words)

    


# Example usage
def test_reformat():
    title = """Future ML Systems Will Be Qualitatively Different"""
    reformatted_entry = reformat_title_using_rules(title)
    print(f"Reformatted Entry:\n{reformatted_entry}")

test_reformat()

#%%

def parse_with_bibtexparser(input_file):
    with open(input_file) as file:
        content = file.read()

        # Parsing a bibtex string with default values
    bib_database = bibtexparser.parse_string(content)
    #print("\n".join([str(entry) for entry in bib_database.entries]))
    return bib_database

def save_with_bibtexparser(library, output_file):
    bibtex_format = bibtexparser.BibtexFormat()
    bibtex_format.indent = '    '
    bibtex_format.block_separator = '\n\n'

    bib_str = bibtexparser.write_string(library, bibtex_format=bibtex_format)
    with open(output_file, 'w') as file:
        file.write(bib_str)


def reformat_titles(library):
    """
    Entry (line: 13999, type: `article`, key: `swersky2014freeze`):
        `title` = `Freeze-thaw Bayesian optimization`
        `author` = `Swersky, Kevin and Snoek, Jasper and Adams, Ryan Prescott`
        `journal` = `arXiv preprint arXiv:1406.3896`
        `year` = `2014`
    """
    #return {key: reformat(text) for key, text in bib_dict.items()}
    for entry in tqdm(library.entries):
        title = entry['title']
        reformatted_title = reformat_title_using_rules(title)
        if reformatted_title:
            #print(title)
            entry['title'] = reformatted_title
            #print(reformatted_title)
        else:
            print(f"Failed to reformat title for entry {entry}.")
    return library

def lowercase_fields(library):  
    """
    Lowercase "Title" into "title". Don't lowercase the actual entry.
    """
    important_keys = ['title', 'author', 'journal', 'year', 'url', 'abstract']
    for entry in library.entries:
        for key, value in entry.items():
            for important_key in important_keys:
                if key.lower() == important_key and key != important_key:
                    entry[important_key] = value
                    del entry[key]
    return library


def remove_unnecessary(library):
    for entry in library.entries:
        if 'abstract' in entry:
            del entry['abstract']
        if 'keywords' in entry:
            del entry['keywords']
    return library

def reorder_properly(library):
    # Reorder fields so that title goes first, then author, then whatever order was there before
    custom_order = ['title', 'author']
    middleware = SortFieldsCustomMiddleware(order=custom_order, case_sensitive=False)
# Use the middleware to sort the fields of the entry
    for entry in library.entries:
        entry = middleware.transform_entry(entry, library)
    return library
        
def reduce_num_authors_and_clean(library):
    for entry in library.entries:
        if 'author' in entry:
            authors = entry['author']
            print(authors)
            if " and" in authors:
                author_list = authors.split(" and")
                print(author_list)
                author_list = [author.strip() for author in author_list]
                if len(author_list) >= 21:
                    # first 19, then ..., then last one
                    #author_list = author_list[:19] + ["..."] + author_list[-1]
                    author_list = author_list[:19] + ["..."] + [author_list[-1]]
                authors = " and ".join(author_list)
                entry['author'] = authors
                print("Modified authors:", authors)
    return library

def sort_library(library):
    # Sort the entries by year, then by title
    library.entries.sort(key=lambda x: (x['title']))
    return library

def main():
    parser = argparse.ArgumentParser(description="Process and reformat a .bib file.")
    parser.add_argument("--input_file", "-i", type=str, help="Name of the input file")
    parser.add_argument("--out_file", "-o", type=str, help="Name of the output file")
    args = parser.parse_args()

    library = parse_with_bibtexparser(args.input_file)
    library = lowercase_fields(library)
    library = remove_unnecessary(library)
    library = reorder_properly(library)
    library = reformat_titles(library)
    library = sort_library(library)
    library = reduce_num_authors_and_clean(library)
    save_with_bibtexparser(library, args.out_file)
    #library = reformat_library(library)
    #bib_dict = load_bibfile(args.input_file)
    #reformatted_bib_dict = reformat_bibfile(bib_dict)
    #save_bibfile(reformatted_bib_dict, args.out_file)
    #print(reformatted_bib_dict)

if __name__ == "__main__":
    main()