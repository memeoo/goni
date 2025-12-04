import sys
import os
import logging
import threading
import time
from dotenv import load_dotenv

# Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'back'))

from back.app.services.recommendation_service import RecommendationService
from back.app.database import SessionLocal

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load env
load_dotenv('analyze/.env')

def job_function():
    logger.info("Starting job in thread")
    
    app_key = os.getenv('KIWOOM_APP_KEY')
    secret_key = os.getenv('KIWOOM_SECRET_KEY')
    account_no = os.getenv('KIWOOM_ACCOUNT_NO')
    
    if not app_key:
        logger.error("No env vars")
        return

    db = SessionLocal()
    try:
        service = RecommendationService(app_key, secret_key, account_no)
        logger.info("Service created, starting search...")
        
        # Try to search for condition 7 (same as scheduler)
        success = service.search_and_update_rec_stocks(
            condition_id='7',
            algorithm_id=1,
            db=db,
            stock_exchange_type='K'
        )
        
        if success:
            logger.info("Job success")
        else:
            logger.error("Job failed")
            
    except Exception as e:
        logger.error(f"Job exception: {e}", exc_info=True)
    finally:
        db.close()

def main():
    logger.info("Main thread starting")
    
    # Run in a separate thread like BackgroundScheduler
    t = threading.Thread(target=job_function)
    t.start()
    t.join()
    
    logger.info("Main thread finished")

if __name__ == "__main__":
    main()
