import openai
import re
from transformers import GPT2Tokenizer
import time

def analyze_sentiment(text, key):
    openai.api_key = key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            #{"role": "user", "content": f"Analyze the sentiment of the following text and provide a sentiment score between -1 and 1, where -1 denotes extremely negative sentiment, 0 denotes neutral sentiment, and 1 denotes extremely positive sentiment. Format your response as 'Sentiment analysis: (your sentiment analysis here)', and a new line , and then 'Sentiment score: (your sentiment score here)'. Do not use newlines for the output of analysis and analysis score.\n\n{text}"}
            {"role": "user", "content": f"Analyze the sentiment of the following text and provide a sentiment score between -1 and 1, where -1 denotes extremely negative sentiment, 0 denotes neutral sentiment, and 1 denotes extremely positive sentiment. Start your response with 'Sentiment analysis:' and then 'Sentiment score:' on a new line.The analysis should not contain any new line. \n\n{text}"},
        ],
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.1,
    )
    time.sleep(25)

    response_text = response['choices'][0]['message']['content'].strip()
    response_lines = response_text.split('\n')

    sentiment_analysis = None
    sentiment_score = None

    #print(response_text)

    for line in response_lines:
        if line.startswith('Sentiment analysis:'):
            sentiment_analysis = line.replace('Sentiment analysis:', '').strip()
        elif line.startswith('Sentiment score:'):
            sentiment_score_text = line.replace('Sentiment score:', '').strip()
            ss = re.findall(r"[-+]?\d*\.\d+|\d+", sentiment_score_text)
            if ss:
                sentiment_score = float(ss[0])

        if sentiment_analysis is not None and sentiment_score is not None:
            break

    if sentiment_analysis is None or sentiment_score is None:
        #raise ValueError("Failed to extract the sentiment analysis or sentiment score from the response.")
        return None, None

    return sentiment_analysis, sentiment_score

def split_text(text, tokenizer, max_tokens=3000):
    tokens = tokenizer.encode(text)

    chunks = []
    current_chunk = []

    for token in tokens:
        if len(current_chunk) + 1 > max_tokens:
            chunks.append(tokenizer.decode(current_chunk))
            current_chunk = []

        current_chunk.append(token)

    if current_chunk:
        chunks.append(tokenizer.decode(current_chunk))

    return chunks

def summarize_chunk(chunk, model, max_tokens):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Please provide a summary of the following text:\n\n{chunk}"},
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        n=1,
        max_tokens=max_tokens,
        stop=None,
        temperature=0.7,
    )
    time.sleep(25)
    return response['choices'][0]['message']['content'].strip()

def summarize_large_text(text, key, model="gpt-3.5-turbo"):
    openai.api_key = key

    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    total_tokens = len(tokenizer.encode(text))

    if total_tokens <= 3000:
        return text

    text_chunks = split_text(text, tokenizer)

    summarized_chunks = [summarize_chunk(chunk, model, 1000) for chunk in text_chunks]

    combined_summary = " ".join(summarized_chunks)

    # If the combined summary is too long, summarize it again
    if len(tokenizer.encode(combined_summary)) > 3000:
        combined_summary = summarize_chunk(combined_summary, model, 3000)

    return combined_summary

def openai_splitter(text, key):
    openai.api_key = key
    messages = [
        {"role": "system", "content": "You are a helpful assistant that splits text into a list of items."},
        {"role": "user", "content": f"Please split the following text into a list of items, and remove any numbers or punctuation before each item (e.g., '- item' should become 'item'), the output should not have any your Note:\n\n {text}"}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.1,
    )
    time.sleep(25)

    # Extract the list items from the response
    assistant_message = response.choices[0].message['content'].strip()
    cleaned_items = assistant_message.replace("\n", "").split("- ")
    cleaned_items = list(filter(None, cleaned_items))

    return cleaned_items

def extract_nonce_keywords(text, key, n=5):
    openai.api_key = key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            #{"role": "user", "content": f"Please extract the top {n} most important nonce keywords from the following text:\n\n{text}"},
            #{"role": "user", "content": f"Please extract the top {n} most important nonce keywords relevant to business or investing, such as company names, stock symbols, market trends, and economic factors from the following text:\n\n{text}"},
            {"role": "user", "content": f"Please extract the top {n} most important nonce keywords relevant to money or investing or cryptocurrency or company or stocks from the following text. The keywords should not completely equal to money, investing, cryptocurrency, company, stocks:\n\n{text}"},
        ],
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.1,
    )
    time.sleep(25)

    extracted_keywords = response['choices'][0]['message']['content'].strip()
    keywords = openai_splitter(extracted_keywords, key)
    keywords = [re.sub(r'\s*\([^)]*\)', '', keyword) for keyword in keywords]
    keywords= ['"{}"'.format(item).strip() if not item.startswith('"') and not item.endswith('"') else item for item in keywords]

    return keywords
