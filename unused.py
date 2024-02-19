import os
from dotenv import load_dotenv
from openai import OpenAI
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