import os
import json
import torch
import argparse
import numpy as np
from tqdm import tqdm
from sklearn.neighbors import NearestNeighbors
from InstructorEmbedding import INSTRUCTOR
from evaluate_judge import build_dataset


def build_trainset(data_type, data_path):
    trainset = []
    if data_type == "pandalm":
        with open(os.path.join(data_path, "pandalm/train.json"), "r") as fin:
            lines = json.load(fin)

        for line in lines:
            parts = line["input_sequence"].split("###")

            example = {
                "question_body": "",
                "answer1_body": "",
                "answer2_body": "",
                "review": ""
            }

            example["review"] = line["output_sequence"]
            for part in parts:
                section = part.strip()
                if section.startswith("Instruction:"):
                    # Skip the "Instruction:" part and get the rest
                    example["question_body"] = section[len(
                        "Instruction:"):].strip()
                elif section.startswith("Response 1:"):
                    # Skip the "Response 1:" part and get the rest
                    example["answer1_body"] = section[len(
                        "Response 1:"):].strip()
                elif section.startswith("Response 2:"):
                    # Skip the "Response 2:" part and get the rest
                    example["answer2_body"] = section[len(
                        "Response 2:"):].strip()

            trainset.append(example)

    return trainset


def concat_sentence(example, data_type):
    question_body = str(example["question_body"])

    if "prometheus" in data_type:
        answer_body = str(example["answer_body"])
        sentence = question_body + answer_body

    else:
        answer1_body = str(example["answer1_body"])
        answer2_body = str(example["answer2_body"])
        sentence = question_body + \
            answer1_body + answer2_body

    return sentence


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bs", type=int, default=512)
    parser.add_argument(
        "--data-type",
        type=str,
        choices=("judgelm", "pandalm", "auto-j",
                 "prometheus-ind", "prometheus-ood"),
        default=None,
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="./data",
    )

    args = parser.parse_args()

    model = INSTRUCTOR('models/instructor-xl')

    PROMPT = "Represent the sentence: "

    if torch.cuda.is_available():
        model = model.cuda()

    trainset = build_trainset(args.data_type, args.data_path)
    testset = build_dataset(args.data_type, args.data_path)

    results = []

    for start_index in tqdm(range(0, len(trainset), args.bs)):
        sentences = [concat_sentence(trainset[i], args.data_type) for i in range(
            start_index, min(start_index + args.bs, len(trainset)))]
        sentences = [[PROMPT, sentence] for sentence in sentences]
        embeddings = list(model.encode(sentences))
        results += embeddings

    train_embeddings = np.array(results)

    results_test = []

    for start_index in tqdm(range(0, len(testset), args.bs)):
        sentences = [concat_sentence(testset[i], args.data_type) for i in range(
            start_index, min(start_index + args.bs, len(testset)))]
        sentences = [[PROMPT, sentence] for sentence in sentences]
        embeddings = list(model.encode(sentences))
        results_test += embeddings

    test_embeddings = np.array(results_test)

    neigh = NearestNeighbors(n_neighbors=1, metric="cosine")
    neigh.fit(train_embeddings)

    distances, indices = neigh.kneighbors(test_embeddings)

    nearest_neighbors_data = []

    for i, idx in enumerate(indices):
        nearest_neighbor_example = trainset[idx[0]]
        nearest_neighbors_data.append(nearest_neighbor_example)

    with open(os.path.join(args.data_path, args.data_type, "nearest_neighbors_data.json"), "w") as outfile:
        json.dump(nearest_neighbors_data, outfile,
                  ensure_ascii=False, indent=4)