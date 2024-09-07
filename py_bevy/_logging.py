from logging import getLogger, basicConfig, DEBUG, INFO, WARNING, ERROR, CRITICAL, Formatter, StreamHandler


class CustomFormatter(Formatter):

    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = f"[%(levelname)s | %(asctime)s | %(name)s | (%(filename)s:%(lineno)d)]\
{reset} :  %(message)s"

    FORMATS = {
        DEBUG: f"{blue}{format}",
        INFO: f"{green}{format}",
        WARNING: f"{yellow}{format}",
        ERROR: f"{red}{format}",
        CRITICAL: f"{bold_red}{format}",
    }

    def format(self, record):
        # print("format")
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = Formatter(log_fmt)
        return formatter.format(record)


def get_logger(log_level):

    logger = getLogger("PyBevy")
    # basicConfig(level=log_level)

    # return logger
    ch = StreamHandler()
    # ch.setLevel(log_level)
    logger.setLevel(log_level)

    ch.setFormatter(CustomFormatter())

    logger.addHandler(ch)

    # logger.error("Fuck!")

    return logger
