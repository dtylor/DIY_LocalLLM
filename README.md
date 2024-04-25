# DIY_LocalLLM

Taken largely from this [example](https://github.com/jiggy-ai/pydantic-chatcompletion/blob/master/example/book_info.py), the script app_pidantic.py demonstrates the method shown in [pydantic-chatcompletion](https://github.com/jiggy-ai/pydantic-chatcompletion/tree/master), but points to a private Phi-2 LLM, running locally on [jan.ai](https://jan.ai/) server. The results were successfull after a couple attempts.  The LLM returned a summary of the user supplied unstructured text, according to the proper json schema, as dictated by the user supplied pidantic class.  The initial attempts yielded error messages, which the code adds to the LLM chat context.  Given the additional error message hint, the LLM then successfully output according to the stipulated schema.  The example and schema were taken from the pydantic-chatcompletion project.


