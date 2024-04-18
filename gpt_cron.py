from datetime import datetime

from loguru import logger

from app import app
from crud import crud
from gpt import gpt_gen

if __name__ == "__main__":
    logger = logger.bind(name="gpt")

    NOW = datetime.now()
    WEEKDAY, H, M = NOW.weekday() + 1, NOW.hour, NOW.minute

    with app.app_context():
        events = crud.get_event_all(WEEKDAY, H, M)
        # events = [{'user_id': int, 'prompt_id': int}, {}...]
        for event in events:
            logger.info(
                f"=======CRON=======\nWeekDay H:M >> {WEEKDAY} {H}:{M:02} EVENT >> {event}"
            )
            gpt_gen(event.get("user_id"), event.get("prompt_id"))
