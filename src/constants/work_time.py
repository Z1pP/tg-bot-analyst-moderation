from datetime import time, timedelta

# Начало рабочего дня (10:00)
WORK_START = time(10, 0)

# Конец рабочего дня (22:00)
WORK_END = time(22, 0)

# Допустимое отклонение от рабочего времени
TOLERANCE = timedelta(minutes=10)
