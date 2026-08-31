import json
from pathlib import Path

# Location of scores.json
SCORES_FILE = Path(__file__).parent / "scores.json"

def load_scores():
    """
    Load leaderboard scores from scores.json

    If the file does not exist or cannot be read,
    return an empty leaderboard.
    """

    if not SCORES_FILE.exists():
        return []

    try:
        with open(SCORES_FILE, "r") as file:
            scores = json.load(file)

        return scores

    except (json.JSONDecodeError, OSError):
        return []

def save_scores(scores):
    """
    Save the leaderboard list into scores.json
    """

    with open(SCORES_FILE, "w") as file:
        json.dump(
            scores,
            file,
            indent=4,
        )

def add_score(name, score):
    """
    Add one new score, sort the leaderboard,
    keep only the top 10, save it, and return it.
    """

    scores = load_scores()

    scores.append({
        "name": name,
        "score": score,
    })

    scores = sorted(
        scores,
        key=lambda entry: entry["score"],
        reverse=True,
    )[:10]

    save_scores(scores)

    return scores