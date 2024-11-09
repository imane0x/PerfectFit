from src.query_engine import get_query_engine

def get_response(msg):
    query_engine = get_query_engine()
    response = query_engine.query(msg)
    print(response.metadata["text_nodes"][0].score)
    get_image = False
    if response.metadata["text_nodes"][0].score>=0.55:
        response.metadata["text_nodes"][0].metadata["file_path"]
        get_image = True
        
    return response,get_image

if __name__ == "__main__":
    print("Let's chat! (type 'quit' to exit)")
    while True:
        sentence = input("You: ")
        resp = get_response(sentence)
    