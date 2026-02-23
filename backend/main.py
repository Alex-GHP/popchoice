from langgraph.types import Command

from app.agent import recommender
from app.database import add_media

INITIAL_STATE = {
    "mood": None,
    "media_type": None,
    "genres": [],
    "nostalgic_title": None,
    "search_results": [],
    "recommendation": None,
    "asked_nostalgic": False,
}

SEED_DATA = [
    {
        "title": "Severance",
        "type": "series",
        "genres": ["thriller", "sci-fi", "drama"],
        "description": "Office workers discover their work memories are surgically divided from personal life.",
        "user_rating": 9,
        "gf_rating": 8,
        "user_review": "Loved the slow burn tension and dystopian corporate horror. Visually stunning.",
        "gf_review": "Really liked the mystery and characters, felt slow at first but totally hooked by episode 3.",
    },
    {
        "title": "The Bear",
        "type": "series",
        "genres": ["drama"],
        "description": "A young chef returns to Chicago to run his family's chaotic sandwich shop after a tragedy.",
        "user_rating": 8,
        "gf_rating": 9,
        "user_review": "Intense and stressful in the best way. The kitchen scenes feel incredibly real.",
        "gf_review": "Loved the emotional depth and the characters. Cried multiple times.",
    },
    {
        "title": "Everything Everywhere All at Once",
        "type": "movie",
        "genres": ["sci-fi", "comedy", "drama"],
        "description": "A middle-aged Chinese-American woman discovers she must connect with parallel universe versions of herself to save the world.",
        "user_rating": 10,
        "gf_rating": 10,
        "user_review": "Best movie I've seen in years. Absurd and profound at the same time.",
        "gf_review": "Made me cry and laugh in the same minute. Absolutely loved it.",
    },
    {
        "title": "Parasite",
        "type": "movie",
        "genres": ["thriller", "drama", "dark comedy"],
        "description": "A poor Korean family schemes to become employed by a wealthy family, with increasingly dark consequences.",
        "user_rating": 10,
        "gf_rating": 9,
        "user_review": "Masterpiece. The tension builds perfectly and the twist completely floored me.",
        "gf_review": "Loved it but it was hard to watch at times. The ending stayed with me for days.",
    },
    {
        "title": "Fleabag",
        "type": "series",
        "genres": ["comedy", "drama"],
        "description": "A dry-witted woman navigates modern London life while dealing with grief and a deeply dysfunctional family.",
        "user_rating": 8,
        "gf_rating": 10,
        "user_review": "Incredibly witty writing, the fourth-wall breaks are genius. Short and perfect.",
        "gf_review": "My favorite show ever. Funny, heartbreaking, and so real.",
    },
    {
        "title": "Arrival",
        "type": "movie",
        "genres": ["sci-fi", "drama"],
        "description": "A linguist is recruited to communicate with alien spacecraft that have appeared around the world.",
        "user_rating": 9,
        "gf_rating": 7,
        "user_review": "Genuinely mind-bending. The twist recontextualizes everything in the best way.",
        "gf_review": "Beautiful but felt slow. The ending hit me harder on reflection than while watching.",
    },
    {
        "title": "The Lighthouse",
        "type": "movie",
        "genres": ["horror", "drama", "psychological"],
        "description": "Two lighthouse keepers try to maintain their sanity while living on a remote island in the 1890s.",
        "user_rating": 8,
        "gf_rating": 5,
        "user_review": "Hypnotic and deeply unsettling. The black and white photography is incredible.",
        "gf_review": "Too slow and weird for me. I appreciated the craft but didn't enjoy watching it.",
    },
    {
        "title": "When Harry Met Sally",
        "type": "movie",
        "genres": ["romance", "comedy"],
        "description": "Two friends debate whether men and women can ever truly be just friends over the course of many years.",
        "user_rating": 7,
        "gf_rating": 9,
        "user_review": "Classic and charming. Great dialogue, fun to watch together.",
        "gf_review": "Perfect comfort movie. Funny and romantic without being cheesy.",
    },
    {
        "title": "Succession",
        "type": "series",
        "genres": ["drama", "dark comedy"],
        "description": "The Roy family fights over control of their global media empire as their aging father's health declines.",
        "user_rating": 10,
        "gf_rating": 9,
        "user_review": "Writing is untouchable. Every character is awful and I love all of them.",
        "gf_review": "Stressful but brilliant. Tom and Greg are iconic.",
    },
    {
        "title": "Midsommar",
        "type": "movie",
        "genres": ["horror", "drama"],
        "description": "A couple travel to Sweden for a midsummer festival that turns increasingly disturbing.",
        "user_rating": 7,
        "gf_rating": 4,
        "user_review": "Beautifully shot and genuinely disturbing. Slow burn done right.",
        "gf_review": "Too disturbing and upsetting. Wouldn't watch again.",
    },
]


def seed():
    print("Seeding database...")
    for entry in SEED_DATA:
        saved = add_media(entry)
        print(f"  ✓ {saved['title']}")
    print("Done.\n")


def run_agent():
    config = {"configurable": {"thread_id": "test-1"}}
    result = recommender.invoke(INITIAL_STATE, config)

    while "__interrupt__" in result:
        question = result["__interrupt__"][0].value
        print(f"\nAgent: {question}")
        answer = input("You: ").strip()
        result = recommender.invoke(Command(resume=answer), config)

    print(f"\nRecommendation:\n{result['recommendation']}")


if __name__ == "__main__":
    # seed()
    run_agent()
