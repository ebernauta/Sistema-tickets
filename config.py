class Config:
    SECRET_KEY = '7110c8ae51a4b5af97be6534caef90e4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe'


class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = 'munidalcahue.cl'
    MYSQL_USER = 'munidalc_ticket'
    MYSQL_PASSWORD = 'MDTicket-2023'
    MYSQL_DB = 'munidalc_Tickets2'


config = {
    'development': DevelopmentConfig
}
