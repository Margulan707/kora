import logging

def log_init():
    logging.basicConfig( 
        filename="main.log",
        filemode='w',
        level=logging.DEBUG,
        format= '%(asctime)s - %(levelname)s - %(message)s',
)

def log_exception(e, f_name):
    logging.error("Function {} raised {}".format(f_name,e))

def log_database_changes(msg):
    logging.info(msg)

def log_database_connections(f_name):
    logging.info("Database connection closed in {}".format(f_name))
