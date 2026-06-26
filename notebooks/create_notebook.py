import os
import json

def create_demo_notebook():
    os.makedirs("notebooks", exist_ok=True)
    
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# IKS-Aware Explainable Neural Machine Translation for Classical Tamil\n",
                    "This notebook demonstrates the complete pipeline of our **IKS-Aware Explainable Neural Machine Translation (NMT)** system. It covers data exploration, concept detection, FAISS-based semantic retrieval, multilingual meaning ranking, input tag-augmentation, translation, and explainability reporting."
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Setup and Imports\n",
                    "We start by importing our pipeline modules and loading configurations."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import os\n",
                    "import sys\n",
                    "import pandas as pd\n",
                    "import yaml\n",
                    "import json\n",
                    "\n",
                    "# Append parent directory to path so we can import modules from scripts/\n",
                    "sys.path.append(os.path.abspath('../scripts'))\n",
                    "sys.path.append(os.path.abspath('scripts'))\n",
                    "\n",
                    "from detector import IKSConceptDetector\n",
                    "from retriever import IKSMeaningRetriever\n",
                    "from ranker import IKSMeaningRanker\n",
                    "from augment import IKSInputAugmenter\n",
                    "from explain import IKSExplainer\n",
                    "print(\"Modules imported successfully!\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. Explore the Curated Datasets\n",
                    "Let's load the compiled IKS Knowledge Base (200 concepts) and the parallel sentence dataset."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Load Knowledge Base\n",
                    "kb_df = pd.read_csv('../knowledge_base/iks_kb.csv' if os.path.exists('../knowledge_base/iks_kb.csv') else 'knowledge_base/iks_kb.csv')\n",
                    "print(f\"Knowledge Base Shape: {kb_df.shape}\")\n",
                    "kb_df.head(10)"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Load Parallel Sentence Dataset\n",
                    "dataset_df = pd.read_csv('../datasets/classical_tamil_parallel.csv' if os.path.exists('../datasets/classical_tamil_parallel.csv') else 'datasets/classical_tamil_parallel.csv')\n",
                    "print(f\"Parallel Dataset Shape: {dataset_df.shape}\")\n",
                    "dataset_df.head(10)"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. Concept Resolution & Augmentation Pipeline\n",
                    "We initialize our augmenter which handles the joint workflow: concept detection -> semantic candidate retrieval -> contextual meaning ranking -> context tag prepending."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Initialize the augmenter (this builds/loads the FAISS semantic index of the KB)\n",
                    "config_path = '../configs/config.yaml' if os.path.exists('../configs/config.yaml') else 'configs/config.yaml'\n",
                    "augmenter = IKSInputAugmenter(config_path)\n",
                    "print(\"Augmenter pipeline initialized and FAISS index loaded.\")"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Run augmentation on a sample classical sentence\n",
                    "sample_sentence = \"அறத்தாறின் இல்வாழ்க்கை ஆற்றின் புறத்தாறின் போஒய்ப் பெறுவது எவன்.\"\n",
                    "aug_result = augmenter.augment_sentence(sample_sentence)\n",
                    "\n",
                    "print(f\"Original Sentence:  {aug_result['original']}\")\n",
                    "print(f\"Augmented Sentence: {aug_result['augmented']}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 4. Translation and Explainable Output Generation\n",
                    "Let's pass the augmented sentence to the explainer and simulate the full translation and reasoning report."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "explainer = IKSExplainer()\n",
                    "translation_output = \"If a person leads a domestic life in the path of virtue, what more is to be gained by entering other paths?\"\n",
                    "\n",
                    "report = explainer.generate_explanation(\n",
                    "    original_text=aug_result[\"original\"],\n",
                    "    translation=translation_output,\n",
                    "    augmentation_details=aug_result[\"details\"]\n",
                    ")\n",
                    "print(report)"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11.9"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    
    with open("notebooks/iks_nmt_demo.ipynb", "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=4, ensure_ascii=False)
    print("Saved notebooks/iks_nmt_demo.ipynb successfully.")

if __name__ == "__main__":
    create_demo_notebook()
