#see https://github.com/jiggy-ai/pydantic-chatcompletion/blob/master/example/book_info.py
import requests
import json
import logging
from pydantic import BaseModel, ValidationError
from pydantic import  Field
from typing import Optional
from typing import List, Tuple

#endpoint url
url = "http://localhost:1337/v1/chat/completions"


"""
Wrapper  that compels the language model to produce a valid Pydantic model as output via prompting and iterative error remediation.  The easiest way to go from unstructured text to structured Pydantic data.

It uses the pydantic json_schema to help guide the model to the required output format.

It will retry the task with error messages if the model does not produce appropriate output data due to either a json load issue or a pydantic validation issue.

"""

def create(messages : List[dict], model_class: BaseModel, retry=2, temperature=0, **kwargs) -> BaseModel:

    messages.append({"role"   : "system",
                     "content": f"Please respond ONLY with valid json that conforms to this pydantic json_schema: {model_class.schema_json()}. Do not include additional text other than the object json as we will load this object with json.loads() and pydantic."})

        #Headers
    headers = {
        "Content-Type": "application/json",
    }

    payload = {
      "messages": messages,
      "model": "dolphin-phi-2",
      "stream": False,
      "max_tokens": 2048,
      "stop": ["hello"],
      "frequency_penalty": 0,
      "presence_penalty": 0,
      "temperature": temperature,
      "top_p": 0.95
    }


    last_exception = None
    for i in range(retry+1):
        #response = openai.ChatCompletion.create(messages=messages, temperature=temperature, **kwargs)
        response = requests.post(url, headers=headers, data = json.dumps(payload))
        #Extracting 'content' value from response
        #print(response.text)
        result = response.json()
        #content = result['choices'][0]['message']['content']
        
        assistant_message= result['choices'][0]['message']
        content = assistant_message['content']
        try:
            json_content = json.loads(content)
        except Exception as e:
            last_exception = e
            error_msg = f"json.loads exception: {e}"
            logging.error(error_msg)
            messages.append(assistant_message)
            messages.append({"role"   : "system",
                            "content": error_msg})
            continue
        try:
            return model_class(**json_content)
        except ValidationError as e:
            last_exception = e
            error_msg = f"pydantic exception: {e}"
            logging.error(error_msg)
            messages.append(assistant_message)            
            messages.append({"role"   : "system",
                            "content": error_msg})    
    raise last_exception
            

class BookInformation(BaseModel):
    title: str = Field(description="The title of the book")
    author: str = Field(description="The name of the book's author")
    publication_year: Optional[int] = Field(description="The publication year of the book")
    genre: Optional[str] = Field(description="The genre of the book")
    characters: Optional[List[str]] = Field(description="A list of the main characters in the book")
    summary: Optional[str] = Field(min_length=10, description="A brief summary of the book's plot")
 
model_class = BookInformation
# Input unstructured text
unstructured_text = """
Pride and Prejudice is a novel by Jane Austen, published in 1813.
This classic novel follows the story of Elizabeth Bennet, the protagonist, as she navigates issues of manners, morality, education, and marriage in the society of the landed gentry of early 19th-century England.
The story revolves primarily around Elizabeth and her relationship with the haughty yet enigmatic Mr. Darcy.
The book is set in rural England, and it is notable for its wit and humor as well as its commentary on class distinctions, social norms, and values.
Some of the main characters in the novel include Elizabeth Bennet, Mr. Darcy, Jane Bennet, Mr. Bingley, Lydia Bennet, and Mr. Wickham.
Pride and Prejudice is considered a classic work of English literature and has been adapted numerous times for television, film, and stage.
It is often categorized as a romantic novel, but it also has elements of satire and social commentary.
"""

# Set up messages
messages = [
    {"role": "user", "content": "Extract the book information from the following content:"},
    {"role": "user", "content": unstructured_text},
  ]

out_class = create(messages, model_class, retry = 10,temperature = 0.7)
print(out_class)

#first error with json format and fed error into context and retried
"""
ERROR:root:json.loads exception: Expecting ',' delimiter: line 16 column 25 (char 331)
"""
#then succesffully returned json/ class schema
"""
title='Pride and Prejudice' 
author='Jane Austen' 
publication_year=1813 
genre='Romantic novel' 
characters=['Elizabeth Bennet', 'Mr. Darcy', 'Jane Bennet', 'Mr. Bingley', 'Lydia Bennet', 'Mr. Wickham'] 
summary='A classic novel about manners, morality, education, and marriage in early 19th-century England. It follows the story of Elizabeth Bennet and her relationship with Mr. Darcy.'
"""
#another run after a pydantic exception of missing fields, produced the following:
"""
title='Pride and Prejudice' 
author='Jane Austen' 
publication_year=1813 
genre='Romantic novel' 
characters=['Elizabeth Bennet', 'Mr. Darcy', 'Jane Bennet', 'Mr. Bingley', 'Lydia Bennet', 'Mr. Wickham'] 
summary='Pride and Prejudice is a classic novel by Jane Austen, published in 1813. It follows the story of Elizabeth Bennet as she navigates issues of manners, morality, education, and marriage in early 19th-century England. The story revolves primarily around Elizabeth and her relationship with the haughty yet enigmatic Mr. Darcy.'
"""
