"""
train_tag_scorer.py — Fine-tune CAMeL-BERT as a token-level UPOS tag scorer on PADT.

Trains BERTForTokenClassification over the UPOS labels found in the training
CoNLL (16 labels for PADT). The result is:
  * an honest neural baseline on the same UPOS scheme as the Jawhar evaluation,
    and
  * the scorer used by the candidate-constrained hybrid in run_evaluation.py.

Usage
-----
    python eval/train_tag_scorer.py \
        --train eval/data/ar_padt_train.conll \
        --dev   eval/data/ar_padt_dev.conll \
        --model CAMeL-Lab/bert-base-arabic-camelbert-msa \
        --epochs 5 --lr 2e-5 --batch-size 24 --max-len 180 \
        --output-dir ./checkpoints/tag-scorer

Best checkpoint (by dev token accuracy) is saved to <output-dir>.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer,
    BertForTokenClassification,
    get_linear_schedule_with_warmup,
)

from eval.metrics import load_conll


def build_label_vocab(sentences) -> dict[str, int]:
    """Map UPOS tags in the gold data to integer ids (frequency-ordered)."""
    freq: dict[str, int] = {}
    for sent in sentences:
        for _, tag in sent:
            if not tag:
                continue
            freq[tag] = freq.get(tag, 0) + 1
    labels = sorted(freq, key=lambda t: (-freq[t], t))
    return {t: i for i, t in enumerate(labels)}


class TagDataset(Dataset):
    def __init__(self, sentences, tokenizer, label2id, max_len):
        self.encodings = []
        self.n_tokens = 0
        for sent in sentences:
            tokens = [tok for tok, _ in sent]
            tags = [tag for _, tag in sent]
            enc = tokenizer(tokens, is_split_into_words=True, truncation=True,
                            max_length=max_len)
            word_ids = enc.word_ids()
            labels = []
            prev = None
            for wid in word_ids:
                if wid is None or wid == prev:
                    labels.append(-100)
                else:
                    labels.append(label2id.get(tags[wid], -100))
                    prev = wid
            enc["labels"] = labels
            self.encodings.append(enc)
            self.n_tokens += len(tokens)

    def __len__(self):
        return len(self.encodings)

    def __getitem__(self, i):
        e = self.encodings[i]
        return {
            "input_ids": torch.tensor(e["input_ids"], dtype=torch.long),
            "attention_mask": torch.tensor(e["attention_mask"], dtype=torch.long),
            "labels": torch.tensor(e["labels"], dtype=torch.long),
        }


def collate_fn(batch, pad_id):
    max_len = max(len(b["input_ids"]) for b in batch)
    input_ids = torch.full((len(batch), max_len), pad_id, dtype=torch.long)
    attention = torch.zeros((len(batch), max_len), dtype=torch.long)
    labels = torch.full((len(batch), max_len), -100, dtype=torch.long)
    for i, b in enumerate(batch):
        n = len(b["input_ids"])
        input_ids[i, :n] = b["input_ids"]
        attention[i, :n] = b["attention_mask"]
        labels[i, :n] = b["labels"]
    return {"input_ids": input_ids, "attention_mask": attention, "labels": labels}


def token_accuracy_from_logits(logits, labels):
    preds = logits.argmax(-1)
    mask = labels != -100
    correct = (preds[mask] == labels[mask]).sum().item()
    total = mask.sum().item()
    return (correct / total) if total else 0.0


def evaluate(model, loader, device, use_amp):
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.amp.autocast("cuda", enabled=use_amp):
                logits = model(input_ids=batch["input_ids"],
                               attention_mask=batch["attention_mask"]).logits
            mask = batch["labels"] != -100
            preds = logits.argmax(-1)
            correct += (preds[mask] == batch["labels"][mask]).sum().item()
            total += mask.sum().item()
    return (correct / total) if total else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--dev", required=True)
    ap.add_argument("--model", default="CAMeL-Lab/bert-base-arabic-camelbert-msa")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch-size", type=int, default=24)
    ap.add_argument("--max-len", type=int, default=180)
    ap.add_argument("--patience", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output-dir", default="./checkpoints/tag-scorer")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = torch.cuda.is_available()

    gold_train = load_conll(args.train)
    gold_dev = load_conll(args.dev)
    print(f"train: {sum(len(s) for s in gold_train)} tokens / {len(gold_train)} sentences")
    print(f"dev  : {sum(len(s) for s in gold_dev)} tokens / {len(gold_dev)} sentences")

    label2id = build_label_vocab(gold_train)
    id2label = {i: t for t, i in label2id.items()}
    print(f"labels ({len(label2id)}): {', '.join(id2label[i] for i in range(len(id2label)))}")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = BertForTokenClassification.from_pretrained(
        args.model, num_labels=len(label2id), id2label=id2label, label2id=label2id
    ).to(device)

    train_ds = TagDataset(gold_train, tokenizer, label2id, args.max_len)
    dev_ds = TagDataset(gold_dev, tokenizer, label2id, args.max_len)
    pad_id = tokenizer.pad_token_id
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              collate_fn=lambda b: collate_fn(b, pad_id))
    dev_loader = DataLoader(dev_ds, batch_size=32,
                            collate_fn=lambda b: collate_fn(b, pad_id))
    print(f"train batches: {len(train_loader)} ({train_ds.n_tokens} tokens)")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.999))
    total_steps = math.ceil(len(train_loader) * args.epochs)
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    os.makedirs(args.output_dir, exist_ok=True)
    best_acc, patience_counter = 0.0, 0

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad()
            with torch.amp.autocast("cuda", enabled=use_amp):
                out = model(input_ids=batch["input_ids"],
                            attention_mask=batch["attention_mask"],
                            labels=batch["labels"])
            loss = out.loss
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            total_loss += loss.item()

        dev_acc = evaluate(model, dev_loader, device, use_amp)
        print(f"epoch {epoch}: train_loss={total_loss / len(train_loader):.4f}  "
              f"dev_acc={dev_acc:.4f}")

        if dev_acc > best_acc:
            best_acc = dev_acc
            patience_counter = 0
            model.save_pretrained(args.output_dir)
            tokenizer.save_pretrained(args.output_dir)
            with open(os.path.join(args.output_dir, "label_vocab.json"), "w", encoding="utf-8") as f:
                json.dump({"id2label": {str(k): v for k, v in id2label.items()},
                           "label2id": label2id}, f, ensure_ascii=False, indent=1)
            print(f"  saved best model (dev_acc={best_acc:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"early stopping at epoch {epoch} (patience={args.patience})")
                break

    print(f"\nBest dev accuracy: {best_acc:.4f}. Best checkpoint in {args.output_dir}")


if __name__ == "__main__":
    main()
