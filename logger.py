import logging
import sys

def setup_logger():
    logger = logging.getLogger('death_bot')
    logger.setLevel(logging.INFO)
    
    # Konsol ve dosya için handler'lar
    ch = logging.StreamHandler(sys.stdout)
    fh = logging.FileHandler('app.log', encoding='utf-8')
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger

logger = setup_logger()
