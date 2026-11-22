from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

sentences = [
    "AI software that screens job applicants' CVs",
    "AI systems intended to be used for the recruitment or selection of natural persons, in particular to analyse and filter job applications",
    "A face recognition camera in a shopping mall",
    "Remote biometric identification systems",
    "A chatbot that recommends pizza toppings",
]

embeddings = model.encode(sentences, normalize_embeddings=True)

print("Shape:", embeddings.shape)
print("First 5 numbers of sentence 1:", embeddings[0][:5])
print()

for i in range(len(sentences)):
    for j in range(i + 1, len(sentences)):
        score = np.dot(embeddings[i], embeddings[j])
        print(f"{score:.2f}  |  {sentences[i][:40]}  <->  {sentences[j][:40]}")
